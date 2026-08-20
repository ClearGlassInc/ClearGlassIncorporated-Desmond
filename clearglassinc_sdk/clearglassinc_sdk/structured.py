"""Structured output: constrain an agent's final answer to a JSON schema.

Attach an `OutputSchema` to an `Agent` and the `Runner` will (a) append schema
instructions to the system prompt, (b) parse the final message as JSON, and
(c) on a parse/validation failure, feed the error back to the model for a
bounded number of repair attempts before giving up.

Validation is a dependency-free subset of JSON Schema (type, required,
properties, enum, items) — enough to keep agent outputs honest without
pulling in `jsonschema`.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

_JSON_TYPES: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
}

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


class OutputValidationError(ValueError):
    """Raised when a model's output doesn't satisfy the declared schema."""


def extract_json(text: str) -> Any:
    """Pull a JSON value out of a model response, tolerating code fences and
    surrounding prose."""
    candidate = text.strip()
    if not candidate:
        raise OutputValidationError("model returned empty output")

    fenced = _FENCE_RE.search(candidate)
    if fenced:
        candidate = fenced.group(1).strip()

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # Fall back to the first balanced {...} or [...] block in the text.
    for opener, closer in (("{", "}"), ("[", "]")):
        start = candidate.find(opener)
        end = candidate.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(candidate[start : end + 1])
            except json.JSONDecodeError:
                continue

    raise OutputValidationError("model output was not valid JSON")


def validate(value: Any, schema: dict[str, Any], path: str = "$") -> None:
    """Validate `value` against a JSON Schema subset. Raises on the first problem."""
    expected_type = schema.get("type")
    if expected_type:
        python_type = _JSON_TYPES.get(expected_type)
        if python_type is None:
            raise OutputValidationError(f"{path}: unsupported schema type '{expected_type}'")
        # bool is a subclass of int in Python; keep them distinct here.
        if expected_type in {"integer", "number"} and isinstance(value, bool):
            raise OutputValidationError(f"{path}: expected {expected_type}, got boolean")
        if not isinstance(value, python_type):
            raise OutputValidationError(
                f"{path}: expected {expected_type}, got {type(value).__name__}"
            )

    if "enum" in schema and value not in schema["enum"]:
        raise OutputValidationError(f"{path}: value {value!r} is not one of {schema['enum']}")

    if expected_type == "object" or isinstance(value, dict):
        properties: dict[str, Any] = schema.get("properties", {})
        for required_key in schema.get("required", []):
            if required_key not in value:
                raise OutputValidationError(f"{path}: missing required property '{required_key}'")
        for key, sub_schema in properties.items():
            if key in value:
                validate(value[key], sub_schema, f"{path}.{key}")

    if (expected_type == "array" or isinstance(value, list)) and "items" in schema:
        for index, item in enumerate(value):
            validate(item, schema["items"], f"{path}[{index}]")


@dataclass
class OutputSchema:
    """A named JSON schema an agent's final answer must satisfy."""

    name: str
    schema: dict[str, Any]
    description: str = ""
    max_repair_attempts: int = 2
    strict: bool = True

    def prompt_instructions(self) -> str:
        """Text appended to the system prompt so the model knows the contract."""
        described = f" {self.description}" if self.description else ""
        return (
            f"\n\nYou MUST reply with a single JSON object named '{self.name}'"
            f" and nothing else.{described}\n"
            f"It must conform to this JSON Schema:\n{json.dumps(self.schema, indent=2)}\n"
            "Do not wrap it in prose. Do not include explanatory text."
        )

    def parse(self, text: str) -> Any:
        """Parse and validate a model response. Raises `OutputValidationError`."""
        value = extract_json(text)
        if self.strict:
            validate(value, self.schema)
        return value

    def repair_prompt(self, error: str) -> str:
        """The corrective user turn sent back to the model after a bad output."""
        return (
            f"Your previous reply did not satisfy the required schema: {error}\n"
            "Reply again with ONLY the corrected JSON object."
        )


@dataclass
class StructuredResult:
    """A parsed, schema-valid agent output alongside the raw text it came from."""

    value: Any
    raw_text: str
    repair_attempts: int = 0
    errors: list[str] = field(default_factory=list)

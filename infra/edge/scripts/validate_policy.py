#!/usr/bin/env python3
"""Validate ClearGlass edge policy safety invariants without third-party packages."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "policies" / "baseline.json"
DEFAULT_SCHEMA = ROOT / "policy.schema.json"

ALLOWED_ACTIONS = {
    "allow", "log", "managed_challenge", "interactive_challenge",
    "rate_limit", "block", "set_header", "remove_header", "cache", "route",
}
ALLOWED_ROLLOUT = {"observe", "challenge", "enforce", "disabled"}
ALLOWED_LOG_LEVELS = {"none", "metadata", "security_event"}
ALLOWED_CATEGORIES = {
    "ddos", "managed_waf", "custom_waf", "bot", "ip_reputation",
    "rate_limit", "geo_asn", "headers", "cache", "origin", "logging", "emergency",
}
REQUIRED_RULE_IDS = {
    "ddos.provider-managed",
    "waf.managed-baseline",
    "waf.unexpected-method-static",
    "waf.path-traversal-probing",
    "waf.request-size-anomaly",
    "bot.verified-crawlers",
    "bot.trusted-operations",
    "bot.normal-browsers",
    "bot.suspicious-automation",
    "reputation.anonymous-network",
    "ratelimit.static-assets",
    "ratelimit.html",
    "ratelimit.login",
    "ratelimit.password-reset",
    "ratelimit.search",
    "ratelimit.contact-form",
    "ratelimit.api",
    "ratelimit.admin",
    "ratelimit.webhooks",
    "geo.default-disabled",
    "headers.security-baseline",
    "cache.static-assets",
    "cache.sensitive-bypass",
    "origin.pages-bypass-known",
    "origin.dynamic-authenticated-pull",
    "logging.privacy-baseline",
    "emergency.high-security-template",
}


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top level must be an object")
    return data


def parse_expiry(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("expiry must include a timezone")
    return parsed.astimezone(timezone.utc)


def _is_type(value: Any, expected: str) -> bool:
    return {
        "array": isinstance(value, list),
        "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "null": value is None,
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "object": isinstance(value, dict),
        "string": isinstance(value, str),
    }.get(expected, False)


def validate_schema(instance: Any, schema: dict[str, Any], root: dict[str, Any], path: str = "$") -> list[str]:
    """Validate the deterministic JSON-Schema subset used by policy.schema.json."""
    errors: list[str] = []
    if "$ref" in schema:
        reference = schema["$ref"]
        if not isinstance(reference, str) or not reference.startswith("#/"):
            return [f"{path}: unsupported schema reference {reference!r}"]
        target: Any = root
        try:
            for part in reference[2:].split("/"):
                target = target[part.replace("~1", "/").replace("~0", "~")]
        except (KeyError, TypeError):
            return [f"{path}: unresolved schema reference {reference!r}"]
        return validate_schema(instance, target, root, path)

    expected = schema.get("type")
    expected_types = expected if isinstance(expected, list) else [expected] if expected else []
    if expected_types and not any(_is_type(instance, item) for item in expected_types):
        return [f"{path}: expected type {' or '.join(expected_types)}"]
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: unsupported value {instance!r}")

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                errors.append(f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in instance.keys() - properties.keys():
                errors.append(f"{path}: unknown property {key!r}")
        for key, value in instance.items():
            child = properties.get(key)
            if isinstance(child, dict):
                errors.extend(validate_schema(value, child, root, f"{path}.{key}"))
    elif isinstance(instance, list):
        if len(instance) < int(schema.get("minItems", 0)):
            errors.append(f"{path}: fewer than minItems")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, value in enumerate(instance):
                errors.extend(validate_schema(value, item_schema, root, f"{path}[{index}]"))
    elif isinstance(instance, str):
        if len(instance) < int(schema.get("minLength", 0)):
            errors.append(f"{path}: shorter than minLength")
        pattern = schema.get("pattern")
        if pattern and re.search(pattern, instance) is None:
            errors.append(f"{path}: does not match required pattern")
        if schema.get("format") == "date-time":
            try:
                parse_expiry(instance)
            except ValueError as exc:
                errors.append(f"{path}: invalid date-time: {exc}")
    elif isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: below minimum")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: above maximum")
    return errors


def validate(policy: dict[str, Any], schema: dict[str, Any] | None = None) -> list[str]:
    if schema is None:
        schema = load_json(DEFAULT_SCHEMA)
    errors: list[str] = validate_schema(policy, schema, schema)
    required_top = {"version", "environment", "defaults", "rules"}
    missing = required_top - policy.keys()
    if missing:
        errors.append(f"missing top-level keys: {sorted(missing)}")
        return errors

    defaults = policy.get("defaults")
    if not isinstance(defaults, dict):
        errors.append("defaults must be an object")
        defaults = {}

    if defaults.get("geo_enforcement_enabled") is not False:
        errors.append("safe default violated: geo_enforcement_enabled must be false")
    if defaults.get("csp_mode") != "report-only":
        errors.append("safe default violated: baseline CSP must start report-only")
    if defaults.get("log_sensitive_fields") is not False:
        errors.append("privacy invariant violated: log_sensitive_fields must be false")
    if defaults.get("verified_crawlers_challenged") is not False:
        errors.append("safe default violated: verified_crawlers_challenged must be false")
    if defaults.get("broad_automation_block_enabled") is not False:
        errors.append("safe default violated: broad_automation_block_enabled must be false")
    if defaults.get("provider_changes_applied") is not False:
        errors.append("truth invariant violated: repository policy must not claim provider changes were applied")

    rules = policy.get("rules")
    if not isinstance(rules, list) or not rules:
        errors.append("rules must be a non-empty array")
        return errors

    seen_ids: set[str] = set()
    seen_priorities: set[int] = set()
    now = datetime.now(timezone.utc)

    for index, rule in enumerate(rules):
        where = f"rules[{index}]"
        if not isinstance(rule, dict):
            errors.append(f"{where}: must be an object")
            continue

        required = {
            "id", "description", "category", "scope", "priority", "action",
            "rollout_mode", "log_level", "enabled", "match", "exceptions",
            "expires_at", "owner", "change_ticket", "rationale",
        }
        missing_rule = required - rule.keys()
        if missing_rule:
            errors.append(f"{where}: missing keys {sorted(missing_rule)}")
            continue

        rule_id = rule.get("id")
        if not isinstance(rule_id, str) or len(rule_id) < 3:
            errors.append(f"{where}: invalid id")
        elif rule_id in seen_ids:
            errors.append(f"{where}: duplicate id {rule_id}")
        else:
            seen_ids.add(rule_id)

        priority = rule.get("priority")
        if not isinstance(priority, int) or not 1 <= priority <= 100000:
            errors.append(f"{where}: priority must be integer 1..100000")
        elif priority in seen_priorities:
            errors.append(f"{where}: duplicate priority {priority}")
        else:
            seen_priorities.add(priority)

        action = rule.get("action")
        rollout = rule.get("rollout_mode")
        category = rule.get("category")
        log_level = rule.get("log_level")

        if action not in ALLOWED_ACTIONS:
            errors.append(f"{where}: unsupported action {action!r}")
        if rollout not in ALLOWED_ROLLOUT:
            errors.append(f"{where}: unsupported rollout_mode {rollout!r}")
        if category not in ALLOWED_CATEGORIES:
            errors.append(f"{where}: unsupported category {category!r}")
        if log_level not in ALLOWED_LOG_LEVELS:
            errors.append(f"{where}: unsupported log_level {log_level!r}")

        enabled = rule.get("enabled")
        if not isinstance(enabled, bool):
            errors.append(f"{where}: enabled must be boolean")

        exceptions = rule.get("exceptions")
        if not isinstance(exceptions, list) or not all(isinstance(x, str) for x in exceptions):
            errors.append(f"{where}: exceptions must be an array of strings")

        # Dangerous broad terminal policies require explicit rationale/exception handling.
        if enabled and rule.get("scope") == "all" and action in {"allow", "block"}:
            errors.append(f"{where}: broad enabled {action} over scope=all is prohibited")

        if enabled and action == "allow":
            scope = str(rule.get("scope", ""))
            exception_text = " ".join(str(item) for item in exceptions).lower() if isinstance(exceptions, list) else ""
            if "layer" not in scope or "managed waf" not in exception_text:
                errors.append(f"{where}: allow must be layer-scoped and explicitly retain managed WAF inspection")

        # Geo/ASN is disabled in the baseline unless the operator explicitly changes it.
        if category == "geo_asn" and enabled:
            errors.append(f"{where}: geo/ASN rule must be disabled in baseline policy")

        if category == "custom_waf" and enabled and (action != "log" or rollout != "observe"):
            errors.append(f"{where}: custom WAF baseline rules must start as log/observe")

        # Permanent reputation-only blocks are prohibited.
        if category == "ip_reputation" and action == "block" and not rule.get("expires_at"):
            errors.append(f"{where}: reputation-only block requires expiry and review")

        if category == "bot" and enabled and action == "block" and not rule.get("expires_at"):
            errors.append(f"{where}: enabled bot-only block requires expiry and corroborated review")

        # Emergency controls must be temporary.
        if category == "emergency" and enabled:
            expiry = rule.get("expires_at")
            if not expiry:
                errors.append(f"{where}: enabled emergency rule requires expires_at")
            else:
                try:
                    if parse_expiry(str(expiry)) <= now:
                        errors.append(f"{where}: emergency rule is already expired")
                except ValueError as exc:
                    errors.append(f"{where}: invalid expires_at: {exc}")

        threshold = rule.get("threshold")
        if category == "rate_limit":
            if not isinstance(threshold, dict):
                errors.append(f"{where}: rate_limit requires threshold object")
            else:
                requests = threshold.get("requests")
                period = threshold.get("period_seconds")
                if not isinstance(requests, int) or requests <= 0:
                    errors.append(f"{where}: threshold.requests must be a positive integer")
                if not isinstance(period, int) or period <= 0:
                    errors.append(f"{where}: threshold.period_seconds must be a positive integer")

        if action == "block" and rollout == "observe":
            errors.append(f"{where}: block action cannot be in observe rollout")
        if rollout == "disabled" and enabled:
            errors.append(f"{where}: disabled rollout cannot be enabled")
        if not enabled and rollout != "disabled":
            errors.append(f"{where}: disabled rule must use rollout_mode=disabled")
        if enabled and action == "block" and not rule.get("change_ticket"):
            errors.append(f"{where}: enabled block action requires a change_ticket")

        if not str(rule.get("owner", "")).strip():
            errors.append(f"{where}: owner is required")
        if len(str(rule.get("rationale", "")).strip()) < 5:
            errors.append(f"{where}: rationale is too short")

    missing_required_rules = REQUIRED_RULE_IDS - seen_ids
    if missing_required_rules:
        errors.append(f"missing required baseline rule IDs: {sorted(missing_required_rules)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()

    try:
        policy = load_json(args.policy)
        schema = load_json(args.schema)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    # Ensure the committed schema itself is parseable and clearly identifies the expected draft.
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        print("ERROR: policy schema must use JSON Schema draft 2020-12", file=sys.stderr)
        return 2

    errors = validate(policy, schema)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Policy validation failed with {len(errors)} error(s).", file=sys.stderr)
        return 1

    print(f"Policy OK: {args.policy} ({len(policy['rules'])} rules, version {policy['version']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

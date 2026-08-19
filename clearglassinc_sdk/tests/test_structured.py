import pytest

from clearglassinc_sdk.structured import (
    OutputSchema,
    OutputValidationError,
    extract_json,
    validate,
)

TRIAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "severity": {"type": "string", "enum": ["low", "high"]},
        "count": {"type": "integer"},
        "tags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["severity"],
}


def test_extract_plain_json():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_from_code_fence():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_embedded_in_prose():
    assert extract_json('Sure! Here you go: {"a": 1} — hope that helps.') == {"a": 1}


def test_extract_json_rejects_empty_output():
    with pytest.raises(OutputValidationError):
        extract_json("   ")


def test_extract_json_rejects_non_json():
    with pytest.raises(OutputValidationError):
        extract_json("no json anywhere here")


def test_validate_accepts_valid_object():
    validate({"severity": "high", "count": 3, "tags": ["a"]}, TRIAGE_SCHEMA)


def test_validate_rejects_missing_required_property():
    with pytest.raises(OutputValidationError, match="missing required property"):
        validate({"count": 1}, TRIAGE_SCHEMA)


def test_validate_rejects_wrong_type():
    with pytest.raises(OutputValidationError, match="expected integer"):
        validate({"severity": "high", "count": "three"}, TRIAGE_SCHEMA)


def test_validate_rejects_value_outside_enum():
    with pytest.raises(OutputValidationError, match="not one of"):
        validate({"severity": "catastrophic"}, TRIAGE_SCHEMA)


def test_validate_rejects_bad_array_item():
    with pytest.raises(OutputValidationError, match=r"\$\.tags\[1\]"):
        validate({"severity": "low", "tags": ["ok", 5]}, TRIAGE_SCHEMA)


def test_validate_treats_boolean_as_non_integer():
    with pytest.raises(OutputValidationError, match="got boolean"):
        validate({"severity": "low", "count": True}, TRIAGE_SCHEMA)


def test_schema_parse_roundtrip():
    schema = OutputSchema(name="triage", schema=TRIAGE_SCHEMA)
    assert schema.parse('```json\n{"severity": "low"}\n```') == {"severity": "low"}


def test_schema_parse_raises_on_violation():
    schema = OutputSchema(name="triage", schema=TRIAGE_SCHEMA)
    with pytest.raises(OutputValidationError):
        schema.parse('{"count": 2}')


def test_non_strict_schema_skips_validation():
    schema = OutputSchema(name="triage", schema=TRIAGE_SCHEMA, strict=False)
    assert schema.parse('{"anything": true}') == {"anything": True}


def test_prompt_instructions_mention_schema_and_name():
    schema = OutputSchema(name="triage", schema=TRIAGE_SCHEMA)
    instructions = schema.prompt_instructions()
    assert "triage" in instructions
    assert "severity" in instructions

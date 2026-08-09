import copy
import json
from pathlib import Path

import pytest

from scripts.minerals_pipeline import DATA_ROOT, ValidationError, load_json, run, validate_manifest, validate_minerals


def test_production_minerals_data_passes_validation() -> None:
    metrics = run()
    assert metrics.feeds_attempted == metrics.feeds_successful == 2
    assert metrics.feeds_failed == metrics.records_rejected == 0


def test_manifest_rejects_duplicate_feed_ids() -> None:
    manifest = load_json(DATA_ROOT / "manifest.json")
    manifest["feeds"].append(copy.deepcopy(manifest["feeds"][0]))
    with pytest.raises(ValidationError, match="unique"):
        validate_manifest(manifest)


def test_manifest_rejects_non_finite_numbers(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.json"
    candidate.write_text('{"value": NaN}', encoding="utf-8")
    with pytest.raises(ValidationError, match="non-finite"):
        load_json(candidate)


def test_minerals_reject_schema_drift_and_empty_data() -> None:
    with pytest.raises(ValidationError, match="non-empty"):
        validate_minerals({"records": []})
    with pytest.raises(ValidationError, match="schema drift"):
        validate_minerals({"records": [{"id": "lithium", "renamed_field": "Lithium"}]})


def test_manifest_json_uses_strict_json() -> None:
    with (DATA_ROOT / "manifest.json").open(encoding="utf-8") as handle:
        json.load(handle, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))

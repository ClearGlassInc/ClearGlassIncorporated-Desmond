import json
import math

import pytest

from scripts.minerals_pipeline import ValidationError, atomic_publish, mark_degraded, validate_snapshot


def snapshot(records=None, **metadata):
    return {"metadata": {"source":"Official source","last_updated":"2026-08-01T00:00:00Z","retrieved_at":"2026-08-09T00:00:00Z","frequency":"monthly","status":"MONTHLY","license":"Open","source_url":"https://example.gov/data", **metadata}, "records": records or []}


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_rejects_non_finite_numbers(value):
    with pytest.raises(ValidationError, match="non-finite"):
        validate_snapshot(snapshot([{"id":"x","value":value}]))


def test_accepts_empty_and_valid_current_feeds():
    assert validate_snapshot(snapshot())["records"] == []
    assert validate_snapshot(snapshot([{"id":"li-ca","country_code":"CA","production_tonnes":4,"change_pct":20}]))["records"]


@pytest.mark.parametrize("records, message", [
    ([{"id":"a","country_code":"CAN"}], "country code"),
    ([{"id":"a","production_tonnes":-1}], "negative"),
    ([{"id":"a","change_pct":101}], "percentage"),
    ([{"id":"a"},{"id":"a"}], "duplicate"),
])
def test_rejects_invalid_records(records, message):
    with pytest.raises(ValidationError, match=message):
        validate_snapshot(snapshot(records))


def test_rejects_missing_timestamp_and_unexpected_schema():
    with pytest.raises(ValidationError, match="timestamp"):
        validate_snapshot(snapshot(retrieved_at=None))
    with pytest.raises(ValidationError, match="records"):
        validate_snapshot({"metadata": snapshot()["metadata"]})


def test_failed_candidate_preserves_last_known_good(tmp_path):
    destination = tmp_path / "latest.json"
    destination.write_text(json.dumps(snapshot([{"id":"known-good","production_tonnes":1}])))
    candidate = tmp_path / "candidate.json"
    candidate.write_text("{ malformed")
    with pytest.raises(json.JSONDecodeError):
        atomic_publish(candidate, destination)
    assert json.loads(destination.read_text())["records"][0]["id"] == "known-good"


def test_degraded_state_preserves_records_and_last_success(tmp_path):
    destination = tmp_path / "latest.json"
    original = snapshot([{"id":"known-good"}])
    destination.write_text(json.dumps(original))
    mark_degraded(destination, "API timeout / rate limit")
    degraded = json.loads(destination.read_text())
    assert degraded["metadata"]["status"] == "DEGRADED"
    assert degraded["metadata"]["last_updated"] == original["metadata"]["last_updated"]
    assert degraded["records"] == original["records"]

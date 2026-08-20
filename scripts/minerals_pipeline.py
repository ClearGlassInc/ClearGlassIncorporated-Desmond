#!/usr/bin/env python3
"""Validate and publish Critical Minerals static snapshots without losing LKG data."""
from __future__ import annotations

import argparse
import json
import math
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "minerals"
ALLOWED_STATUSES = {"LIVE", "NEAR LIVE", "DELAYED", "DAILY", "WEEKLY", "MONTHLY", "STATIC REFERENCE", "DEGRADED", "STALE", "OFFLINE", "EMPTY"}
METADATA_FIELDS = {"source", "last_updated", "retrieved_at", "frequency", "status", "license", "source_url"}


class ValidationError(ValueError):
    """Raised when untrusted feed content cannot be safely published."""


def parse_timestamp(value: Any, *, nullable: bool = False) -> datetime | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value:
        raise ValidationError("timestamp must be a non-empty ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"invalid timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise ValidationError("timestamp must include a timezone")
    return parsed


def reject_non_finite(value: Any, path: str = "root") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValidationError(f"non-finite number at {path}")
    if isinstance(value, dict):
        for key, child in value.items():
            reject_non_finite(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_non_finite(child, f"{path}[{index}]")


def validate_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        raise ValidationError("snapshot must be an object")
    reject_non_finite(snapshot)
    metadata = snapshot.get("metadata")
    if not isinstance(metadata, dict) or not METADATA_FIELDS.issubset(metadata):
        raise ValidationError("metadata contract is incomplete")
    parse_timestamp(metadata["retrieved_at"])
    parse_timestamp(metadata["last_updated"], nullable=True)
    if metadata["status"] not in ALLOWED_STATUSES:
        raise ValidationError(f"unsupported status: {metadata['status']!r}")
    records = snapshot.get("records")
    if not isinstance(records, list):
        raise ValidationError("records must be an array")
    identifiers: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValidationError(f"record {index} must be an object")
        identifier = record.get("id") or record.get("material_id")
        if identifier:
            if identifier in identifiers:
                raise ValidationError(f"duplicate record identifier: {identifier}")
            identifiers.add(identifier)
        country = record.get("country_code")
        if country is not None and (not isinstance(country, str) or len(country) != 2 or not country.isalpha()):
            raise ValidationError(f"invalid ISO alpha-2 country code: {country!r}")
        for key, value in record.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                if any(token in key for token in ("production", "reserves", "volume", "capacity")) and value < 0:
                    raise ValidationError(f"negative physical quantity in record {index}: {key}")
                if ("percentage" in key or key.endswith("_pct")) and abs(value) > 100:
                    raise ValidationError(f"absurd percentage in record {index}: {key}")
    return snapshot


def atomic_publish(candidate: Path, destination: Path) -> None:
    payload = json.loads(candidate.read_text(encoding="utf-8"))
    validated = validate_snapshot(payload)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=destination.parent, delete=False) as handle:
        json.dump(validated, handle, ensure_ascii=False, separators=(",", ":"))
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(destination)


def mark_degraded(destination: Path, reason: str) -> None:
    """Preserve records and last success; update only safe operational metadata."""
    if not destination.exists():
        return
    snapshot = json.loads(destination.read_text(encoding="utf-8"))
    validate_snapshot(snapshot)
    snapshot["metadata"]["status"] = "DEGRADED"
    snapshot["degradation_reason"] = reason[:240]
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=destination.parent, delete=False) as handle:
        json.dump(snapshot, handle, ensure_ascii=False, separators=(",", ":"))
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(destination)


def validate_repository() -> dict[str, int]:
    manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    attempted = successful = failed = processed = rejected = 0
    for feed in manifest["feeds"]:
        attempted += 1
        try:
            snapshot = json.loads((DATA / feed["path"]).read_text(encoding="utf-8"))
            validate_snapshot(snapshot)
            processed += len(snapshot["records"])
            successful += 1
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            failed += 1
            rejected += 1
            print(f"REJECTED {feed['id']}: {exc}")
    return {"feeds_attempted": attempted, "feeds_successful": successful, "feeds_failed": failed, "records_processed": processed, "records_rejected": rejected}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true", help="Validate committed snapshots without mutation")
    parser.add_argument("--summary", type=Path, help="Write safe aggregate telemetry for GitHub Step Summary")
    args = parser.parse_args()
    started = time.monotonic()
    telemetry = validate_repository()
    telemetry["pipeline_duration_ms"] = round((time.monotonic() - started) * 1000)
    telemetry["last_success"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z") if not telemetry["feeds_failed"] else None
    if args.summary:
        args.summary.write_text("## Minerals data validation\n\n" + "\n".join(f"- **{key}**: {value}" for key, value in telemetry.items()) + "\n", encoding="utf-8")
    print(json.dumps(telemetry, sort_keys=True))
    return 1 if telemetry["feeds_failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

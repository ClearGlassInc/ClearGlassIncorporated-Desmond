#!/usr/bin/env python3
"""Validate public minerals feeds without replacing last-known-good data."""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "minerals"
STATUSES = {"LIVE", "NEAR LIVE", "DELAYED", "DAILY", "WEEKLY", "MONTHLY", "ANNUAL", "STATIC REFERENCE", "STALE", "DEGRADED", "OFFLINE", "UNAVAILABLE"}
CONFIDENCE = {"HIGH", "MEDIUM", "LOW", "UNKNOWN"}


class ValidationError(ValueError):
    """A candidate dataset failed deterministic publication checks."""


@dataclass
class Metrics:
    feeds_attempted: int = 0
    feeds_successful: int = 0
    feeds_failed: int = 0
    feeds_skipped: int = 0
    records_processed: int = 0
    records_rejected: int = 0
    data_changed: bool = False
    last_known_good_fallbacks: int = 0


def parse_timestamp(value: Any, field: str, *, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValidationError(f"{field} must be a UTC timestamp ending in Z")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{field} is not a valid ISO timestamp") from exc


def reject_non_finite(value: Any, path: str = "root") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValidationError(f"{path} contains a non-finite number")
    if isinstance(value, dict):
        for key, child in value.items():
            reject_non_finite(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_non_finite(child, f"{path}[{index}]")


def load_json(path: Path) -> Any:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{path.relative_to(ROOT)} is not readable JSON: {exc}") from exc
    reject_non_finite(value)
    return value


def validate_manifest(value: Any) -> int:
    if not isinstance(value, dict) or not isinstance(value.get("feeds"), list) or not value["feeds"]:
        raise ValidationError("manifest must contain at least one feed")
    parse_timestamp(value.get("generated_at"), "generated_at")
    ids: set[str] = set()
    for feed in value["feeds"]:
        required = {"id", "name", "source", "source_url", "retrieved_at", "source_updated_at", "expected_frequency", "status", "record_count", "schema_version", "confidence"}
        if not isinstance(feed, dict) or not required.issubset(feed):
            raise ValidationError("manifest feed is missing required properties")
        if feed["id"] in ids or not isinstance(feed["id"], str):
            raise ValidationError("manifest feed ids must be unique strings")
        ids.add(feed["id"])
        if feed["status"] not in STATUSES or feed["confidence"] not in CONFIDENCE:
            raise ValidationError(f"feed {feed['id']} has an invalid status or confidence")
        if not isinstance(feed["record_count"], int) or isinstance(feed["record_count"], bool) or feed["record_count"] < 0:
            raise ValidationError(f"feed {feed['id']} has an invalid record_count")
        parse_timestamp(feed["retrieved_at"], f"{feed['id']}.retrieved_at", nullable=True)
        parse_timestamp(feed["source_updated_at"], f"{feed['id']}.source_updated_at", nullable=True)
    return len(value["feeds"])


def validate_minerals(value: Any) -> int:
    records = value.get("records") if isinstance(value, dict) else None
    if not isinstance(records, list) or not records:
        raise ValidationError("mineral reference must contain non-empty records")
    ids: set[str] = set()
    for record in records:
        if not isinstance(record, dict) or set(record) != {"id", "name", "symbol", "category", "uses"}:
            raise ValidationError("mineral record schema drift detected")
        if record["id"] in ids or not isinstance(record["id"], str) or not record["id"]:
            raise ValidationError("mineral ids must be unique non-empty strings")
        ids.add(record["id"])
        if not all(isinstance(record[key], str) and record[key] for key in ("name", "symbol", "category")):
            raise ValidationError(f"mineral {record['id']} has invalid text fields")
        if not isinstance(record["uses"], list) or not record["uses"] or not all(isinstance(item, str) and item for item in record["uses"]):
            raise ValidationError(f"mineral {record['id']} has invalid uses")
    return len(records)


def run() -> Metrics:
    metrics = Metrics(feeds_attempted=2)
    checks = ((DATA_ROOT / "manifest.json", validate_manifest), (DATA_ROOT / "metadata" / "minerals.json", validate_minerals))
    for path, validator in checks:
        try:
            metrics.records_processed += validator(load_json(path))
            metrics.feeds_successful += 1
        except ValidationError:
            metrics.feeds_failed += 1
            metrics.records_rejected += 1
            metrics.last_known_good_fallbacks += 1
            raise
    return metrics


def write_summary(metrics: Metrics, path: Path) -> None:
    values = asdict(metrics)
    lines = ["# CLEARGLASS MINERALS DATA PIPELINE", ""] + [f"- {key.replace('_', ' ').title()}: **{value}**" for key, value in values.items()]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    try:
        metrics = run()
    except ValidationError as exc:
        print(f"minerals pipeline validation failed: {exc}")
        return 1
    if args.summary:
        write_summary(metrics, args.summary)
    print(json.dumps(asdict(metrics), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

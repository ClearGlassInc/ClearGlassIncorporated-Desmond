#!/usr/bin/env python3
"""Produce a reviewable, non-mutating WAF/rate false-positive analysis.

Input is JSON Lines exported from the provider and enriched by a reviewer with
``classification`` = ``legitimate``, ``malicious``, or ``unknown``. Cloudflare
field names (``Datetime``, ``RuleID``, ``Action``) and provider-neutral lower-case
names are both accepted. The script recommends at most an action; it never edits
Terraform or calls a provider API.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

CLASSIFICATIONS = {"legitimate", "malicious", "unknown"}
HIGH_CONFIDENCE_BLOCK_RULES = {
    "path_traversal_and_probe",
    "confirmed_abuse_ip_deny",
}


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def read_events(paths: Iterable[Path]) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    errors: list[str] = []
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            errors.append(f"{path}: {exc}")
            continue
        for line_number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}:{line_number}: invalid JSON: {exc.msg}")
                continue
            if not isinstance(item, dict):
                errors.append(f"{path}:{line_number}: event must be an object")
                continue
            rule = item.get("rule_key") or item.get("rule_id") or item.get("RuleID")
            if not isinstance(rule, str) or not rule.strip() or len(rule) > 160:
                errors.append(f"{path}:{line_number}: missing/invalid rule_key or RuleID")
                continue
            classification = item.get("classification", "unknown")
            if classification not in CLASSIFICATIONS:
                errors.append(f"{path}:{line_number}: unsupported classification")
                continue
            events.append(
                {
                    "rule": rule.strip(),
                    "classification": classification,
                    "timestamp": parse_time(item.get("timestamp") or item.get("Datetime")),
                    "verified_bot": item.get("verified_bot") is True,
                    "challenge_solved": item.get("challenge_solved")
                    if isinstance(item.get("challenge_solved"), bool)
                    else None,
                    "action": str(item.get("action") or item.get("Action") or "unknown")[:40],
                }
            )
    return events, errors


def recommendation(rule: str, stats: dict[str, Any], window_days: float) -> tuple[str, list[str]]:
    reasons: list[str] = []
    total = stats["total"]
    legitimate = stats["legitimate"]
    malicious = stats["malicious"]
    unknown = stats["unknown"]
    labeled = legitimate + malicious
    false_positive_rate = legitimate / labeled if labeled else 1.0
    unknown_rate = unknown / total if total else 1.0
    solved = stats["challenge_solved"]
    challenges = stats["challenge_samples"]

    if window_days < 7:
        reasons.append("observation window is shorter than seven days")
    if total < 100:
        reasons.append("fewer than 100 matches")
    if labeled < 50:
        reasons.append("fewer than 50 reviewer-labeled matches")
    if stats["verified_bot_legitimate"]:
        reasons.append("verified-bot traffic was classified legitimate")
    if unknown_rate > 0.25:
        reasons.append("more than 25% of matches remain unknown")
    if reasons:
        return "log", reasons

    challenge_ready = false_positive_rate <= 0.01 and malicious >= 25
    block_ready = (
        rule in HIGH_CONFIDENCE_BLOCK_RULES
        and false_positive_rate == 0
        and malicious >= 100
        and unknown_rate <= 0.05
        and challenges >= 20
        and solved / challenges <= 0.02
    )
    if block_ready:
        return "block", ["high-confidence rule met zero-FP, volume, unknown-rate, and challenge-solve gates"]
    if challenge_ready:
        return "managed_challenge", ["false-positive rate is at most 1% with sufficient malicious samples"]
    if false_positive_rate > 0.01:
        reasons.append("false-positive rate exceeds 1%")
    if malicious < 25:
        reasons.append("fewer than 25 malicious labeled matches")
    return "log", reasons or ["promotion gates were not met"]


def analyze(events: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "total": 0,
            "legitimate": 0,
            "malicious": 0,
            "unknown": 0,
            "verified_bot_legitimate": 0,
            "challenge_samples": 0,
            "challenge_solved": 0,
            "actions": defaultdict(int),
        }
    )
    timestamps = [event["timestamp"] for event in events if event["timestamp"] is not None]
    window_start = min(timestamps) if timestamps else None
    window_end = max(timestamps) if timestamps else None
    window_days = (
        (window_end - window_start).total_seconds() / 86400
        if window_start is not None and window_end is not None
        else 0.0
    )

    for event in events:
        stats = grouped[event["rule"]]
        stats["total"] += 1
        stats[event["classification"]] += 1
        stats["actions"][event["action"]] += 1
        if event["verified_bot"] and event["classification"] == "legitimate":
            stats["verified_bot_legitimate"] += 1
        if event["challenge_solved"] is not None:
            stats["challenge_samples"] += 1
            stats["challenge_solved"] += int(event["challenge_solved"])

    rules = []
    for rule, stats in sorted(grouped.items()):
        action, reasons = recommendation(rule, stats, window_days)
        labeled = stats["legitimate"] + stats["malicious"]
        rules.append(
            {
                "rule": rule,
                "matches": stats["total"],
                "legitimate": stats["legitimate"],
                "malicious": stats["malicious"],
                "unknown": stats["unknown"],
                "false_positive_rate": round(stats["legitimate"] / labeled, 6) if labeled else None,
                "unknown_rate": round(stats["unknown"] / stats["total"], 6),
                "verified_bot_legitimate": stats["verified_bot_legitimate"],
                "challenge_solve_rate": round(
                    stats["challenge_solved"] / stats["challenge_samples"], 6
                )
                if stats["challenge_samples"]
                else None,
                "observed_actions": dict(sorted(stats["actions"].items())),
                "recommended_action": action,
                "reasons": reasons,
            }
        )
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "observation_window_start": window_start.isoformat().replace("+00:00", "Z") if window_start else None,
        "observation_window_end": window_end.isoformat().replace("+00:00", "Z") if window_end else None,
        "observation_window_days": round(window_days, 3),
        "event_count": len(events),
        "rules": rules,
        "automatic_provider_changes": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path, help="Reviewer-enriched JSONL event files.")
    parser.add_argument("--output", type=Path, required=True, help="Reviewable JSON evidence artifact.")
    args = parser.parse_args()

    events, errors = read_events(args.inputs)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if not events:
        print("ERROR: no valid security events were supplied", file=sys.stderr)
        return 2

    report = analyze(events)
    encoded = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded)
    digest = hashlib.sha256(encoded).hexdigest()
    print(f"Security observation report: {args.output}")
    print(f"promotion_evidence_sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Aggregate privacy-minimized CSP JSONL without automatically widening policy."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def configured_for_directive(inventory: dict[str, Any], directive: str, origin: str) -> bool:
    source_map = inventory.get("csp_sources", {})
    base = directive.removesuffix("-elem").removesuffix("-attr")
    sources = source_map.get(base) or source_map.get("default-src") or []
    if not isinstance(sources, list):
        return False
    return origin in sources or (origin.startswith("https://") and "https:" in sources)


def read_reports(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    reports: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [], [str(exc)]
    for number, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line:
            continue
        if "csp_violation " in line:
            line = line.split("csp_violation ", 1)[1]
        try:
            report = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {number}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(report, dict):
            errors.append(f"line {number}: report must be an object")
            continue
        reports.append(report)
    return reports, errors


def analyze(reports: list[dict[str, Any]], inventory: dict[str, Any]) -> dict[str, Any]:
    counts: Counter[tuple[str, str]] = Counter()
    for report in reports:
        directive = str(report.get("effective_directive") or "unknown")[:160]
        blocked = str(report.get("blocked_origin") or "unknown")[:512]
        counts[(directive, blocked)] += 1

    findings = []
    for (directive, blocked), count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        configured = configured_for_directive(inventory, directive, blocked)
        findings.append(
            {
                "directive": directive,
                "blocked_origin": blocked,
                "count": count,
                "already_configured": configured,
                "disposition": "investigate-policy-or-browser-noise" if configured else "unreviewed-source",
            }
        )
    unresolved = sum(item["count"] for item in findings if not item["already_configured"])
    manual = inventory.get("manual_review_required", [])
    return {
        "schema_version": 1,
        "report_count": len(reports),
        "unresolved_report_count": unresolved,
        "findings": findings,
        "manual_review_required": manual if isinstance(manual, list) else [],
        "enforcement_ready": len(reports) >= 500 and unresolved == 0 and not manual,
        "policy_widened_automatically": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="JSONL from the CSP collector logs.")
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-enforcement-ready", action="store_true")
    args = parser.parse_args()
    try:
        inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot load inventory: {exc}", file=sys.stderr)
        return 2
    reports, errors = read_reports(args.input)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    result = analyze(reports, inventory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"CSP analysis: {len(reports)} reports, {result['unresolved_report_count']} unresolved")
    if args.require_enforcement_ready and not result["enforcement_ready"]:
        print("ERROR: CSP enforcement evidence gate is not satisfied", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

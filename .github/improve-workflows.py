#!/usr/bin/env python3
"""Analyze workflow metadata and propose fail-closed improvements.

This tool is intentionally proposal-only. It does not modify workflows, bypass
controls, create credentials, or deploy production artifacts.
"""
from __future__ import annotations

import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent
PATTERNS = ROOT / "workflow-patterns.json"
OUT = ROOT / "workflow-improvement-suggestions.md"


def main() -> int:
    data = json.loads(PATTERNS.read_text(encoding="utf-8"))
    patterns = data.get("patterns", [])
    counts = Counter(p.get("root_cause", "unknown") for p in patterns)

    lines = ["# Workflow Improvement Suggestions", "", "Generated from verified pattern records.", ""]
    if not patterns:
        lines += ["No verified failure patterns are currently recorded.", ""]
    else:
        for category, count in counts.most_common():
            lines.append(f"- `{category}`: {count} recorded occurrence(s)")
        lines += ["", "## Guardrails", "", "- Suggestions are advisory until reviewed.", "- Never auto-bypass production controls.", "- Never write secret values to repository files.", "- Never convert an unexecuted/blocked workflow into PASS."]

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

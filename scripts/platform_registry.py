# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""ClearGlass Intelligence Platform — registry loader, validator, and reporter.

`data/platform/architecture.json` is the canonical, machine-readable source of
truth for the platform's brand + system taxonomy: the executive platform tiers,
the autonomous agent framework, the enterprise hierarchy, the product family,
and the naming standard that ties them together.

This module keeps that registry honest as it grows. It is stdlib-only (no third
-party imports) so it runs in minimal CI environments, mirroring the convention
used by `governance.py` / `daily_loop.py` elsewhere in the monorepo.

Guarantees enforced here (and by `tests/test_platform_registry.py`):

  * The registry parses and carries every required top-level section.
  * Every entry declares a status drawn from the published legend.
  * Names are unique within each agent-framework category and globally
    consistent (an `operational` name never silently downgrades to `reserved`).
  * Every `operational` entry points at an artifact path that actually exists
    on disk — an operational name is a claim, and the claim must be backed by a
    shipping file. `reserved` entries carry no artifact (namespace only).
  * The naming standard is well-formed: each tier has a prefix, example, and a
    `<...>` pattern.

Run as a script for a human-readable report or a machine-readable summary:

    python -m scripts.platform_registry            # report
    python -m scripts.platform_registry --json      # summary as JSON
    python -m scripts.platform_registry --validate  # exit 1 on any problem
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "data" / "platform" / "architecture.json"

VALID_STATUSES = ("operational", "reserved")
REQUIRED_SECTIONS = (
    "naming_standard",
    "executive_layer",
    "agent_framework",
    "hierarchy",
    "product_family",
)


def load(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    """Load and parse the platform registry."""
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _iter_named_entries(registry: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Yield (context, entry) for every status-bearing entry in the registry."""
    entries: list[tuple[str, dict[str, Any]]] = []
    for entry in registry.get("executive_layer", []):
        entries.append(("executive_layer", entry))
    for category, agents in registry.get("agent_framework", {}).items():
        for entry in agents:
            entries.append((f"agent_framework/{category}", entry))
    for entry in registry.get("hierarchy", {}).get("branches", []):
        entries.append(("hierarchy", entry))
    for entry in registry.get("product_family", []):
        entries.append(("product_family", entry))
    return entries


def validate(registry: dict[str, Any], repo_root: Path = REPO_ROOT) -> list[str]:
    """Return a list of human-readable problems; empty list means the registry is sound."""
    problems: list[str] = []

    for section in REQUIRED_SECTIONS:
        if section not in registry:
            problems.append(f"missing required section: {section}")

    # Naming standard must be well-formed.
    for row in registry.get("naming_standard", []):
        tier = row.get("tier", "<unnamed>")
        for field in ("tier", "prefix", "example", "pattern"):
            if not row.get(field):
                problems.append(f"naming_standard[{tier}]: missing '{field}'")
        pattern = row.get("pattern", "")
        if "<" not in pattern or ">" not in pattern:
            problems.append(f"naming_standard[{tier}]: pattern '{pattern}' has no <placeholder>")

    # Every agent-framework category must have unique names within it.
    for category, agents in registry.get("agent_framework", {}).items():
        seen: set[str] = set()
        for entry in agents:
            name = entry.get("name")
            if not name:
                problems.append(f"agent_framework/{category}: entry with no name")
                continue
            if name in seen:
                problems.append(f"agent_framework/{category}: duplicate name '{name}'")
            seen.add(name)

    # Artifact-bearing sections bind a name to a shipping file; the hierarchy is
    # a conceptual domain map whose nodes are validated structurally only.
    status_by_name: dict[str, str] = {}
    for context, entry in _iter_named_entries(registry):
        label = entry.get("name") or entry.get("node") or entry.get("product") or "<unnamed>"
        status = entry.get("status")
        if status not in VALID_STATUSES:
            problems.append(f"{context}/{label}: invalid status {status!r}")
            continue

        if context == "hierarchy":
            # Hierarchy nodes describe domains, not files — status only.
            if not entry.get("node") or not entry.get("domain"):
                problems.append(f"{context}/{label}: hierarchy node needs 'node' and 'domain'")
            continue

        # A name that is operational anywhere must not be reserved elsewhere.
        prior = status_by_name.get(label)
        if prior and prior != status:
            problems.append(
                f"{label}: inconsistent status — '{prior}' and '{status}' across sections"
            )
        # 'operational' wins so the inconsistency is only reported once.
        if status_by_name.get(label) != "operational":
            status_by_name[label] = status

        artifact = entry.get("artifact")
        if status == "operational":
            if not artifact:
                problems.append(f"{context}/{label}: operational but no artifact declared")
            elif not (repo_root / artifact).exists():
                problems.append(f"{context}/{label}: artifact not found on disk — {artifact}")
        elif status == "reserved" and artifact:
            problems.append(f"{context}/{label}: reserved but declares artifact {artifact!r}")

    return problems


def summarize(registry: dict[str, Any]) -> dict[str, Any]:
    """Return counts of operational vs. reserved names across the registry."""
    entries = _iter_named_entries(registry)
    operational = sum(1 for _, e in entries if e.get("status") == "operational")
    reserved = sum(1 for _, e in entries if e.get("status") == "reserved")
    agent_count = sum(len(v) for v in registry.get("agent_framework", {}).values())
    return {
        "platform": registry.get("platform"),
        "version": registry.get("version"),
        "total_names": len(entries),
        "operational": operational,
        "reserved": reserved,
        "agent_categories": len(registry.get("agent_framework", {})),
        "agents": agent_count,
        "products": len(registry.get("product_family", [])),
    }


def _report(registry: dict[str, Any]) -> str:
    s = summarize(registry)
    lines = [
        f"{s['platform']}  v{s['version']}",
        "=" * 52,
        f"Names in taxonomy : {s['total_names']}",
        f"  operational     : {s['operational']}  (bound to a shipping artifact)",
        f"  reserved        : {s['reserved']}  (namespace only, not provisioned)",
        f"Agent categories  : {s['agent_categories']}",
        f"Agents            : {s['agents']}",
        f"Product lines     : {s['products']}",
        "",
        "Naming standard:",
    ]
    for row in registry.get("naming_standard", []):
        lines.append(f"  {row['tier']:<15} {row['prefix']:<11} e.g. {row['example']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    registry = load()
    if "--json" in argv:
        print(json.dumps(summarize(registry), indent=2))
        return 0
    problems = validate(registry)
    if "--validate" in argv:
        if problems:
            print("Registry validation FAILED:", file=sys.stderr)
            for problem in problems:
                print(f"  - {problem}", file=sys.stderr)
            return 1
        print("Registry validation passed.")
        return 0
    print(_report(registry))
    if problems:
        print("\nWARNINGS:")
        for problem in problems:
            print(f"  - {problem}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""Tests for the ClearGlass Intelligence Platform registry.

These lock the canonical taxonomy (`data/platform/architecture.json`) to the
same honesty rule the rest of the monorepo follows: an `operational` name must
be backed by a shipping artifact, `reserved` names are namespace only, and the
naming standard stays well-formed. If someone marks a name operational without
wiring it to a real file, or introduces a duplicate/typo, these fail.
"""

from __future__ import annotations

from scripts import platform_registry as reg


def test_registry_loads_with_required_sections():
    registry = reg.load()
    for section in reg.REQUIRED_SECTIONS:
        assert section in registry, f"missing section: {section}"
    assert registry["platform"] == "ClearGlass Intelligence Platform"


def test_registry_validates_clean():
    registry = reg.load()
    problems = reg.validate(registry)
    assert problems == [], "registry validation problems:\n" + "\n".join(problems)


def test_all_operational_names_have_existing_artifacts():
    registry = reg.load()
    missing = []
    for context, entry in reg._iter_named_entries(registry):
        if context == "hierarchy":
            continue  # domain map, not artifact-bearing
        if entry.get("status") == "operational":
            artifact = entry.get("artifact")
            assert artifact, f"{context}: operational entry without artifact"
            if not (reg.REPO_ROOT / artifact).exists():
                missing.append(f"{context} -> {artifact}")
    assert not missing, "operational artifacts not found on disk:\n" + "\n".join(missing)


def test_reserved_names_carry_no_artifact():
    registry = reg.load()
    for context, entry in reg._iter_named_entries(registry):
        if entry.get("status") == "reserved":
            assert not entry.get("artifact"), f"{context}: reserved entry declares an artifact"


def test_naming_standard_is_well_formed():
    registry = reg.load()
    tiers = {row["tier"] for row in registry["naming_standard"]}
    # The taxonomy the platform is documented around.
    for expected in ("Platform", "Agent", "Security", "Analytics", "Executive"):
        assert expected in tiers, f"naming standard missing tier: {expected}"
    for row in registry["naming_standard"]:
        assert "<" in row["pattern"] and ">" in row["pattern"]


def test_agent_names_unique_within_category():
    registry = reg.load()
    for category, agents in registry["agent_framework"].items():
        names = [a["name"] for a in agents]
        assert len(names) == len(set(names)), f"duplicate agent name in {category}"


def test_summary_counts_are_consistent():
    registry = reg.load()
    s = reg.summarize(registry)
    assert s["operational"] + s["reserved"] == s["total_names"]
    assert s["agents"] > 0
    assert s["agent_categories"] == len(registry["agent_framework"])

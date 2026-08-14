# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""Tests for privacy-safe analytics and conversion instrumentation."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The pages a visitor actually moves through on the way to paying. Analytics is
# worthless if it is missing from these, so they are asserted explicitly.
FUNNEL_PAGES = (
    "index.html",
    "store.html",
    "pricing.html",
    "offers/security-quick-audit.html",
    "offers/thank-you.html",
)


def test_analytics_file_present_and_idempotent() -> None:
    js = (ROOT / "analytics.js").read_text(encoding="utf-8")
    assert "__cgAnalytics" in js, "analytics.js must guard against double-init"
    assert "window.cgTrack" in js, "analytics.js must expose a provider-neutral event API"
    assert "begin_checkout" in js
    assert "generate_lead" in js
    assert 'analytics_storage: "denied"' in js
    assert "allow_google_signals: false" in js
    assert "window.cgAnalyticsConsent" in js


def test_analytics_does_not_allow_pii_properties() -> None:
    js = (ROOT / "analytics.js").read_text(encoding="utf-8")
    allowlist = js.split("var SAFE_PROPERTY_KEYS = {", 1)[1].split("};", 1)[0]
    for forbidden in ("email", "phone", "name", "message", "organization"):
        assert f"{forbidden}: true" not in allowlist


def test_stealth_glass_loads_analytics() -> None:
    js = (ROOT / "stealth-glass.js").read_text(encoding="utf-8")
    assert "/analytics.js" in js, "stealth-glass.js must inject the analytics loader"
    assert "/analytics-config.js" in js, "destination config must load before analytics"


def test_destination_config_is_safe_by_default() -> None:
    js = (ROOT / "analytics-config.js").read_text(encoding="utf-8")
    assert 'provider: "queue"' in js
    assert 'measurementId: ""' in js
    for forbidden in ("sk_live_", "sk_test_", "ghp_", "password:"):
        assert forbidden not in js.lower()


def test_funnel_pages_carry_the_universal_loader() -> None:
    missing = [
        page for page in FUNNEL_PAGES
        if "stealth-glass.js" not in (ROOT / page).read_text(encoding="utf-8")
    ]
    assert not missing, f"funnel pages missing /stealth-glass.js (lose analytics): {missing}"


def test_quick_audit_form_has_attribution_pipeline() -> None:
    page = (ROOT / "offers/security-quick-audit.html").read_text(encoding="utf-8")
    assert "data-cg-lead-form" in page
    assert "/assets/js/lead-pipeline.js" in page
    assert "pipeline_stage" in page

"""Tests for the governance safety core (stdlib-only, no DB needed)."""
from __future__ import annotations

from app.governance import RiskTier, score_action


def test_read_metrics_is_auto_executable() -> None:
    a = score_action("read_metrics", {})
    assert a.tier == RiskTier.LOW
    assert a.requires_approval is False


def test_generate_copy_is_low_risk() -> None:
    a = score_action("generate_copy", {"product_slug": "x"})
    assert a.requires_approval is False


def test_pricing_change_always_requires_approval() -> None:
    a = score_action("update_pricing", {"old_price": 10, "new_price": 12})
    assert a.requires_approval is True
    assert a.tier in (RiskTier.HIGH, RiskTier.CRITICAL)


def test_payment_settings_is_critical() -> None:
    a = score_action("update_payment_settings", {})
    assert a.tier == RiskTier.CRITICAL
    assert a.requires_approval is True


def test_refund_is_gated() -> None:
    assert score_action("trigger_refund", {}).requires_approval is True


def test_unknown_action_fails_closed() -> None:
    a = score_action("mystery_action", {})
    assert a.requires_approval is True


def test_large_price_delta_raises_score() -> None:
    small = score_action("update_pricing", {"old_price": 100, "new_price": 102})
    large = score_action("update_pricing", {"old_price": 100, "new_price": 200})
    assert large.score >= small.score


def test_low_confidence_escalates() -> None:
    a = score_action("refresh_products", {}, low_confidence=True)
    assert any("low confidence" in r for r in a.reasons)
    # Operating rule 8: low confidence must hard-gate, not merely bump the score.
    assert a.requires_approval is True


def test_low_confidence_gates_low_base_action() -> None:
    # A low/medium-base action stays below the HIGH threshold after the score
    # bump, so without a dedicated gate it would auto-execute despite rule 8.
    baseline = score_action("generate_copy", {})
    assert baseline.requires_approval is False
    gated = score_action("generate_copy", {}, low_confidence=True)
    assert gated.requires_approval is True

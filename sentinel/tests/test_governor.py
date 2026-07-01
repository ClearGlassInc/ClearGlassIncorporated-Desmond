# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""Tests for sentinel/sentinel/governor.py — the sovereign Policy Governor."""
from __future__ import annotations

import pytest

from sentinel.capability import Tier
from sentinel.governor import PolicyGovernor
from sentinel.identity import AgentIdentity


def _identity(**kw) -> AgentIdentity:
    base = dict(
        instance_id="percival-8",
        sponsor="Desmond",
        purpose="governed execution",
        allowed_scopes={"strategy", "architecture", "implementation", "security", "operations"},
        default_tier=Tier.CHANGE,  # allow up to internal execution for tests
    )
    base.update(kw)
    return AgentIdentity(**base)


def _request(**kw) -> dict:
    base = {
        "request_context": {"mission_id": "m1", "auth_token": "tok"},
        "action_scope": "read_only",
        "target_lane": ["strategy"],
    }
    base.update(kw)
    return base


# --------------------------------------------------------------------------- #
# schema validation
# --------------------------------------------------------------------------- #
def test_missing_required_field_is_denied():
    gov = PolicyGovernor(_identity())
    d = gov.evaluate({"action_scope": "read_only", "target_lane": ["strategy"]})
    assert d.allowed is False
    assert "schema violation" in d.reason


def test_missing_auth_token_is_denied():
    gov = PolicyGovernor(_identity())
    req = _request(request_context={"mission_id": "m1"})
    d = gov.evaluate(req)
    assert d.allowed is False
    assert "auth_token" in d.reason


def test_bad_action_scope_is_denied():
    gov = PolicyGovernor(_identity())
    d = gov.evaluate(_request(action_scope="sudo"))
    assert d.allowed is False
    assert "action_scope" in d.reason


def test_empty_lane_is_denied():
    gov = PolicyGovernor(_identity())
    d = gov.evaluate(_request(target_lane=[]))
    assert d.allowed is False


def test_invalid_lane_is_denied():
    gov = PolicyGovernor(_identity())
    d = gov.evaluate(_request(target_lane=["marketing"]))
    assert d.allowed is False


# --------------------------------------------------------------------------- #
# happy path + tiers
# --------------------------------------------------------------------------- #
def test_read_only_within_scope_is_allowed():
    gov = PolicyGovernor(_identity())
    d = gov.evaluate(_request(action_scope="read_only", target_lane=["strategy"]))
    assert d.allowed is True
    assert d.required_tier == Tier.READ_ONLY


def test_internal_execution_within_grant_is_allowed():
    gov = PolicyGovernor(_identity(default_tier=Tier.CHANGE))
    d = gov.evaluate(_request(action_scope="execute_internal", target_lane=["operations"]))
    assert d.allowed is True
    assert d.required_tier == Tier.CHANGE


def test_internal_execution_above_grant_is_denied():
    # Identity only granted READ_ONLY cannot execute internally (CHANGE).
    gov = PolicyGovernor(_identity(default_tier=Tier.READ_ONLY))
    d = gov.evaluate(_request(action_scope="execute_internal", target_lane=["operations"]))
    assert d.allowed is False
    assert d.escalate is False


# --------------------------------------------------------------------------- #
# escalation for high-power scopes
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("scope", ["execute_external", "modify_system"])
def test_high_power_scopes_escalate_not_execute(scope):
    gov = PolicyGovernor(_identity(default_tier=Tier.DEPLOY))
    d = gov.evaluate(_request(action_scope=scope, target_lane=["security"]))
    assert d.allowed is False
    assert d.escalate is True
    assert "human approval" in d.reason


# --------------------------------------------------------------------------- #
# lane scope / deny-by-default
# --------------------------------------------------------------------------- #
def test_lane_outside_identity_scope_is_denied():
    gov = PolicyGovernor(_identity(allowed_scopes={"strategy"}))
    d = gov.evaluate(_request(target_lane=["security"]))
    assert d.allowed is False
    assert "not in identity scope" in d.reason


def test_stopped_identity_denies_everything():
    ident = _identity()
    ident.stop()
    gov = PolicyGovernor(ident)
    d = gov.evaluate(_request())
    assert d.allowed is False
    assert "stopped" in d.reason


# --------------------------------------------------------------------------- #
# confidence threshold (EvalOps downgrade)
# --------------------------------------------------------------------------- #
def test_low_confidence_downgrades():
    gov = PolicyGovernor(_identity())
    d = gov.evaluate(_request(confidence_threshold=0.9), confidence=0.5)
    assert d.allowed is False
    assert "below threshold" in d.reason


def test_confidence_above_threshold_allows():
    gov = PolicyGovernor(_identity())
    d = gov.evaluate(_request(confidence_threshold=0.5), confidence=0.9)
    assert d.allowed is True


# --------------------------------------------------------------------------- #
# multi-lane synthesis + audit integrity
# --------------------------------------------------------------------------- #
def test_multi_lane_request_allowed_when_all_in_scope():
    gov = PolicyGovernor(_identity())
    d = gov.evaluate(_request(target_lane=["architecture", "operations"]))
    assert d.allowed is True
    assert d.lanes == ["architecture", "operations"]


def test_every_decision_is_audited_and_chain_verifies():
    gov = PolicyGovernor(_identity())
    gov.evaluate(_request())
    gov.evaluate(_request(action_scope="modify_system", target_lane=["security"]))
    assert gov.verify() is True
    assert len(gov.audit.entries) == 2

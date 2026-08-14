from dataclasses import replace

import pytest

from quantum_neural_glass.control_plane import (
    ActionKind,
    Approval,
    AppendOnlyAuditLog,
    ControlDecision,
    GlassCommand,
    GlassControlPlane,
    ImprovementCandidate,
    OperationalContext,
)


def context(*roles: str) -> OperationalContext:
    return OperationalContext("operator-1", "pilot-1", "CLG-ONT", frozenset(roles), "corr-1")


def command(**changes: object) -> GlassCommand:
    base = GlassCommand("cmd-1", "pane-1", "zone-a", ActionKind.APPLY_OPTICAL_STATE, 55, False)
    return replace(base, **changes)


def test_model_and_bci_commands_fail_closed_without_evidence() -> None:
    plane = GlassControlPlane()
    for source in ("model", "bci", "optimizer"):
        result = plane.submit(command(source=source), context("facility_operator"))
        assert result.decision is ControlDecision.BLOCK
        assert result.reason == "untrusted_source_without_evidence"


def test_physical_action_requires_separate_safety_approval_bound_to_digest() -> None:
    plane = GlassControlPlane()
    proposed = command(source="optimizer", evidence_ids=("telemetry-7",))
    ctx = context("facility_operator")
    assert plane.submit(proposed, ctx).decision is ControlDecision.NEEDS_APPROVAL
    approval = Approval(
        proposed.command_id,
        "safety-2",
        frozenset({"safety_officer"}),
        plane.command_digest(proposed),
        True,
    )
    event = plane.execute(proposed, ctx, approval)
    assert event["payload"]["adapter_status"] == "not_connected_reference_only"
    assert plane.audit.verify()


def test_changed_command_cannot_reuse_approval() -> None:
    plane = GlassControlPlane()
    original = command(evidence_ids=("operator-observation",))
    approval = Approval("cmd-1", "safety-2", frozenset({"safety_officer"}), plane.command_digest(original), True)
    with pytest.raises(PermissionError, match="changed after approval"):
        plane.execute(replace(original, tint_percent=90), context("facility_operator"), approval)


def test_safety_limits_and_invalid_values_fail_closed() -> None:
    plane = GlassControlPlane()
    assert plane.authorize(command(tint_percent=101), context("facility_operator")).decision is ControlDecision.BLOCK
    governance = command(action=ActionKind.CHANGE_SAFETY_LIMIT, tint_percent=None)
    assert plane.authorize(governance, context("facility_operator")).decision is ControlDecision.NEEDS_APPROVAL


def test_improvement_candidate_never_auto_promotes() -> None:
    plane = GlassControlPlane()
    candidate = ImprovementCandidate(
        "candidate-9", "optical-router", "1.4.0", "1.4.1",
        {"precision": 0.94, "recall": 0.89, "p95_latency_ms": 180, "policy_violations": 0},
        "1.4.0", ("model-governance-1", "safety-owner-2"),
    )
    result = plane.evaluate_improvement(candidate)
    assert result.decision is ControlDecision.NEEDS_APPROVAL
    assert result.reason == "apollo_canary_only"


def test_policy_regression_blocks_candidate() -> None:
    plane = GlassControlPlane()
    candidate = ImprovementCandidate(
        "candidate-10", "optical-router", "1.4.0", "1.4.1",
        {"precision": 0.99, "recall": 0.99, "p95_latency_ms": 50, "policy_violations": 1},
        "1.4.0", ("review-1", "review-2"),
    )
    assert plane.evaluate_improvement(candidate).reason == "policy_regression"


def test_audit_chain_detects_tampering() -> None:
    audit = AppendOnlyAuditLog()
    audit.append("one", {"safe": True})
    audit.append("two", {"safe": True})
    assert audit.verify()
    audit.records[0]["payload"]["safe"] = False
    assert not audit.verify()

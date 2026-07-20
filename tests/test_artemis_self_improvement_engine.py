from datetime import datetime, timezone

from tools.artemis_self_improvement_engine import (
    ArtemisImprovementEngine,
    FeedbackSignal,
    ProposalType,
    SignalType,
)


def _signal(signal_id: str, signal_type: SignalType, payload: dict) -> FeedbackSignal:
    return FeedbackSignal(
        signal_id=signal_id,
        signal_type=signal_type,
        mission_id="mission-alpha",
        ontology_object_id="alert-001",
        actor="operator.test",
        classification="SECRET",
        compartment="ARTEMIS",
        payload=payload,
        observed_at=datetime(2026, 7, 13, tzinfo=timezone.utc),
    )


def test_three_operator_corrections_generate_human_approved_prompt_proposal() -> None:
    engine = ArtemisImprovementEngine({"aip.agent.triage_copilot": "2.4.9"})
    signals = [
        _signal(
            "s1",
            SignalType.OPERATOR_CORRECTION,
            {"correction": "missed_context", "theme": "temporal_linkage"},
        ),
        _signal(
            "s2",
            SignalType.OPERATOR_CORRECTION,
            {"correction": "false_positive", "theme": "evidence_threshold"},
        ),
        _signal(
            "s3",
            SignalType.OPERATOR_CORRECTION,
            {"correction": "missed_context", "theme": "coalition_caveat"},
        ),
        _signal("s4", SignalType.ALERT_OUTCOME, {"final_disposition": "validated"}),
        _signal("s5", SignalType.LATENCY_SAMPLE, {"latency_ms": 412}),
    ]

    proposals = engine.synthesize_proposals(signals)

    assert len(proposals) == 1
    proposal = proposals[0]
    assert proposal.proposal_type == ProposalType.PROMPT_PATCH
    assert proposal.current_version == "2.4.9"
    assert proposal.proposed_version == "2.4.10"
    assert proposal.approval_required is True
    assert proposal.rollout_ring == "staging-canary"
    assert "Never convert a recommendation" in " ".join(proposal.patch["guardrail_additions"])
    assert proposal.signed_manifest["signature"]


def test_fewer_than_three_operator_corrections_do_not_generate_proposal() -> None:
    engine = ArtemisImprovementEngine({"aip.agent.triage_copilot": "2.4.9"})
    signals = [
        _signal("s1", SignalType.OPERATOR_CORRECTION, {"correction": "missed_context"}),
        _signal("s2", SignalType.OPERATOR_CORRECTION, {"correction": "false_positive"}),
    ]

    assert engine.synthesize_proposals(signals) == []


def test_generated_proposal_carries_eval_gate_and_drift_controls() -> None:
    engine = ArtemisImprovementEngine({"aip.agent.triage_copilot": "2.4.9"})
    signals = [
        _signal(
            "s1",
            SignalType.OPERATOR_CORRECTION,
            {"correction": "missed_context", "theme": "temporal_linkage"},
        ),
        _signal(
            "s2",
            SignalType.OPERATOR_CORRECTION,
            {"correction": "missed_context", "theme": "temporal_linkage"},
        ),
        _signal(
            "s3",
            SignalType.OPERATOR_CORRECTION,
            {"correction": "missed_context", "theme": "temporal_linkage"},
        ),
    ]

    proposal = engine.synthesize_proposals(signals)[0]

    assert proposal.approval_state.value == "eval_failed"
    assert proposal.policy_decision == "blocked_eval_threshold"
    assert proposal.drift_score == 1.0
    assert proposal.patch["rollout_controls"] == {
        "canary_percentage": 5,
        "rollback_on_policy_violation": True,
        "rollback_on_p95_latency_ms": 1200,
    }


def test_invalid_component_version_fails_closed() -> None:
    engine = ArtemisImprovementEngine({"aip.agent.triage_copilot": "latest"})
    signals = [
        _signal("s1", SignalType.OPERATOR_CORRECTION, {"correction": "missed_context"}),
        _signal("s2", SignalType.OPERATOR_CORRECTION, {"correction": "false_positive"}),
        _signal("s3", SignalType.OPERATOR_CORRECTION, {"correction": "missed_context"}),
    ]

    try:
        engine.synthesize_proposals(signals)
    except ValueError as exc:
        assert "MAJOR.MINOR.PATCH" in str(exc)
    else:
        raise AssertionError("invalid component versions must fail closed")

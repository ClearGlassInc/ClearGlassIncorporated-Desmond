from artemis.intelligence import (
    AccessContext,
    Alert,
    FeedbackEvent,
    OntologyEntity,
    SelfImprovementEngine,
    WorkflowState,
)
from artemis.intelligence.platform import InMemoryOntologyStore, PolicyEngine, TriageAgent


def test_triage_agent_requires_approval_for_visible_alert() -> None:
    ontology = InMemoryOntologyStore()
    ontology.entities["entity-1"] = OntologyEntity(
        entity_id="entity-1",
        kind="infrastructure",
        canonical_name="edge-node-17",
        confidence=0.91,
        markings=frozenset({"ARTEMIS"}),
        lineage=("obs-1",),
    )
    context = AccessContext(
        operator_id="op-1",
        roles=frozenset({"analyst"}),
        mission_ids=frozenset({"mission-1"}),
        compartments=frozenset({"ARTEMIS"}),
        coalition="internal",
        purpose="triage",
    )
    alert = Alert(
        alert_id="alert-1",
        mission_id="mission-1",
        severity="high",
        hypothesis="Suspicious infrastructure behavior",
        entity_ids=("entity-1",),
        evidence_refs=("obs-1",),
        markings=frozenset({"ARTEMIS"}),
        workflow_state=WorkflowState.RECEIVED,
    )

    action = TriageAgent(ontology, PolicyEngine()).triage(context, alert)

    assert action.required_approval is True
    assert action.risk_tier == "high"
    assert action.parameters["visible_entity_count"] == 1


def test_self_improvement_requires_eval_gates() -> None:
    engine = SelfImprovementEngine(minimum_precision=0.90, maximum_latency_ms=1_500)
    feedback = [
        FeedbackEvent(
            feedback_id="fb-1",
            operator_id="op-1",
            artifact_id="alert-1",
            workflow_version="triage.v1",
            rating=1,
            correction="Maintenance window was not considered before escalation.",
            outcome="false_positive",
        )
    ]

    proposal = engine.proposal_from_feedback(
        feedback=feedback,
        target="triage_prompt",
        current_version="triage.v1",
        candidate_prompt="Check maintenance windows before severity escalation.",
        eval_metrics={"precision": 0.94, "recall": 0.91, "p95_latency_ms": 900},
    )

    assert proposal is not None
    assert proposal.requires_human_approval is True
    assert proposal.candidate_version.startswith("triage.v1+")


def test_feedback_compiler_redacts_disallowed_fields() -> None:
    from artemis.intelligence import compile_feedback_to_eval

    eval_example = compile_feedback_to_eval(
        {
            "signal_id": "sig-1",
            "task_type": "action_recommendation",
            "reason": "overconfident_single_source",
            "latency_budget_ms": 1_800,
            "policy_decision": {"allowed_fields": ["case_id", "summary"]},
            "input_snapshot": {
                "case_id": "case-1",
                "summary": "single-source correlation",
                "restricted_source": "do-not-copy",
            },
            "operator_correction": {
                "required_phrases": ["single-source"],
                "forbidden_phrases": ["confirmed hostile intent"],
            },
        }
    )

    assert eval_example["input_snapshot"] == {
        "case_id": "case-1",
        "summary": "single-source correlation",
    }
    assert "restricted_source" not in eval_example["input_snapshot"]
    assert eval_example["expected_behavior"]["requires_uncertainty_statement"] is True
    assert eval_example["rubric"]["p95_latency_ms"]["maximum"] == 1_800


def test_promotion_controller_requires_policy_approvals_and_rollback() -> None:
    from artemis.intelligence import ApprovalToken, PromotionController, ReleaseCandidate

    approvals = (
        ApprovalToken("op-mission", "mission_owner", "policy.v1"),
        ApprovalToken("op-gov", "governance_reviewer", "policy.v1"),
        ApprovalToken("op-sec", "security_officer", "policy.v1"),
    )
    candidate = ReleaseCandidate(
        candidate_version="triage.v2",
        baseline_version="triage.v1",
        target="triage_prompt",
        eval_metrics={
            "precision": 0.95,
            "p95_latency_ms": 900,
            "policy_pass_rate": 1.0,
            "unsafe_action_rate": 0.0,
        },
        rollback_pointer="triage.v1",
        approvals=approvals,
    )

    decision = PromotionController().evaluate(candidate)

    assert decision.allowed is True
    assert decision.deployment_ring == "mission-cell-5pct"


def test_promotion_controller_blocks_unsafe_or_unapproved_candidate() -> None:
    from artemis.intelligence import PromotionController, ReleaseCandidate

    candidate = ReleaseCandidate(
        candidate_version="triage.v2",
        baseline_version="triage.v1",
        target="triage_prompt",
        eval_metrics={
            "precision": 0.99,
            "p95_latency_ms": 500,
            "policy_pass_rate": 1.0,
            "unsafe_action_rate": 0.01,
        },
        rollback_pointer="triage.v1",
        approvals=(),
    )

    decision = PromotionController().evaluate(candidate)

    assert decision.allowed is False
    assert decision.reason == "unsafe action rate must be zero"

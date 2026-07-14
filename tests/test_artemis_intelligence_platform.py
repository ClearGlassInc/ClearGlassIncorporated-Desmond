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


def test_self_improvement_blocks_unapproved_or_regressed_candidates() -> None:
    engine = SelfImprovementEngine(
        minimum_precision=0.90,
        maximum_latency_ms=1_500,
        minimum_recall=0.80,
        maximum_policy_denials_delta=0.0,
    )

    unapproved = engine.evaluate_candidate(
        current_version="triage.v1",
        candidate_version="triage.v2",
        eval_metrics={
            "precision": 0.95,
            "recall": 0.88,
            "p95_latency_ms": 700,
            "policy_denials_delta": 0.0,
        },
        human_approved=False,
    )

    assert unapproved.passed is False
    assert unapproved.rollback_version == "triage.v1"
    assert unapproved.candidate_version is None
    assert "human approval is required" in unapproved.reasons

    policy_regression = engine.evaluate_candidate(
        current_version="triage.v1",
        candidate_version="triage.v2",
        eval_metrics={
            "precision": 0.95,
            "recall": 0.88,
            "p95_latency_ms": 700,
            "policy_denials_delta": 0.01,
        },
        human_approved=True,
    )

    assert policy_regression.passed is False
    assert "policy denial rate regressed" in policy_regression.reasons

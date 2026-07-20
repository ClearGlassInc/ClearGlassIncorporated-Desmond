from artemis.intelligence.platform import (
    AccessContext,
    AgentAction,
    ApprovalGate,
    FeedbackEvent,
    ImmutableAuditLog,
    PolicyEngine,
    PromotionController,
    ReleaseCandidate,
    SelfImprovementEngine,
    compile_feedback_to_eval,
)


def test_self_improvement_gate_requires_human_approval_and_quality_thresholds():
    engine = SelfImprovementEngine()

    blocked = engine.evaluate_candidate(
        current_version="triage-v1",
        candidate_version="triage-v2",
        eval_metrics={
            "precision": 0.91,
            "recall": 0.90,
            "p95_latency_ms": 900,
            "policy_denials_delta": 0,
        },
        human_approved=False,
    )

    assert not blocked.passed
    assert blocked.candidate_version is None
    assert blocked.rollback_version == "triage-v1"
    assert "precision below required threshold" in blocked.reasons
    assert "human approval is required" in blocked.reasons

    passed = engine.evaluate_candidate(
        current_version="triage-v1",
        candidate_version="triage-v2",
        eval_metrics={
            "precision": 0.94,
            "recall": 0.89,
            "p95_latency_ms": 900,
            "policy_denials_delta": 0,
        },
        human_approved=True,
    )

    assert passed.passed
    assert passed.candidate_version == "triage-v2"
    assert passed.rollback_version == "triage-v1"


def test_promotion_controller_blocks_invalid_rollback_and_audits_decision():
    audit_log = ImmutableAuditLog()
    controller = PromotionController(SelfImprovementEngine(), audit_log)
    context = AccessContext(
        operator_id="governance-reviewer-1",
        roles=frozenset({"governance"}),
        mission_ids=frozenset({"mission-7"}),
        compartments=frozenset({"alpha"}),
        coalition="CLEARGLASSINC",
        purpose="evaluation",
    )

    decision = controller.review_for_canary(
        context,
        ReleaseCandidate(
            candidate_id="candidate-1",
            proposal_id="proposal-1",
            artifact_type="prompt",
            baseline_version="triage-v1",
            candidate_version="triage-v2",
            rollback_version="triage-v2",
            eval_metrics={
                "precision": 0.95,
                "recall": 0.90,
                "p95_latency_ms": 700,
                "policy_denials_delta": 0,
            },
            human_approved=True,
        ),
    )

    assert not decision.canary_allowed
    assert "rollback version must differ from candidate version" in decision.reasons
    assert audit_log.verify()
    assert audit_log.records[-1].decision == "DENY"


def test_approval_gate_denies_high_risk_action_without_commander_role():
    audit_log = ImmutableAuditLog()
    gate = ApprovalGate(PolicyEngine(), audit_log)
    context = AccessContext(
        operator_id="analyst-1",
        roles=frozenset({"analyst"}),
        mission_ids=frozenset({"mission-7"}),
        compartments=frozenset({"alpha"}),
        coalition="CLEARGLASSINC",
        purpose="investigation",
    )
    action = AgentAction(
        action_id="action-1",
        action_type="external.execute",
        mission_id="mission-7",
        risk_tier="high",
        summary="High-risk action package.",
        required_approval=True,
        evidence_refs=("evidence-1",),
        parameters={},
    )

    decision = gate.approve(context, action, "approve", "Reviewed evidence")

    assert not decision.allowed
    assert decision.reason == "high-risk action requires commander role"
    assert audit_log.verify()
    assert audit_log.records[-1].decision == "REJECT"


def test_compile_feedback_to_eval_keeps_stable_ids_and_operator_expected_behavior():
    feedback = FeedbackEvent(
        feedback_id="feedback-1",
        operator_id="operator-1",
        artifact_id="recommendation-1",
        workflow_version="workflow-v3",
        rating=2,
        correction="Require second independent lineage source before escalation.",
        outcome="false_positive",
    )

    eval_case = compile_feedback_to_eval(feedback)

    assert eval_case["eval_id"] == "eval-feedback-1"
    assert eval_case["artifact_id"] == "recommendation-1"
    assert eval_case["workflow_version"] == "workflow-v3"
    assert eval_case["expected_behavior"] == {
        "correction": "Require second independent lineage source before escalation.",
        "outcome": "false_positive",
        "rating": 2,
    }
    assert eval_case["source_feedback_ids"] == ["feedback-1"]

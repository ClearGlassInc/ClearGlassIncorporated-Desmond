from artemis_legal_agent_mvp import (
    LegalCaseState,
    LegalDocument,
    LegalTechWorkflow,
    RiskLevel,
    demo_matter,
    evaluate_workflow,
)


def test_demo_workflow_uses_multiple_agents_and_preserves_counsel_gate():
    state = LegalTechWorkflow().run(demo_matter())

    assert len(LegalTechWorkflow().agents) >= 2
    assert state.approval_required is True
    assert state.risk_level is RiskLevel.CRITICAL
    assert "privacy_ai" in state.extracted_clauses
    assert "Northstar Holdings LLC" in state.osint_entities
    assert any("recommendation_agent" in item for item in state.trace)


def test_eval_harness_meets_less_than_five_percent_error_target():
    fixtures = [
        (demo_matter(), RiskLevel.CRITICAL),
        (
            LegalCaseState(
                matter_id="low-001",
                jurisdiction="Ontario",
                documents=[LegalDocument("d1", "NDA", "The parties exchange general business information.")],
            ),
            RiskLevel.LOW,
        ),
        (
            LegalCaseState(
                matter_id="medium-001",
                jurisdiction="Delaware",
                documents=[LegalDocument("d2", "Terms", "Acme Corp may terminate for default. Governing law is Delaware.")],
            ),
            RiskLevel.MEDIUM,
        ),
    ]

    metrics = evaluate_workflow(fixtures)

    assert metrics["error_rate"] < 0.05
    assert metrics["counsel_gate_rate"] == 1.0

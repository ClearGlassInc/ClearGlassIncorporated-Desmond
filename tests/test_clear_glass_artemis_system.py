from artemis_platform.clear_glass_artemis_system import (
    ApprovalGate,
    ArtemisArchitecture,
    OperatorFeedback,
    SelfImprovementEngine,
    run_cinematic_scenario,
)


def test_architecture_mentions_clear_glass_and_palantir_layers():
    markdown = ArtemisArchitecture().as_markdown()
    assert "ClearGlassInc Artemis" in markdown
    assert "Gotham" in markdown
    assert "Foundry" in markdown
    assert "AIP" in markdown
    assert "Apollo" in markdown


def test_cinematic_scenario_requires_human_gate_and_builds_upgrade_proposal():
    result = run_cinematic_scenario()
    recommendation = result["recommendation"]
    proposal = result["upgrade_proposal"]
    assert recommendation.gate is ApprovalGate.OPERATIONAL_EFFECT
    assert result["approval_required"] is True
    assert proposal is not None
    assert proposal.rollback_pointer == "triage_workflow.v1"
    assert result["promotion_decision"] in {"approve", "reject", "revise"}


def test_self_improvement_requires_enough_feedback_before_proposing():
    engine = SelfImprovementEngine()
    feedback = [OperatorFeedback("r1", "approve", "good", 0.9, 100)]
    assert engine.propose(feedback, "v1", [0.8, 0.81, 0.82, 0.83, 0.84]) is None

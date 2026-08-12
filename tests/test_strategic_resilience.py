from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from artemis.strategic_resilience import (
    ApprovalWorkflow, AuditLedger, BearCase, LifecycleStage, RecommendationState,
    ResilienceEngine, Signal, SignalType, Source,
)


def signal(stage: LifecycleStage = LifecycleStage.ANNOUNCED, budget: str | None = None) -> Signal:
    now = datetime.now(UTC)
    return Signal(
        title="Public remote-infrastructure program", source=Source(
            name="Public agency", url="https://example.gov/program", published_at=now - timedelta(days=1),
            retrieved_at=now, source_type="government", primary=True, independent=True,
            reliability=5, supporting_passage="The agency published a funded remote monitoring program.",
        ), geography=("Canada",), organizations=("Public agency",), domain="ARCTIC",
        signal_type=SignalType.INFRASTRUCTURE, lifecycle_stage=stage,
        strategic_relevance="Remote resilience", commercial_relevance="Monitoring demand",
        credibility_relevance="Public program", urgency=3, confidence=.9,
        potential_customer_types=("utilities", "ports"), potential_capabilities=("monitoring",),
        likely_budget_path=budget, dependencies=("connectivity",), next_validation_action="Verify tender documents",
        owner="strategy", review_date=now + timedelta(days=7),
    )


def diversified() -> BearCase:
    return BearCase(1, 1, 1, 1, 1, 1, 1, 1, 1)


def test_policy_announcement_never_permits_revenue_forecast() -> None:
    assessment = ResilienceEngine().assess(
        signal(), diversified(), interpretation="Direction is relevant", inference="Demand may emerge",
        assumption="Commercial procurement follows", unknown="Timing", recommendation="Interview buyers",
        decision_trigger="Published tender",
    )
    assert assessment.revenue_forecast_permitted is False
    assert assessment.state is RecommendationState.DRAFT


def test_funded_signal_with_budget_path_can_enter_revenue_validation() -> None:
    assessment = ResilienceEngine().assess(
        signal(LifecycleStage.FUNDED, "published capital program"), diversified(),
        interpretation="Budget supports implementation", inference="A reusable pilot may fit",
        assumption="Commercial eligibility", unknown="Award criteria", recommendation="Validate buyer pain",
        decision_trigger="Buyer confirms delivery path",
    )
    assert assessment.revenue_forecast_permitted is True
    assert assessment.resilience_score == 80.0


def test_approval_workflow_fails_closed() -> None:
    assessment = ResilienceEngine().assess(
        signal(), diversified(), interpretation="i", inference="i", assumption="a", unknown="u",
        recommendation="r", decision_trigger="d",
    )
    with pytest.raises(ValueError, match="forbidden transition"):
        ApprovalWorkflow().transition(assessment, RecommendationState.APPROVED, actor="leader", reason="Looks reasonable")


def test_source_and_bear_case_validation() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        replace(signal().source, url="http://localhost/private").validate()
    with pytest.raises(ValueError, match="between 0 and 5"):
        BearCase(6, 0, 0, 0, 0, 0, 0, 0, 0)


def test_audit_ledger_detects_tampering() -> None:
    ledger = AuditLedger()
    ledger.append(actor="analyst", action="signal.assessed", payload={"signal_id": "SIG-1"})
    ledger.append(actor="reviewer", action="recommendation.reviewed", payload={"decision": "approve"})
    assert ledger.verify() is True
    ledger.records[0]["payload"] = {"signal_id": "changed"}
    assert ledger.verify() is False

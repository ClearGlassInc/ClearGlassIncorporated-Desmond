"""ClearGlassInc Artemis strategic resilience decision engine.

This module is deliberately deterministic and standard-library only.  Network
collectors, Palantir adapters, and language models may propose inputs, but this
boundary validates evidence, calculates commercial weight, and keeps every
recommendation in a human-approved workflow.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
import json
from urllib.parse import urlparse
from uuid import uuid4


class LifecycleStage(StrEnum):
    MENTIONED = "MENTIONED"
    ANNOUNCED = "ANNOUNCED"
    FUNDED = "FUNDED"
    PROCURED = "PROCURED"
    PILOTED = "PILOTED"
    DEPLOYED = "DEPLOYED"
    SCALED = "SCALED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    DELAYED = "DELAYED"
    UNCERTAIN = "UNCERTAIN"


class SignalType(StrEnum):
    POLICY = "Policy"
    BUDGET = "Budget"
    TENDER = "Tender"
    CONTRACT = "Contract"
    PARTNERSHIP = "Partnership"
    EXERCISE = "Exercise"
    STANDARD = "Standard"
    INFRASTRUCTURE = "Infrastructure"
    TECHNOLOGY = "Technology"
    REGULATION = "Regulation"
    SUPPLY_CHAIN = "Supply chain"
    MARKET_DEMAND = "Market demand"
    COMPETITIVE_MOVEMENT = "Competitive movement"
    CUSTOMER_PAIN = "Customer pain"
    CAPABILITY_GAP = "Capability gap"
    PUBLIC_CREDIBILITY = "Public credibility signal"


class RecommendationState(StrEnum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    VALIDATING = "VALIDATING"
    CLOSED = "CLOSED"


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    published_at: datetime
    retrieved_at: datetime
    source_type: str
    primary: bool
    independent: bool
    reliability: int
    supporting_passage: str

    def validate(self) -> None:
        parsed = urlparse(self.url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("sources must use a public HTTPS URL")
        if not 1 <= self.reliability <= 5:
            raise ValueError("source reliability must be between 1 and 5")
        if len(self.supporting_passage.strip()) < 20:
            raise ValueError("an exact supporting passage is required")
        if self.published_at > self.retrieved_at:
            raise ValueError("publication cannot postdate retrieval")


@dataclass(frozen=True)
class Signal:
    title: str
    source: Source
    geography: tuple[str, ...]
    organizations: tuple[str, ...]
    domain: str
    signal_type: SignalType
    lifecycle_stage: LifecycleStage
    strategic_relevance: str
    commercial_relevance: str
    credibility_relevance: str
    urgency: int
    confidence: float
    potential_customer_types: tuple[str, ...]
    potential_capabilities: tuple[str, ...]
    likely_budget_path: str | None
    dependencies: tuple[str, ...]
    next_validation_action: str
    owner: str
    review_date: datetime
    signal_id: str = field(default_factory=lambda: f"SIG-{uuid4().hex[:12].upper()}")
    observed_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def validate(self) -> None:
        self.source.validate()
        if self.domain not in {"ARCTIC", "NATO", "CROSS_MARKET"}:
            raise ValueError("domain must be ARCTIC, NATO, or CROSS_MARKET")
        if not 1 <= self.urgency <= 5 or not 0 <= self.confidence <= 1:
            raise ValueError("urgency must be 1..5 and confidence 0..1")
        if not self.next_validation_action.strip() or not self.owner.strip():
            raise ValueError("validation action and accountable owner are required")


@dataclass(frozen=True)
class BearCase:
    """Concentration exposure, where 0 is diversified and 5 is single-point dependency."""

    country: int
    procurement_cycle: int
    customer: int
    supply_chain: int
    cloud_provider: int
    hardware_category: int
    regulatory_assumption: int
    geopolitical_thesis: int
    public_funding: int

    def __post_init__(self) -> None:
        if any(not 0 <= value <= 5 for value in asdict(self).values()):
            raise ValueError("bear-case exposures must be between 0 and 5")

    @property
    def exposure(self) -> float:
        exposures = (
            self.country,
            self.procurement_cycle,
            self.customer,
            self.supply_chain,
            self.cloud_provider,
            self.hardware_category,
            self.regulatory_assumption,
            self.geopolitical_thesis,
            self.public_funding,
        )
        return round(sum(exposures) / (len(exposures) * 5) * 100, 1)

    @property
    def diversification_score(self) -> float:
        return round(100 - self.exposure, 1)


@dataclass(frozen=True)
class OpportunityAssessment:
    opportunity_id: str
    signal_id: str
    commercial_weight: float
    resilience_score: float
    total_score: float
    revenue_forecast_permitted: bool
    verified_fact: str
    interpretation: str
    analyst_inference: str
    assumption: str
    unknown: str
    recommendation: str
    decision_trigger: str
    validation_requirement: str
    state: RecommendationState = RecommendationState.DRAFT


_STAGE_WEIGHT = {
    LifecycleStage.MENTIONED: 5,
    LifecycleStage.ANNOUNCED: 15,
    LifecycleStage.FUNDED: 55,
    LifecycleStage.PROCURED: 80,
    LifecycleStage.PILOTED: 70,
    LifecycleStage.DEPLOYED: 85,
    LifecycleStage.SCALED: 95,
    LifecycleStage.COMPLETED: 20,
    LifecycleStage.CANCELLED: 0,
    LifecycleStage.DELAYED: 10,
    LifecycleStage.UNCERTAIN: 5,
}


class ResilienceEngine:
    """Scores public signals without converting headlines into invented revenue."""

    def assess(
        self,
        signal: Signal,
        bear_case: BearCase,
        *,
        interpretation: str,
        inference: str,
        assumption: str,
        unknown: str,
        recommendation: str,
        decision_trigger: str,
    ) -> OpportunityAssessment:
        signal.validate()
        stage_weight = _STAGE_WEIGHT[signal.lifecycle_stage]
        source_weight = signal.source.reliability * 4 + (8 if signal.source.primary else 0)
        commercial_weight = round(
            min(100, stage_weight * 0.65 + source_weight + signal.confidence * 12), 1
        )
        total = round(commercial_weight * 0.6 + bear_case.diversification_score * 0.4, 1)
        revenue_allowed = (
            signal.lifecycle_stage
            in {LifecycleStage.FUNDED, LifecycleStage.PROCURED, LifecycleStage.PILOTED,
                LifecycleStage.DEPLOYED, LifecycleStage.SCALED}
            and bool(signal.likely_budget_path and signal.potential_customer_types)
        )
        return OpportunityAssessment(
            opportunity_id=f"OPP-{uuid4().hex[:12].upper()}",
            signal_id=signal.signal_id,
            commercial_weight=commercial_weight,
            resilience_score=bear_case.diversification_score,
            total_score=total,
            revenue_forecast_permitted=revenue_allowed,
            verified_fact=signal.source.supporting_passage,
            interpretation=interpretation,
            analyst_inference=inference,
            assumption=assumption,
            unknown=unknown,
            recommendation=recommendation,
            decision_trigger=decision_trigger,
            validation_requirement=signal.next_validation_action,
        )


class ApprovalWorkflow:
    """Fail-closed state machine for consequential recommendation activation."""

    _TRANSITIONS = {
        RecommendationState.DRAFT: {RecommendationState.IN_REVIEW},
        RecommendationState.IN_REVIEW: {RecommendationState.APPROVED, RecommendationState.REJECTED},
        RecommendationState.APPROVED: {RecommendationState.VALIDATING},
        RecommendationState.VALIDATING: {RecommendationState.CLOSED},
        RecommendationState.REJECTED: {RecommendationState.CLOSED},
        RecommendationState.CLOSED: set(),
    }

    def transition(self, assessment: OpportunityAssessment, target: RecommendationState, *, actor: str, reason: str) -> OpportunityAssessment:
        if target not in self._TRANSITIONS[assessment.state]:
            raise ValueError(f"forbidden transition: {assessment.state} -> {target}")
        if not actor.strip() or len(reason.strip()) < 10:
            raise ValueError("actor and substantive reason are required")
        values = asdict(assessment)
        values["state"] = target
        return OpportunityAssessment(**values)


class AuditLedger:
    """Append-only, hash-chained decision evidence suitable for external persistence."""

    def __init__(self) -> None:
        self.records: list[dict[str, object]] = []

    def append(self, *, actor: str, action: str, payload: dict[str, object]) -> dict[str, object]:
        previous_hash = str(self.records[-1]["record_hash"]) if self.records else "GENESIS"
        record: dict[str, object] = {
            "record_id": str(uuid4()), "recorded_at": datetime.now(UTC).isoformat(),
            "actor": actor, "action": action, "payload": payload, "previous_hash": previous_hash,
        }
        canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), default=str)
        record["record_hash"] = sha256(canonical.encode()).hexdigest()
        self.records.append(record)
        return dict(record)

    def verify(self) -> bool:
        previous_hash = "GENESIS"
        for stored in self.records:
            candidate = dict(stored)
            claimed = candidate.pop("record_hash", None)
            if candidate["previous_hash"] != previous_hash:
                return False
            canonical = json.dumps(candidate, sort_keys=True, separators=(",", ":"), default=str)
            if claimed != sha256(canonical.encode()).hexdigest():
                return False
            previous_hash = str(claimed)
        return True

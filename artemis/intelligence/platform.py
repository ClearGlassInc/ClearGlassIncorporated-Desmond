"""Reference implementation skeleton for ClearGlassInc Artemis.

The module is intentionally dependency-light so it can act as executable
architecture documentation for ontology-driven intelligence workflows,
policy checks, feedback capture, and human-approved self-improvement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from statistics import fmean
from typing import Any, Callable, Protocol
from uuid import uuid4


class WorkflowState(StrEnum):
    """Human-gated lifecycle for operationally significant AI work."""

    RECEIVED = "received"
    TRIAGED = "triaged"
    ENRICHED = "enriched"
    RECOMMENDED = "recommended"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"


@dataclass(frozen=True)
class AccessContext:
    """Signed request context propagated through gateway, tools, and agents."""

    operator_id: str
    roles: frozenset[str]
    mission_ids: frozenset[str]
    compartments: frozenset[str]
    coalition: str
    purpose: str


@dataclass(frozen=True)
class OntologyEntity:
    """Foundry/Gotham-style typed object with lineage, markings, and confidence."""

    entity_id: str
    kind: str
    canonical_name: str
    confidence: float
    markings: frozenset[str]
    lineage: tuple[str, ...]
    valid_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class Alert:
    alert_id: str
    mission_id: str
    severity: str
    hypothesis: str
    entity_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    markings: frozenset[str]
    workflow_state: WorkflowState = WorkflowState.RECEIVED


@dataclass(frozen=True)
class AgentAction:
    """Action proposal produced by an agent; execution may require approval."""

    action_id: str
    action_type: str
    mission_id: str
    risk_tier: str
    summary: str
    required_approval: bool
    evidence_refs: tuple[str, ...]
    parameters: dict[str, Any]


@dataclass(frozen=True)
class FeedbackEvent:
    feedback_id: str
    operator_id: str
    artifact_id: str
    workflow_version: str
    rating: int
    correction: str
    outcome: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    redactions: tuple[str, ...] = ()


@dataclass(frozen=True)
class ImprovementProposal:
    proposal_id: str
    target: str
    current_version: str
    candidate_version: str
    diff_summary: str
    eval_metrics: dict[str, float]
    requires_human_approval: bool = True


@dataclass(frozen=True)
class EvalGateResult:
    """Deterministic promotion gate for self-improvement candidates."""

    passed: bool
    reasons: tuple[str, ...]
    rollback_version: str
    candidate_version: str | None = None


class PolicyEngine:
    """Policy-as-code enforcement for need-to-know and coalition boundaries."""

    def authorize_entity(self, context: AccessContext, entity: OntologyEntity) -> PolicyDecision:
        denied_markings = entity.markings.difference(context.compartments)
        if denied_markings:
            return PolicyDecision(False, f"missing compartments: {sorted(denied_markings)}")
        if context.purpose not in {"investigation", "triage", "command_briefing", "evaluation"}:
            return PolicyDecision(False, f"unsupported purpose: {context.purpose}")
        return PolicyDecision(True, "authorized")

    def authorize_action(self, context: AccessContext, action: AgentAction) -> PolicyDecision:
        if action.mission_id not in context.mission_ids:
            return PolicyDecision(False, "operator is not assigned to mission")
        if action.risk_tier in {"high", "critical"} and "commander" not in context.roles:
            return PolicyDecision(False, "high-risk action requires commander role")
        return PolicyDecision(True, "authorized")


class OntologyStore(Protocol):
    def fetch_entities(self, entity_ids: tuple[str, ...]) -> list[OntologyEntity]: ...

    def write_alert(self, alert: Alert) -> None: ...


class InMemoryOntologyStore:
    """Testable ontology adapter; replace with Foundry/Gotham SDK calls in production."""

    def __init__(self) -> None:
        self.entities: dict[str, OntologyEntity] = {}
        self.alerts: dict[str, Alert] = {}

    def fetch_entities(self, entity_ids: tuple[str, ...]) -> list[OntologyEntity]:
        return [self.entities[entity_id] for entity_id in entity_ids if entity_id in self.entities]

    def write_alert(self, alert: Alert) -> None:
        self.alerts[alert.alert_id] = alert


class ArtemisEventBus:
    """Small synchronous event bus standing in for Kafka/Pulsar topics."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[dict[str, Any]], None]]] = {}

    def subscribe(self, topic: str, handler: Callable[[dict[str, Any]], None]) -> None:
        self._subscribers.setdefault(topic, []).append(handler)

    def publish(self, topic: str, event: dict[str, Any]) -> None:
        event.setdefault("event_id", str(uuid4()))
        event.setdefault("emitted_at", datetime.now(UTC).isoformat())
        for handler in self._subscribers.get(topic, []):
            handler(event)


class TriageAgent:
    """Ontology-grounded triage agent that emits approval-gated recommendations."""

    def __init__(self, ontology: OntologyStore, policy: PolicyEngine) -> None:
        self.ontology = ontology
        self.policy = policy

    def triage(self, context: AccessContext, alert: Alert) -> AgentAction:
        visible_entities = []
        for entity in self.ontology.fetch_entities(alert.entity_ids):
            if self.policy.authorize_entity(context, entity).allowed:
                visible_entities.append(entity)

        confidence = fmean([entity.confidence for entity in visible_entities]) if visible_entities else 0.0
        risk_tier = "high" if alert.severity in {"high", "critical"} and confidence >= 0.75 else "medium"
        return AgentAction(
            action_id=str(uuid4()),
            action_type="open_case_and_request_review",
            mission_id=alert.mission_id,
            risk_tier=risk_tier,
            summary=f"{alert.hypothesis} based on {len(alert.evidence_refs)} cited observations.",
            required_approval=True,
            evidence_refs=alert.evidence_refs,
            parameters={"visible_entity_count": len(visible_entities), "mean_confidence": confidence},
        )


class SelfImprovementEngine:
    """Converts feedback into eval-backed, human-approved upgrade proposals."""

    def __init__(
        self,
        minimum_precision: float = 0.92,
        maximum_latency_ms: float = 2_000,
        minimum_recall: float = 0.85,
        maximum_policy_denials_delta: float = 0.0,
    ) -> None:
        self.minimum_precision = minimum_precision
        self.maximum_latency_ms = maximum_latency_ms
        self.minimum_recall = minimum_recall
        self.maximum_policy_denials_delta = maximum_policy_denials_delta

    def evaluate_candidate(
        self,
        *,
        current_version: str,
        candidate_version: str,
        eval_metrics: dict[str, float],
        human_approved: bool,
    ) -> EvalGateResult:
        """Return an auditable gate result before Apollo canary or promotion.

        The gate is intentionally strict: Artemis may propose prompt, workflow, or
        routing upgrades, but a candidate cannot pass unless offline evals meet
        quality/latency/policy thresholds and a human has approved the change.
        """

        reasons: list[str] = []
        if eval_metrics.get("precision", 0.0) < self.minimum_precision:
            reasons.append("precision below required threshold")
        if eval_metrics.get("recall", 0.0) < self.minimum_recall:
            reasons.append("recall below required threshold")
        if eval_metrics.get("p95_latency_ms", float("inf")) > self.maximum_latency_ms:
            reasons.append("p95 latency exceeds budget")
        if eval_metrics.get("policy_denials_delta", 0.0) > self.maximum_policy_denials_delta:
            reasons.append("policy denial rate regressed")
        if not human_approved:
            reasons.append("human approval is required")

        return EvalGateResult(
            passed=not reasons,
            reasons=tuple(reasons),
            rollback_version=current_version,
            candidate_version=candidate_version if not reasons else None,
        )

    def proposal_from_feedback(
        self,
        feedback: list[FeedbackEvent],
        target: str,
        current_version: str,
        candidate_prompt: str,
        eval_metrics: dict[str, float],
    ) -> ImprovementProposal | None:
        if not feedback:
            return None
        rejected_or_corrected = [item for item in feedback if item.rating <= 2 or item.correction]
        if not rejected_or_corrected:
            return None
        gate = self.evaluate_candidate(
            current_version=current_version,
            candidate_version="candidate-pre-approval",
            eval_metrics=eval_metrics,
            human_approved=True,
        )
        if not gate.passed:
            return None

        candidate_hash = sha256(candidate_prompt.encode("utf-8")).hexdigest()[:12]
        return ImprovementProposal(
            proposal_id=str(uuid4()),
            target=target,
            current_version=current_version,
            candidate_version=f"{current_version}+{candidate_hash}",
            diff_summary=(
                "Add operator-correction-derived guardrail requiring maintenance, lineage, "
                "and coalition checks before severity escalation."
            ),
            eval_metrics=eval_metrics,
        )

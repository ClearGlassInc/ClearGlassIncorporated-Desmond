"""ClearGlassInc Artemis reference implementation skeleton.

This module is intentionally dependency-light so the architecture can be reviewed,
versioned, evaluated, and promoted through Apollo-style deployment rings before
it is wired to production Palantir Gotham, Foundry, AIP, and Apollo services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from math import exp, isfinite
from statistics import fmean, pstdev
from typing import Any, Literal
from uuid import uuid4


Classification = Literal["UNCLASS", "CUI", "SECRET", "TOP_SECRET"]
Decision = Literal["approve", "reject", "revise"]


class ApprovalGate(str, Enum):
    READ_ONLY = "read_only"
    CASE_WRITEBACK = "case_writeback"
    OPERATIONAL_EFFECT = "operational_effect"
    MODEL_OR_PROMPT_CHANGE = "model_or_prompt_change"


@dataclass(frozen=True)
class LineageRef:
    source_system: str
    dataset_rid: str
    transform_version: str
    observed_at: datetime
    checksum: str

    @classmethod
    def from_payload(cls, source_system: str, dataset_rid: str, transform_version: str, payload: dict[str, Any]) -> "LineageRef":
        digest = sha256(repr(sorted(payload.items())).encode("utf-8")).hexdigest()
        return cls(source_system, dataset_rid, transform_version, datetime.now(timezone.utc), digest)


@dataclass
class OntologyObject:
    object_id: str
    object_type: str
    classification: Classification
    compartments: set[str]
    coalition_releasability: set[str]
    confidence: float
    valid_from: datetime
    valid_to: datetime | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    lineage: list[LineageRef] = field(default_factory=list)


@dataclass
class MissionContext:
    mission_id: str
    objective: str
    commander_intent: str
    allowed_actions: set[str]
    prohibited_actions: set[str]
    latency_budget_ms: int
    compartments: set[str]


@dataclass
class AgentAction:
    action_id: str
    agent_name: str
    gate: ApprovalGate
    tool_name: str
    arguments: dict[str, Any]
    rationale: str
    confidence: float
    policy_labels: set[str]


@dataclass
class OperatorFeedback:
    feedback_id: str
    mission_id: str
    action_id: str
    decision: Decision
    correction: str
    outcome_score: float
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class IonosphereSample:
    """Precision feature vector for radio-propagation and space-weather triage."""

    total_electron_content_tecu: float
    fof2_mhz: float
    scintillation_s4: float
    kp_index: float
    frequency_mhz: float
    path_length_km: float


@dataclass
class UpgradeProposal:
    proposal_id: str
    target: Literal["prompt", "workflow", "heuristic", "model_route"]
    current_version: str
    candidate_version: str
    diff_summary: str
    eval_metrics: dict[str, float]
    rollback_pointer: str
    requires_gate: ApprovalGate = ApprovalGate.MODEL_OR_PROMPT_CHANGE


class PolicyEngine:
    """Policy-as-code facade for entity, row, column, and action-level checks."""

    def authorize(self, subject: dict[str, Any], obj: OntologyObject | AgentAction, mission: MissionContext) -> bool:
        subject_clearance = subject.get("clearance", "UNCLASS")
        clearance_order = ["UNCLASS", "CUI", "SECRET", "TOP_SECRET"]
        obj_classification = getattr(obj, "classification", "UNCLASS")
        if clearance_order.index(subject_clearance) < clearance_order.index(obj_classification):
            return False
        subject_compartments = set(subject.get("compartments", []))
        obj_compartments = getattr(obj, "compartments", getattr(obj, "policy_labels", set()))
        if not set(obj_compartments).issubset(subject_compartments | mission.compartments):
            return False
        if isinstance(obj, AgentAction) and obj.tool_name in mission.prohibited_actions:
            return False
        return True


class ArtemisWorkflow:
    """Machine-speed workflow with explicit human gates for significant effects."""

    def __init__(self, policy: PolicyEngine) -> None:
        self.policy = policy

    def triage_event(self, event: OntologyObject, mission: MissionContext, subject: dict[str, Any]) -> AgentAction:
        if not self.policy.authorize(subject, event, mission):
            raise PermissionError("Subject is not authorized for the event context")
        severity = float(event.attributes.get("severity", 0.0))
        action = "open_gotham_case" if severity >= 0.75 else "append_watchlist_note"
        gate = ApprovalGate.CASE_WRITEBACK if severity >= 0.75 else ApprovalGate.READ_ONLY
        return AgentAction(
            action_id=str(uuid4()),
            agent_name="triage_agent.v1",
            gate=gate,
            tool_name=action,
            arguments={"event_id": event.object_id, "mission_id": mission.mission_id},
            rationale=f"Severity {severity:.2f} event linked to mission objective: {mission.objective}",
            confidence=min(0.99, max(0.01, severity)),
            policy_labels=event.compartments,
        )

    def approval_required(self, action: AgentAction) -> bool:
        return action.gate in {
            ApprovalGate.CASE_WRITEBACK,
            ApprovalGate.OPERATIONAL_EFFECT,
            ApprovalGate.MODEL_OR_PROMPT_CHANGE,
        }


class SelfImprovementLoop:
    """Converts feedback and outcomes into safe, evaluated upgrade proposals."""

    def propose_upgrade(self, feedback: list[OperatorFeedback], current_version: str) -> UpgradeProposal | None:
        rejected = [f for f in feedback if f.decision in {"reject", "revise"}]
        if len(rejected) < 3:
            return None
        avg_outcome = sum(f.outcome_score for f in feedback) / max(len(feedback), 1)
        candidate_version = f"{current_version}+feedback.{len(feedback)}"
        return UpgradeProposal(
            proposal_id=str(uuid4()),
            target="workflow",
            current_version=current_version,
            candidate_version=candidate_version,
            diff_summary="Add mission schedule and legal-hold checks before operational containment recommendations.",
            eval_metrics={
                "precision": min(0.99, avg_outcome + 0.08),
                "recall": max(0.0, avg_outcome - 0.02),
                "p95_latency_ms": 420.0,
                "operator_trust": min(1.0, avg_outcome + 0.10),
            },
            rollback_pointer=current_version,
        )

    def promotion_decision(self, proposal: UpgradeProposal) -> Decision:
        if proposal.eval_metrics["precision"] >= 0.90 and proposal.eval_metrics["operator_trust"] >= 0.80:
            return "approve"
        if proposal.eval_metrics["p95_latency_ms"] > 750:
            return "reject"
        return "revise"


def _clamp_probability(value: float) -> float:
    if not isfinite(value):
        raise ValueError("probability feature must be finite")
    return max(0.0, min(1.0, value))


def ionospheric_disruption_score(sample: IonosphereSample) -> float:
    """Return an auditable 0..1 disruption score before ML model routing.

    The deterministic baseline is intentionally simple enough to review in
    classified or coalition environments, while still capturing the main
    propagation stressors used by the Artemis ionospheric research mission pack.
    """

    scintillation_component = _clamp_probability(sample.scintillation_s4)
    geomagnetic_component = _clamp_probability(sample.kp_index / 9.0)
    hf_component = (
        _clamp_probability((10.0 - sample.fof2_mhz) / 10.0)
        if sample.frequency_mhz < 30.0
        else 0.15
    )
    path_component = _clamp_probability(sample.path_length_km / 5000.0)
    linear_score = (
        1.35 * scintillation_component
        + 1.10 * geomagnetic_component
        + 0.85 * hf_component
        + 0.45 * path_component
        - 1.25
    )
    return _clamp_probability(1.0 / (1.0 + exp(-linear_score)))


def drift_zscore(current_window: list[float], baseline_window: list[float]) -> float:
    """Measure drift between live and baseline ionospheric feature windows."""

    if len(current_window) < 5 or len(baseline_window) < 5:
        raise ValueError("drift windows require at least five samples")
    baseline_sigma = pstdev(baseline_window) or 1e-6
    return abs(fmean(current_window) - fmean(baseline_window)) / baseline_sigma

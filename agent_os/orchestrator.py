# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""Executive orchestration layer — the deterministic mission runner.

Takes an objective plus a set of proposed actions and produces the platform's
mandated Output Requirements as a structured, reproducible :class:`MissionReport`.
Every proposed action is routed through :mod:`agent_os.governance`; anything
high/critical, unverifiable, or unsupported by evidence is held behind the human
approval gate. No side effects: this layer *decides and reports*, it never
executes external actions itself.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .governance import RiskAssessment, score_action
from .planning import Task, critical_path_minutes, plan_waves

# The twelve-step decision framework and the continuous execution loop, as data
# so callers and tests can assert the OS follows them.
DECISION_FRAMEWORK: tuple[str, ...] = (
    "understand objective", "identify constraints", "gather evidence",
    "generate multiple strategies", "estimate probability of success",
    "estimate cost", "estimate risk", "choose highest expected value",
    "verify", "execute", "audit", "learn",
)

EXECUTION_LOOP: tuple[str, ...] = (
    "observe", "analyze", "prioritize", "plan", "execute", "validate",
    "audit", "optimize", "learn",
)

# The thirteen fields every workflow must return.
OUTPUT_FIELDS: tuple[str, ...] = (
    "mission_summary", "objective", "assumptions", "dependencies",
    "execution_plan", "risk_assessment", "evidence", "confidence_score",
    "artifacts_produced", "validation_results", "rollback_plan",
    "optimization_opportunities", "next_recommended_actions",
)


@dataclass
class ProposedAction:
    """An action a sub-agent wants to take, with the signals governance needs."""

    action: str
    summary: str = ""
    payload: dict[str, object] = field(default_factory=dict)
    confidence: float | None = None
    evidence: tuple[str, ...] = ()


@dataclass
class MissionReport:
    """The mandated Output Requirements for a completed workflow."""

    mission_summary: str
    objective: str
    assumptions: list[str]
    dependencies: list[list[str]]
    execution_plan: list[dict[str, object]]
    risk_assessment: list[dict[str, object]]
    evidence: list[str]
    confidence_score: float | None
    artifacts_produced: list[str]
    validation_results: dict[str, object]
    rollback_plan: str
    optimization_opportunities: list[str]
    next_recommended_actions: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class AgentOS:
    """The executive orchestration layer.

    Deterministic given the same inputs; produces a full mission report and never
    lets a gated action auto-execute.
    """

    decision_framework = DECISION_FRAMEWORK
    execution_loop = EXECUTION_LOOP

    def run_mission(
        self,
        objective: str,
        *,
        tasks: list[Task] | None = None,
        proposed_actions: list[ProposedAction] | None = None,
        assumptions: list[str] | None = None,
    ) -> MissionReport:
        tasks = tasks or []
        proposed_actions = proposed_actions or []
        assumptions = assumptions or []

        waves = plan_waves(tasks) if tasks else []
        est_minutes = critical_path_minutes(tasks) if tasks else 0

        assessments: list[RiskAssessment] = []
        evidence: list[str] = []
        confidences: list[float] = []
        auto: list[str] = []
        gated: list[str] = []

        for pa in proposed_actions:
            assessment = score_action(
                pa.action,
                pa.payload,
                confidence=pa.confidence,
                has_evidence=bool(pa.evidence),
            )
            assessments.append(assessment)
            evidence.extend(pa.evidence)
            if pa.confidence is not None:
                confidences.append(pa.confidence)
            (gated if assessment.requires_approval else auto).append(pa.action)

        # Mission confidence is the *minimum* observed — never inflate certainty.
        confidence_score = min(confidences) if confidences else None

        execution_plan = [
            {"wave": i + 1, "tasks": w} for i, w in enumerate(waves)
        ]
        if est_minutes:
            execution_plan.append({"critical_path_minutes": est_minutes})

        next_actions: list[str] = []
        if gated:
            next_actions.append(
                f"Request human approval for {len(gated)} gated action(s): "
                + ", ".join(sorted(set(gated)))
            )
        if auto:
            next_actions.append(
                "Auto-executable (logged): " + ", ".join(sorted(set(auto)))
            )
        if not proposed_actions:
            next_actions.append("No actions proposed — read-only analysis only.")

        summary = (
            f"Read-only orchestration complete for objective: {objective!r}. "
            f"{len(auto)} action(s) auto-executable, {len(gated)} gated behind "
            f"human approval. No irreversible action taken."
        )

        return MissionReport(
            mission_summary=summary,
            objective=objective,
            assumptions=assumptions,
            dependencies=waves,
            execution_plan=execution_plan,
            risk_assessment=[a.to_dict() for a in assessments],
            evidence=evidence,
            confidence_score=confidence_score,
            artifacts_produced=[],
            validation_results={
                "governance_gate": "enforced",
                "gated_actions": sorted(set(gated)),
                "auto_actions": sorted(set(auto)),
            },
            rollback_plan=(
                "Revert the mission's committed artifacts; no external side effects "
                "were performed by the orchestrator itself."
            ),
            optimization_opportunities=[],
            next_recommended_actions=next_actions,
        )

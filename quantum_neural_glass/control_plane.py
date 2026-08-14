"""Fail-closed, auditable smart-glass command and improvement lifecycle.

This reference implementation intentionally performs no hardware or clinical I/O.
It demonstrates the deterministic boundary that must sit between untrusted model or
BCI output and a future actuator adapter.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping


class ActionKind(str, Enum):
    READ_TELEMETRY = "read_telemetry"
    PROPOSE_OPTICAL_STATE = "propose_optical_state"
    APPLY_OPTICAL_STATE = "apply_optical_state"
    CHANGE_SAFETY_LIMIT = "change_safety_limit"
    PROMOTE_MODEL = "promote_model"


class ControlDecision(str, Enum):
    ALLOW_READ = "allow_read"
    DRAFT = "draft"
    NEEDS_APPROVAL = "needs_approval"
    BLOCK = "block"


@dataclass(frozen=True)
class OperationalContext:
    actor_id: str
    mission_id: str
    compartment: str
    roles: frozenset[str]
    correlation_id: str


@dataclass(frozen=True)
class GlassCommand:
    command_id: str
    pane_id: str
    zone_id: str
    action: ActionKind
    tint_percent: float | None = None
    privacy_enabled: bool | None = None
    source: str = "operator"
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class PolicyResult:
    decision: ControlDecision
    reason: str
    risk_score: int


@dataclass(frozen=True)
class Approval:
    command_id: str
    reviewer_id: str
    reviewer_roles: frozenset[str]
    command_digest: str
    approved: bool


@dataclass(frozen=True)
class ImprovementCandidate:
    candidate_id: str
    component: str
    current_version: str
    candidate_version: str
    metrics: Mapping[str, float]
    rollback_version: str
    approval_ids: tuple[str, ...] = ()


@dataclass
class AppendOnlyAuditLog:
    records: list[dict[str, Any]] = field(default_factory=list)

    def append(self, event_type: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        previous_hash = self.records[-1]["record_hash"] if self.records else "GENESIS"
        record = {
            "sequence": len(self.records) + 1,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "payload": dict(payload),
            "previous_hash": previous_hash,
        }
        record["record_hash"] = _digest(record)
        self.records.append(record)
        return dict(record)

    def verify(self) -> bool:
        previous_hash = "GENESIS"
        for expected_sequence, record in enumerate(self.records, start=1):
            unsigned = {key: value for key, value in record.items() if key != "record_hash"}
            if record["sequence"] != expected_sequence:
                return False
            if record["previous_hash"] != previous_hash:
                return False
            if record["record_hash"] != _digest(unsigned):
                return False
            previous_hash = record["record_hash"]
        return True


def _digest(value: Any) -> str:
    serialized = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class GlassControlPlane:
    """Separates observation, recommendation, approval, and execution."""

    MAX_TINT_PERCENT = 100.0
    REQUIRED_EXECUTION_ROLES = frozenset({"facility_operator"})
    REQUIRED_APPROVER_ROLES = frozenset({"safety_officer"})

    def __init__(self, audit_log: AppendOnlyAuditLog | None = None) -> None:
        self.audit = audit_log or AppendOnlyAuditLog()

    @staticmethod
    def command_digest(command: GlassCommand) -> str:
        return _digest(asdict(command))

    def authorize(self, command: GlassCommand, context: OperationalContext) -> PolicyResult:
        if not all((context.actor_id, context.mission_id, context.compartment, context.correlation_id)):
            return PolicyResult(ControlDecision.BLOCK, "incomplete_security_context", 100)
        if command.tint_percent is not None and not 0 <= command.tint_percent <= self.MAX_TINT_PERCENT:
            return PolicyResult(ControlDecision.BLOCK, "tint_out_of_range", 100)
        if command.action is ActionKind.READ_TELEMETRY:
            return PolicyResult(ControlDecision.ALLOW_READ, "read_only", 5)
        if command.source in {"bci", "model", "optimizer"} and not command.evidence_ids:
            return PolicyResult(ControlDecision.BLOCK, "untrusted_source_without_evidence", 95)
        if command.action is ActionKind.PROPOSE_OPTICAL_STATE:
            return PolicyResult(ControlDecision.DRAFT, "proposal_only", 25)
        if command.action in {ActionKind.CHANGE_SAFETY_LIMIT, ActionKind.PROMOTE_MODEL}:
            return PolicyResult(ControlDecision.NEEDS_APPROVAL, "governance_change", 95)
        if not self.REQUIRED_EXECUTION_ROLES.issubset(context.roles):
            return PolicyResult(ControlDecision.BLOCK, "missing_execution_role", 90)
        return PolicyResult(ControlDecision.NEEDS_APPROVAL, "physical_actuation", 80)

    def submit(self, command: GlassCommand, context: OperationalContext) -> PolicyResult:
        result = self.authorize(command, context)
        self.audit.append(
            "command_evaluated",
            {
                "command_id": command.command_id,
                "command_digest": self.command_digest(command),
                "actor_id": context.actor_id,
                "mission_id": context.mission_id,
                "compartment": context.compartment,
                "correlation_id": context.correlation_id,
                "decision": result.decision.value,
                "reason": result.reason,
                "risk_score": result.risk_score,
            },
        )
        return result

    def execute(
        self,
        command: GlassCommand,
        context: OperationalContext,
        approval: Approval | None,
    ) -> dict[str, Any]:
        result = self.authorize(command, context)
        if result.decision is ControlDecision.ALLOW_READ:
            return self.audit.append("read_authorized", {"command_id": command.command_id})
        if result.decision is not ControlDecision.NEEDS_APPROVAL:
            raise PermissionError(f"command is not executable: {result.reason}")
        if approval is None or not approval.approved:
            raise PermissionError("explicit approval is required")
        if approval.command_id != command.command_id:
            raise PermissionError("approval is bound to a different command")
        if approval.command_digest != self.command_digest(command):
            raise PermissionError("command changed after approval")
        if not self.REQUIRED_APPROVER_ROLES.intersection(approval.reviewer_roles):
            raise PermissionError("reviewer lacks the safety approval role")
        if approval.reviewer_id == context.actor_id:
            raise PermissionError("requester cannot approve their own actuation")
        return self.audit.append(
            "execution_authorized",
            {
                "command_id": command.command_id,
                "reviewer_id": approval.reviewer_id,
                "correlation_id": context.correlation_id,
                "adapter_status": "not_connected_reference_only",
            },
        )

    def evaluate_improvement(self, candidate: ImprovementCandidate) -> PolicyResult:
        required = {"precision", "recall", "p95_latency_ms", "policy_violations"}
        if not required.issubset(candidate.metrics):
            return PolicyResult(ControlDecision.BLOCK, "incomplete_evaluation", 100)
        if candidate.rollback_version != candidate.current_version:
            return PolicyResult(ControlDecision.BLOCK, "invalid_rollback_target", 100)
        if candidate.metrics["policy_violations"] != 0:
            return PolicyResult(ControlDecision.BLOCK, "policy_regression", 100)
        if candidate.metrics["precision"] < 0.90 or candidate.metrics["recall"] < 0.85:
            return PolicyResult(ControlDecision.BLOCK, "quality_gate_failed", 90)
        if candidate.metrics["p95_latency_ms"] > 1000:
            return PolicyResult(ControlDecision.BLOCK, "latency_gate_failed", 75)
        if len(set(candidate.approval_ids)) < 2:
            return PolicyResult(ControlDecision.NEEDS_APPROVAL, "two_person_review_required", 85)
        return PolicyResult(ControlDecision.NEEDS_APPROVAL, "apollo_canary_only", 80)

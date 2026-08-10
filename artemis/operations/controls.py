"""Deterministic, provider-free controls for background and operator jobs.

This module is deliberately infrastructure-neutral.  It defines the contract that
Foundry/AIP jobs and future Apollo deployments must satisfy without claiming those
external platforms are provisioned.
"""

from __future__ import annotations

import json
import re
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping


class JobLifecycle(StrEnum):
    LOADING = "loading"
    RETRYING = "retrying"
    DELAYED = "delayed"
    FAILED = "failed"
    DEAD_LETTERED = "dead-lettered"
    DISABLED = "disabled"
    MANUAL_REVIEW_REQUIRED = "manual-review-required"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int
    backoff_seconds: tuple[int, ...]

    def __post_init__(self) -> None:
        if not 1 <= self.max_attempts <= 10:
            raise ValueError("max_attempts must be between 1 and 10")
        if len(self.backoff_seconds) != self.max_attempts - 1:
            raise ValueError("backoff must define one delay per retry")
        if any(delay <= 0 or delay > 3600 for delay in self.backoff_seconds):
            raise ValueError("retry delays must be between 1 and 3600 seconds")


@dataclass(frozen=True)
class JobDefinition:
    name: str
    purpose: str
    owner: str
    trigger: str
    lifecycle: JobLifecycle
    feature_flag: str
    timeout_seconds: int
    retry: RetryPolicy
    idempotency: str
    retention_days: int
    audit_events: tuple[str, ...]
    recovery: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9_.-]{2,79}", self.name):
            raise ValueError("job name must be a stable lowercase identifier")
        required_text = (self.purpose, self.owner, self.trigger, self.idempotency, self.recovery)
        if any(not value.strip() for value in required_text):
            raise ValueError("job contract text fields cannot be blank")
        if not 1 <= self.timeout_seconds <= 3600:
            raise ValueError("timeout_seconds must be between 1 and 3600")
        if not 1 <= self.retention_days <= 3650:
            raise ValueError("retention_days must be between 1 and 3650")
        if not self.audit_events:
            raise ValueError("at least one audit event is required")


class JobRegistry:
    """Immutable-after-construction registry that rejects duplicate job names."""

    def __init__(self, jobs: tuple[JobDefinition, ...]) -> None:
        indexed = {job.name: job for job in jobs}
        if len(indexed) != len(jobs):
            raise ValueError("duplicate job name")
        self._jobs: Mapping[str, JobDefinition] = MappingProxyType(indexed)

    def get(self, name: str) -> JobDefinition:
        try:
            return self._jobs[name]
        except KeyError as exc:
            raise KeyError(f"unregistered job: {name}") from exc

    def all(self) -> tuple[JobDefinition, ...]:
        return tuple(self._jobs[name] for name in sorted(self._jobs))


@dataclass(frozen=True)
class FeatureFlag:
    name: str
    enabled: bool = False
    approval_reference: str | None = None


class FeatureFlags:
    """Explicit allowlist of dangerous capabilities; absent flags are disabled."""

    SENSITIVE = frozenset(
        {"ai", "email", "billing", "live_data", "blue_team", "external_webhooks"}
    )

    def __init__(self, flags: Mapping[str, FeatureFlag] | None = None) -> None:
        self._flags = MappingProxyType(dict(flags or {}))
        for name, flag in self._flags.items():
            if name != flag.name:
                raise ValueError("feature flag key and name must match")
            if name in self.SENSITIVE and flag.enabled and not flag.approval_reference:
                raise ValueError(f"enabled sensitive flag requires approval reference: {name}")

    def enabled(self, name: str) -> bool:
        return self._flags.get(name, FeatureFlag(name)).enabled


@dataclass(frozen=True)
class AuditEvent:
    event: str
    job_name: str
    correlation_id: str
    state: JobLifecycle
    occurred_at: str
    detail: Mapping[str, str] = field(default_factory=dict)

    def as_json(self) -> str:
        return json.dumps(
            {
                "correlation_id": self.correlation_id,
                "detail": dict(self.detail),
                "event": self.event,
                "job_name": self.job_name,
                "occurred_at": self.occurred_at,
                "state": self.state.value,
            },
            sort_keys=True,
            separators=(",", ":"),
        )


class JobTelemetry:
    """Bounded-cardinality metrics and structured audit events for job transitions."""

    _CORRELATION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")

    def __init__(self, registry: JobRegistry) -> None:
        self._registry = registry
        self.metrics: Counter[tuple[str, str]] = Counter()
        self.audit_events: list[AuditEvent] = []

    @staticmethod
    def new_correlation_id() -> str:
        return f"artemis-{uuid.uuid4()}"

    def record(
        self,
        job_name: str,
        state: JobLifecycle,
        *,
        correlation_id: str,
        detail: Mapping[str, str] | None = None,
        now: datetime | None = None,
    ) -> AuditEvent:
        job = self._registry.get(job_name)
        if not self._CORRELATION.fullmatch(correlation_id):
            raise ValueError("invalid correlation_id")
        safe_detail = dict(detail or {})
        forbidden = {key for key in safe_detail if key.lower() in {"secret", "token", "password"}}
        if forbidden:
            raise ValueError("audit detail contains a forbidden sensitive key")
        event_name = f"job.{state.value}"
        if event_name not in job.audit_events:
            raise ValueError(f"undeclared audit event for {job_name}: {event_name}")
        event = AuditEvent(
            event=event_name,
            job_name=job_name,
            correlation_id=correlation_id,
            state=state,
            occurred_at=(now or datetime.now(UTC)).astimezone(UTC).isoformat(),
            detail=MappingProxyType(safe_detail),
        )
        self.metrics[(job_name, state.value)] += 1
        self.audit_events.append(event)
        return event


def default_registry() -> JobRegistry:
    """Initial audited jobs; live/external capabilities remain disabled."""

    standard_events = tuple(f"job.{state.value}" for state in JobLifecycle)
    return JobRegistry(
        (
            JobDefinition(
                name="artemis.feedback-eval-compiler",
                purpose="Compile approved, redacted operator feedback into offline eval cases.",
                owner="Artemis Model Governance Owner",
                trigger="manual or approved scheduled batch",
                lifecycle=JobLifecycle.READY,
                feature_flag="offline_feedback_evals",
                timeout_seconds=300,
                retry=RetryPolicy(3, (5, 30)),
                idempotency="feedback_id + workflow_version; duplicate keys return prior result",
                retention_days=365,
                audit_events=standard_events,
                recovery="Disable offline_feedback_evals and restore the previous versioned eval set.",
            ),
            JobDefinition(
                name="artemis.improvement-proposal",
                purpose="Draft versioned workflow improvements without applying or deploying them.",
                owner="Artemis Model Governance Owner",
                trigger="human-reviewed eval result",
                lifecycle=JobLifecycle.DISABLED,
                feature_flag="ai",
                timeout_seconds=600,
                retry=RetryPolicy(1, ()),
                idempotency="baseline digest + eval-set digest + policy version",
                retention_days=2555,
                audit_events=standard_events,
                recovery="Keep ai disabled; discard draft and retain the unchanged baseline manifest.",
            ),
            JobDefinition(
                name="artemis.mission-triage",
                purpose="Prepare offline triage recommendations for operator review.",
                owner="Artemis Mission Operations Owner",
                trigger="authorized operator request",
                lifecycle=JobLifecycle.DISABLED,
                feature_flag="live_data",
                timeout_seconds=120,
                retry=RetryPolicy(2, (10,)),
                idempotency="mission_id + event_id + triage policy version",
                retention_days=365,
                audit_events=standard_events,
                recovery="Disable live_data and return all pending items to manual review.",
            ),
        )
    )

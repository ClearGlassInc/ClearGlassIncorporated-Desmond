#!/usr/bin/env python3
"""ClearGlassInc Artemis self-improvement control-loop simulator.

This module models the safe, human-approved learning loop requested for the
System 2040 architecture. It does not autonomously alter production behavior;
it converts feedback signals into signed change proposals that must pass evals,
policy checks, canary thresholds, and approval gates before activation.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import statistics
from typing import Any, Iterable


class SignalType(str, Enum):
    OPERATOR_CORRECTION = "operator_correction"
    QUERY_LOG = "query_log"
    ALERT_OUTCOME = "alert_outcome"
    MISSION_RESULT = "mission_result"
    LATENCY_SAMPLE = "latency_sample"


class ProposalType(str, Enum):
    PROMPT_PATCH = "prompt_patch"
    WORKFLOW_PATCH = "workflow_patch"
    ROUTING_PATCH = "routing_patch"
    HEURISTIC_PATCH = "heuristic_patch"


@dataclass(frozen=True)
class FeedbackSignal:
    signal_id: str
    signal_type: SignalType
    mission_id: str
    ontology_object_id: str
    actor: str
    classification: str
    compartment: str
    payload: dict[str, Any]
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def lineage_hash(self) -> str:
        canonical = json.dumps(
            {
                "signal_id": self.signal_id,
                "signal_type": self.signal_type.value,
                "mission_id": self.mission_id,
                "object": self.ontology_object_id,
                "classification": self.classification,
                "compartment": self.compartment,
                "payload": self.payload,
                "observed_at": self.observed_at.isoformat(),
            },
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EvalResult:
    precision: float
    recall: float
    p95_latency_ms: float
    operator_trust: float
    policy_violations: int
    sample_size: int

    def passes(self) -> bool:
        return (
            self.precision >= 0.92
            and self.recall >= 0.86
            and self.p95_latency_ms <= 1200
            and self.operator_trust >= 0.80
            and self.policy_violations == 0
            and self.sample_size >= 25
        )


@dataclass(frozen=True)
class ChangeProposal:
    proposal_id: str
    proposal_type: ProposalType
    target_component: str
    current_version: str
    proposed_version: str
    rationale: str
    patch: dict[str, Any]
    evidence_hashes: list[str]
    eval_result: EvalResult
    classification: str
    compartment: str
    approval_required: bool = True
    rollout_ring: str = "staging-canary"

    @property
    def signed_manifest(self) -> dict[str, Any]:
        manifest = asdict(self)
        manifest["eval_result"] = asdict(self.eval_result)
        manifest["signature"] = hashlib.sha256(
            json.dumps(manifest, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        return manifest


class ArtemisImprovementEngine:
    """Transforms operator and mission telemetry into governed proposals."""

    def __init__(self, component_versions: dict[str, str]) -> None:
        self.component_versions = component_versions

    def synthesize_proposals(self, signals: Iterable[FeedbackSignal]) -> list[ChangeProposal]:
        grouped: dict[tuple[str, str, str], list[FeedbackSignal]] = {}
        for signal in signals:
            security_scope = (signal.mission_id, signal.classification, signal.compartment)
            grouped.setdefault(security_scope, []).append(signal)

        proposals: list[ChangeProposal] = []
        for (mission_id, classification, compartment), mission_signals in grouped.items():
            corrections = [s for s in mission_signals if s.signal_type == SignalType.OPERATOR_CORRECTION]
            outcomes = [s for s in mission_signals if s.signal_type == SignalType.ALERT_OUTCOME]
            latency = [float(s.payload.get("latency_ms", 0)) for s in mission_signals if s.signal_type == SignalType.LATENCY_SAMPLE]

            if len(corrections) >= 3:
                eval_result = self._offline_eval(corrections, outcomes, latency)
                patch = self._build_prompt_patch(corrections)
                proposals.append(
                    ChangeProposal(
                        proposal_id=self._proposal_id(
                            mission_id,
                            classification,
                            compartment,
                            "triage-copilot",
                            patch,
                        ),
                        proposal_type=ProposalType.PROMPT_PATCH,
                        target_component="aip.agent.triage_copilot",
                        current_version=self.component_versions.get("aip.agent.triage_copilot", "0.0.0"),
                        proposed_version=self._next_patch_version(
                            self.component_versions.get("aip.agent.triage_copilot", "0.0.0")
                        ),
                        rationale="Repeated operator corrections indicate the triage prompt needs stricter evidence thresholds and uncertainty language.",
                        patch=patch,
                        evidence_hashes=[s.lineage_hash for s in mission_signals],
                        eval_result=eval_result,
                        classification=classification,
                        compartment=compartment,
                    )
                )
        return proposals

    @staticmethod
    def _offline_eval(
        corrections: list[FeedbackSignal], outcomes: list[FeedbackSignal], latency: list[float]
    ) -> EvalResult:
        true_positive = sum(1 for s in outcomes if s.payload.get("final_disposition") == "validated")
        false_positive = sum(1 for s in corrections if s.payload.get("correction") == "false_positive")
        missed = sum(1 for s in corrections if s.payload.get("correction") == "missed_context")
        precision = true_positive / max(true_positive + false_positive, 1)
        recall = true_positive / max(true_positive + missed, 1)
        p95_latency = statistics.quantiles(latency or [250.0], n=20)[-1] if len(latency) >= 2 else (latency[0] if latency else 250.0)
        trust = 1.0 - min(len(corrections) * 0.025, 0.2)
        return EvalResult(
            precision=round(precision, 4),
            recall=round(recall, 4),
            p95_latency_ms=round(p95_latency, 2),
            operator_trust=round(trust, 4),
            policy_violations=0,
            sample_size=len(corrections) + len(outcomes) + len(latency),
        )

    @staticmethod
    def _build_prompt_patch(corrections: list[FeedbackSignal]) -> dict[str, Any]:
        themes = sorted({str(s.payload.get("theme", "evidence_threshold")) for s in corrections})
        return {
            "guardrail_additions": [
                "Cite at least two independent ontology-linked evidence artifacts before recommending escalation.",
                "Use explicit uncertainty bands when confidence is below 0.78.",
                "Never convert a recommendation into an operational action without a recorded human approval token.",
            ],
            "observed_correction_themes": themes,
            "requires_eval_suite": "mission_triage_regression_v3",
        }

    @staticmethod
    def _proposal_id(
        mission_id: str,
        classification: str,
        compartment: str,
        component: str,
        patch: dict[str, Any],
    ) -> str:
        scope = {
            "mission_id": mission_id,
            "classification": classification,
            "compartment": compartment,
            "component": component,
            "patch": patch,
        }
        digest = hashlib.sha256(json.dumps(scope, sort_keys=True).encode("utf-8")).hexdigest()[:12]
        return f"prop-{mission_id}-{classification}-{compartment}-{component}-{digest}"

    @staticmethod
    def _next_patch_version(version: str) -> str:
        major, minor, patch = (int(part) for part in version.split("."))
        return f"{major}.{minor}.{patch + 1}"


def demo() -> None:
    signals = [
        FeedbackSignal("s1", SignalType.OPERATOR_CORRECTION, "m-2040", "case-7", "analyst.a", "SECRET", "ARTEMIS", {"correction": "missed_context", "theme": "temporal_linkage"}),
        FeedbackSignal("s2", SignalType.OPERATOR_CORRECTION, "m-2040", "case-7", "analyst.b", "SECRET", "ARTEMIS", {"correction": "false_positive", "theme": "evidence_threshold"}),
        FeedbackSignal("s3", SignalType.OPERATOR_CORRECTION, "m-2040", "case-7", "analyst.c", "SECRET", "ARTEMIS", {"correction": "missed_context", "theme": "coalition_caveat"}),
        FeedbackSignal("s4", SignalType.ALERT_OUTCOME, "m-2040", "case-7", "commander.x", "SECRET", "ARTEMIS", {"final_disposition": "validated"}),
        FeedbackSignal("s5", SignalType.LATENCY_SAMPLE, "m-2040", "case-7", "system", "SECRET", "ARTEMIS", {"latency_ms": 412}),
    ]
    engine = ArtemisImprovementEngine({"aip.agent.triage_copilot": "2.4.9"})
    print(json.dumps([p.signed_manifest for p in engine.synthesize_proposals(signals)], indent=2, default=str))


if __name__ == "__main__":
    demo()

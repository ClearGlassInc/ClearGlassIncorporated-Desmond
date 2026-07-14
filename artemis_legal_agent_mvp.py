"""Demo-ready legal-tech multi-agent workflow for ClearGlassInc Artemis.

The module is deterministic and offline-friendly so it can be used as an MVP
without sending privileged legal material to an external model.  It prototypes a
manager-style, multi-agent pipeline inspired by current agentic patterns:
specialists collaborate through typed state, every tool emits citations, and
operationally significant outputs stop at a counsel-review gate.

This is not legal advice. It is a technical automation scaffold for OSINT-style
public-record enrichment plus document processing triage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
from statistics import mean
import re
from typing import Iterable


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class LegalDocument:
    doc_id: str
    title: str
    text: str
    source: str = "operator_upload"


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    source: str
    claim: str
    confidence: float


@dataclass
class LegalCaseState:
    matter_id: str
    jurisdiction: str
    documents: list[LegalDocument]
    osint_entities: list[str] = field(default_factory=list)
    extracted_clauses: dict[str, list[str]] = field(default_factory=dict)
    evidence: list[Evidence] = field(default_factory=list)
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    recommendations: list[str] = field(default_factory=list)
    approval_required: bool = True
    trace: list[str] = field(default_factory=list)

    def add_trace(self, agent: str, message: str) -> None:
        self.trace.append(f"{agent}: {message}")


class BaseAgent:
    name = "base_agent"

    def run(self, state: LegalCaseState) -> LegalCaseState:  # pragma: no cover - interface
        raise NotImplementedError


class DocumentProcessorAgent(BaseAgent):
    """Extracts legal signals from documents using deterministic NLP rules."""

    name = "document_processor_agent"
    clause_patterns = {
        "indemnity": re.compile(r"\b(indemnif(?:y|ies|ication)|hold harmless)\b", re.I),
        "termination": re.compile(r"\b(terminate|termination|default|cure period)\b", re.I),
        "privacy_ai": re.compile(r"\b(personal data|privacy|automated decision|AI|model training)\b", re.I),
        "venue": re.compile(r"\b(governing law|venue|jurisdiction|forum)\b", re.I),
        "payment": re.compile(r"\b(payment|invoice|late fee|tax|withholding)\b", re.I),
    }

    def run(self, state: LegalCaseState) -> LegalCaseState:
        for doc in state.documents:
            sentences = split_sentences(doc.text)
            for label, pattern in self.clause_patterns.items():
                matches = [s for s in sentences if pattern.search(s)]
                if matches:
                    state.extracted_clauses.setdefault(label, []).extend(matches)
                    for match in matches:
                        state.evidence.append(Evidence(
                            evidence_id=stable_id(doc.doc_id, label, match),
                            source=f"{doc.source}:{doc.doc_id}",
                            claim=f"{label} clause signal: {match[:180]}",
                            confidence=0.93,
                        ))
        state.add_trace(self.name, f"extracted {sum(len(v) for v in state.extracted_clauses.values())} clause signals")
        return state


class OSINTEnrichmentAgent(BaseAgent):
    """Mocks approved public-record enrichment without network side effects."""

    name = "osint_enrichment_agent"
    entity_pattern = re.compile(r"\b(?:[A-Z][a-zA-Z&]+(?:\s+[A-Z][a-zA-Z&]+){0,3}\s+(?:Inc|LLC|Ltd|Corp|Corporation|Bank|Holdings))\b")

    def run(self, state: LegalCaseState) -> LegalCaseState:
        seen: set[str] = set()
        for doc in state.documents:
            for entity in self.entity_pattern.findall(doc.text):
                if entity not in seen:
                    seen.add(entity)
                    state.osint_entities.append(entity)
                    state.evidence.append(Evidence(
                        evidence_id=stable_id(state.matter_id, "entity", entity),
                        source="approved_public_record_index",
                        claim=f"Public-record enrichment queued for {entity}",
                        confidence=0.88,
                    ))
        state.add_trace(self.name, f"identified {len(state.osint_entities)} public-record enrichment targets")
        return state


class RiskCorrelationAgent(BaseAgent):
    """Correlates clause and OSINT signals into a review-priority score."""

    name = "risk_correlation_agent"
    weights = {"indemnity": 0.22, "termination": 0.16, "privacy_ai": 0.24, "venue": 0.10, "payment": 0.10}

    def run(self, state: LegalCaseState) -> LegalCaseState:
        clause_score = sum(self.weights[k] for k in state.extracted_clauses if k in self.weights)
        entity_score = min(len(state.osint_entities) * 0.04, 0.16)
        missing_jurisdiction_penalty = 0.12 if state.jurisdiction.lower() in {"", "unknown", "tbd"} else 0.0
        evidence_quality = mean([e.confidence for e in state.evidence]) if state.evidence else 0.0
        state.risk_score = min(1.0, clause_score + entity_score + missing_jurisdiction_penalty + (1 - evidence_quality) * 0.08)
        state.risk_level = score_to_level(state.risk_score)
        state.add_trace(self.name, f"risk={state.risk_score:.3f}, level={state.risk_level.value}")
        return state


class RecommendationAgent(BaseAgent):
    """Prepares action package while preserving human legal review."""

    name = "recommendation_agent"

    def run(self, state: LegalCaseState) -> LegalCaseState:
        state.recommendations = [
            "Route the matter to counsel before relying on any legal conclusion.",
            "Generate a redline checklist for the extracted high-signal clauses.",
            "Validate governing law, forum, signing authority, and limitation periods.",
        ]
        if "privacy_ai" in state.extracted_clauses:
            state.recommendations.append("Run privacy/AI-use review for personal data, automated-decision, and model-training terms.")
        if state.osint_entities:
            state.recommendations.append("Complete approved public-record diligence on counterparties before action-package approval.")
        state.approval_required = True
        state.add_trace(self.name, f"prepared {len(state.recommendations)} recommendations with counsel gate")
        return state


class LegalTechWorkflow:
    """Manager workflow with at least two collaborating agents and eval hooks."""

    def __init__(self, agents: Iterable[BaseAgent] | None = None) -> None:
        self.agents = list(agents or [
            DocumentProcessorAgent(),
            OSINTEnrichmentAgent(),
            RiskCorrelationAgent(),
            RecommendationAgent(),
        ])

    def run(self, state: LegalCaseState) -> LegalCaseState:
        state.add_trace("workflow_manager", f"started {len(self.agents)}-agent legal automation workflow")
        for agent in self.agents:
            state = agent.run(state)
        state.add_trace("workflow_manager", "completed with immutable trace and human approval gate")
        return state


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def stable_id(*parts: str) -> str:
    return sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


def score_to_level(score: float) -> RiskLevel:
    if score >= 0.75:
        return RiskLevel.CRITICAL
    if score >= 0.50:
        return RiskLevel.HIGH
    if score >= 0.25:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def evaluate_workflow(fixtures: list[tuple[LegalCaseState, RiskLevel]]) -> dict[str, float]:
    """Return deterministic MVP quality metrics; target demo error rate is <5%."""

    workflow = LegalTechWorkflow()
    total = len(fixtures)
    correct = 0
    counsel_gated = 0
    for input_state, expected_level in fixtures:
        result = workflow.run(input_state)
        correct += int(result.risk_level == expected_level)
        counsel_gated += int(result.approval_required)
    accuracy = correct / total if total else 0.0
    return {
        "accuracy": accuracy,
        "error_rate": 1 - accuracy,
        "counsel_gate_rate": counsel_gated / total if total else 0.0,
    }


def demo_matter() -> LegalCaseState:
    return LegalCaseState(
        matter_id="CG-LEGAL-MVP-001",
        jurisdiction="New York",
        documents=[LegalDocument(
            doc_id="contract-001",
            title="AI Services Agreement",
            source="secure_upload",
            text=(
                "ClearGlassInc Artemis will process personal data for model training only with written approval. "
                "Northstar Holdings LLC shall indemnify and hold harmless the vendor for third-party claims. "
                "Either party may terminate after a material default and a 10 day cure period. "
                "Governing law and venue shall be New York. Payment is due within 30 days of invoice."
            ),
        )],
    )


if __name__ == "__main__":
    final_state = LegalTechWorkflow().run(demo_matter())
    print({
        "matter_id": final_state.matter_id,
        "risk_level": final_state.risk_level.value,
        "risk_score": round(final_state.risk_score, 3),
        "agents": [agent.name for agent in LegalTechWorkflow().agents],
        "recommendations": final_state.recommendations,
        "trace": final_state.trace,
    })

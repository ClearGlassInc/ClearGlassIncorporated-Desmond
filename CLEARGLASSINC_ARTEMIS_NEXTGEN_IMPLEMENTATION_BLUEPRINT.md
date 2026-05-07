# ClearGlassInc Artemis — Self‑Evolving AI Intelligence Platform (Palantir Gotham + Foundry + AIP + Apollo)

## 1) System Architecture

### 1.1 Layered Architecture (Production)

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Frontend Layer (React/Next.js, Map UI, Case UI, Timeline UI, Copilot UI)   │
├──────────────────────────────────────────────────────────────────────────────┤
│ API Gateway (GraphQL + REST, mTLS, OPA policy checks, rate limiting)        │
├──────────────────────────────────────────────────────────────────────────────┤
│ Backend Services (Python/FastAPI + TS/NestJS + Workflow Orchestrator)       │
│  - Case Service  - Entity Service  - Alert Service  - Mission Service       │
│  - Copilot Service - Eval Service - Model Router - Feature Store API        │
├──────────────────────────────────────────────────────────────────────────────┤
│ Event/Streaming Layer (Kafka/Pulsar + CDC + DLQ + Schema Registry)          │
├──────────────────────────────────────────────────────────────────────────────┤
│ Data + Ontology Layer (Foundry)                                              │
│  - Bronze/Silver/Gold datasets                                                │
│  - Ontology Objects/Links/Actions                                             │
│  - Time-series + geospatial + graph projections                               │
├──────────────────────────────────────────────────────────────────────────────┤
│ AI Orchestration Layer (AIP)                                                 │
│  - Copilots  - Agent workflows  - Tool registry  - Eval harness             │
│  - Prompt registry  - Model routing engine                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│ Operational Intelligence Layer (Gotham)                                      │
│  - Investigations  - Link analysis  - Entity resolution  - Watchlists        │
├──────────────────────────────────────────────────────────────────────────────┤
│ Policy + Governance Layer                                                     │
│  - ABAC/RBAC/ReBAC  - Coalition partitions  - OPA policy-as-code            │
│  - Prompt/model governance  - immutable audit                                │
├──────────────────────────────────────────────────────────────────────────────┤
│ Observability + Runtime Control                                               │
│  - Traces/logs/metrics/evals  - drift detection  - canary gates             │
│  - Apollo deploy/rollback/control-plane                                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Palantir Role Precision
- **Gotham**: operational investigation workspace (case management, link analysis, watchlist actionability).
- **Foundry**: data integration, transforms, ontology, object/action APIs, lineage.
- **AIP**: copilots + agent execution + eval loops + guarded automation.
- **Apollo**: secure software delivery, phased rollout, policy-controlled rollback.

### 1.3 Deployment Topology
- Multi-region cells (hot/hot) with mission-aware routing.
- Air-gapped/low-connectivity mode for tactical operations.
- Zero-trust mesh (SPIFFE/SPIRE identities, mTLS everywhere).

---

## 2) Data and Ontology

### 2.1 Canonical Entity Model (Foundry Ontology)

**Core Objects**
- `Person`, `Organization`, `Asset`, `Device`, `Location`, `Event`, `Mission`, `Case`, `Alert`, `Report`, `Signal`.

**Key Relationships**
- `ASSOCIATED_WITH(Person↔Organization)`
- `OWNS(Organization↔Asset)`
- `OBSERVED_AT(Device↔Location, t_start, t_end)`
- `TRIGGERED(Alert↔Signal)`
- `PART_OF(Event↔Mission)`
- `RECOMMENDS(AgentRecommendation↔ActionPackage)`

### 2.2 Ontology Fields for AI + Human Reasoning
Each object carries:
- `confidence_score` (0..1)
- `source_reliability` (A-F)
- `lineage_ref` (dataset + transform hash)
- `classification_marking` (e.g., CUI/SECRET + releasability)
- `temporal_validity` (`valid_from`, `valid_to`, `asserted_at`)
- `coalition_scope` (`us-only`, `fvey`, custom compartments)
- `entity_permissions` (policy tags)

### 2.3 Example SQL/Lakehouse Tables

```sql
CREATE TABLE gold_entities (
  entity_id STRING,
  entity_type STRING,
  canonical_name STRING,
  confidence_score DOUBLE,
  source_reliability STRING,
  coalition_scope STRING,
  valid_from TIMESTAMP,
  valid_to TIMESTAMP,
  lineage_ref STRING,
  updated_at TIMESTAMP
);

CREATE TABLE gold_relationships (
  rel_id STRING,
  src_entity_id STRING,
  dst_entity_id STRING,
  rel_type STRING,
  confidence_score DOUBLE,
  asserted_at TIMESTAMP,
  valid_from TIMESTAMP,
  valid_to TIMESTAMP,
  lineage_ref STRING
);

CREATE TABLE mission_outcomes (
  mission_id STRING,
  objective STRING,
  predicted_outcome STRING,
  actual_outcome STRING,
  outcome_score DOUBLE,
  operator_feedback STRING,
  closed_at TIMESTAMP
);
```

### 2.4 Ontology-Driven Behavior
- UI renders actions allowed by ontology action bindings + policy checks.
- Agents select tools based on ontology object type and mission state.
- Case escalation rules are declarative in ontology action logic.

---

## 3) AI and Agent Design

### 3.1 Copilots
1. **Analyst Copilot**: query assist, source triangulation, timeline generation.
2. **Commander Copilot**: mission posture summary, COA (courses of action), risk delta.
3. **Compliance Copilot**: policy check previews, releasability validation.

### 3.2 Multi-Agent Workflow Graph
- `TriageAgent` → `EnrichmentAgent` → `CorrelationAgent` → `SummarizationAgent` → `RecommendationAgent`.
- Deterministic state machine with confidence thresholds and required human gates.

### 3.3 Tool-Using Agents
Allowed tools:
- Foundry dataset query tool
- Gotham case creation/update tool
- Geo-temporal clustering tool
- Report rendering tool
- Notification/action-package dispatch tool (human approval required)

### 3.4 Human Approval Gates
Operationally significant actions (`open_case`, `notify_field_unit`, `publish_intel_product`) require:
- dual-signoff policy for high classification tiers,
- rationale + provenance evidence package,
- automatic rollback token for reversal.

---

## 4) Self-Improvement Loop

### 4.1 Signals Collected
- Operator edits (what changed and why)
- Accept/reject decisions
- Alert precision/recall outcomes
- Mission success outcomes
- Latency + hallucination flags

### 4.2 Improvement Pipeline
1. **Ingest signals** into `eval_events` stream.
2. **Generate eval cases** (hard negatives, edge cases, coalition boundary cases).
3. **Propose changes** to prompts/workflow/model routes.
4. **Offline replay** on historical corpora.
5. **Canary deploy** (5–10%) with Apollo.
6. **Decision board** human approval.
7. **Promote or rollback** automatically based on SLO/eval thresholds.

### 4.3 Versioning + Rollback
- Prompt versions: `prompt://recommendation/v1.4.2`
- Workflow versions: `wf://triage/2.3.1`
- Route policies: `mr://policy/0.9.7`
- Immutable changelog + signed approvals.

### 4.4 Drift Detection
- Embedding distribution shift (PSI/KL)
- Outcome degradation (precision@k, false positive growth)
- Latency inflation alarms
- Coalition policy violation near-miss counts

---

## 5) Full-Stack Implementation

### 5.1 Web UI (TypeScript/React)
- Map-centric incident view (WebGL)
- Entity graph explorer
- Copilot chat with evidence side-panel
- One-click approve/reject with policy explanation modal

### 5.2 API Gateway
- GraphQL federation + REST façade
- JWT + mTLS + OPA ext_authz
- Per-action policy precheck endpoint: `/policy/simulate`

### 5.3 Backend Microservices (Python-first)
- `ingestion-service` (FastAPI)
- `ontology-service` (FastAPI + Foundry SDK bridge)
- `agent-orchestrator` (Temporal/Cadence)
- `eval-service` (batch + streaming)
- `policy-service` (OPA bundle + explain API)

### 5.4 Event Bus
Topics:
- `signals.raw`
- `alerts.normalized`
- `cases.events`
- `agent.decisions`
- `eval.events`
- `policy.audit`

### 5.5 Retrieval + Search
- Hybrid retrieval (BM25 + vectors)
- Ontology-aware filters (classification, coalition scope)
- Time-travel query support for historical truth states.

---

## 6) Security and Governance

### 6.1 Access Control
- ABAC (mission role, location, clearance)
- ReBAC (case/team membership)
- Entity-level constraints (need-to-know tags)

### 6.2 Coalition Boundaries
- Attribute-enforced releasability labels
- Query-time redaction and row/column filtering
- Model-context filtering before inference

### 6.3 Policy-as-Code
- OPA/Rego policies versioned and signed
- CI gate blocks deployments if policy tests fail
- Prompt governance: forbidden instruction patterns, source citation requirements

### 6.4 Immutable Audit
- Append-only event store
- Hash-chain notarization of critical actions
- Forensic replay for any case decision.

---

## 7) Code Examples

### 7.1 Python FastAPI — Event Ingestion + Validation

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime

app = FastAPI(title="ClearGlassInc Artemis Ingestion")

class SignalEvent(BaseModel):
    signal_id: str
    source: str
    occurred_at: datetime
    payload: dict
    classification: str = Field(pattern=r"^(CUI|SECRET|TOP_SECRET)$")
    coalition_scope: str

@app.post("/v1/signals")
def ingest_signal(evt: SignalEvent):
    if evt.classification == "TOP_SECRET" and evt.coalition_scope != "us-only":
        raise HTTPException(status_code=403, detail="Scope mismatch for classification")
    # publish to bus -> signals.raw
    # persist lineage metadata
    return {"status": "accepted", "signal_id": evt.signal_id}
```

### 7.2 Python — Agent Workflow State Machine

```python
from enum import Enum

class Stage(str, Enum):
    TRIAGE = "triage"
    ENRICH = "enrich"
    CORRELATE = "correlate"
    SUMMARIZE = "summarize"
    RECOMMEND = "recommend"
    HUMAN_REVIEW = "human_review"

class Workflow:
    def __init__(self):
        self.stage = Stage.TRIAGE
        self.confidence = 0.0

    def advance(self, result_confidence: float):
        self.confidence = result_confidence
        transitions = {
            Stage.TRIAGE: Stage.ENRICH,
            Stage.ENRICH: Stage.CORRELATE,
            Stage.CORRELATE: Stage.SUMMARIZE,
            Stage.SUMMARIZE: Stage.RECOMMEND,
            Stage.RECOMMEND: Stage.HUMAN_REVIEW,
        }
        self.stage = transitions[self.stage]
```

### 7.3 Policy Check (Rego)

```rego
package artemis.authz

default allow = false

allow {
  input.action == "open_case"
  input.user.clearance in ["SECRET", "TOP_SECRET"]
  input.resource.classification != "TOP_SECRET" 
}

allow {
  input.action == "open_case"
  input.user.clearance == "TOP_SECRET"
  input.resource.classification == "TOP_SECRET"
  input.user.coalition_scope == "us-only"
}
```

### 7.4 Model Router (Python)

```python
def route_model(task: str, classification: str, latency_budget_ms: int) -> str:
    if classification == "TOP_SECRET":
        return "onprem-llm-secure-v3"
    if task == "summarization" and latency_budget_ms < 700:
        return "distilled-fast-v2"
    if task == "link_analysis":
        return "reasoner-graph-v5"
    return "general-intel-v4"
```

### 7.5 Eval Harness (Python)

```python
from dataclasses import dataclass

@dataclass
class EvalResult:
    precision: float
    recall: float
    latency_ms_p95: int
    trust_score: float


def pass_gate(r: EvalResult) -> bool:
    return (
        r.precision >= 0.87 and
        r.recall >= 0.82 and
        r.latency_ms_p95 <= 1200 and
        r.trust_score >= 4.2
    )
```

### 7.6 SQL — Feedback-to-Eval Materialization

```sql
INSERT INTO eval_cases
SELECT
  f.event_id,
  f.prompt_version,
  f.workflow_version,
  f.operator_outcome,
  c.context_blob,
  now() AS created_at
FROM feedback_events f
JOIN case_context c ON c.case_id = f.case_id
WHERE f.operator_outcome IN ('reject', 'major_edit')
  AND f.created_at >= now() - interval '14 days';
```

---

## 8) Scenario Walkthrough (Cinematic + Credible)

1. A maritime sensor emits anomalous AIS + RF signature data (`signals.raw`).
2. `TriageAgent` flags mismatch pattern probability 0.91 and opens a provisional alert.
3. `EnrichmentAgent` pulls historical route deviations, ownership links, sanctions adjacency.
4. `CorrelationAgent` binds device/entity/location in ontology and produces confidence-scored hypothesis graph.
5. `RecommendationAgent` proposes action package: “Open priority case + notify maritime desk.”
6. Policy service requires human approval due to coalition-sensitive source.
7. Operator approves case, rejects notify action (insufficient corroboration).
8. Outcome logged:
   - recommendation partially accepted,
   - operator rationale captured,
   - downstream mission success tracked 24h later.
9. Self-improvement loop:
   - eval case generated from rejected notify action,
   - prompt `recommendation/v1.4.2` updated to require dual-source corroboration for notify,
   - canary run shows 23% reduction in false-positive notifications,
   - Apollo promotes to 100% after approval board sign-off.

Result: faster triage, fewer false escalations, improved operator trust, and fully auditable decision evolution.

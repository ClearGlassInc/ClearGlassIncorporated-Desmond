# ClearGlassInc Artemis — Self-Evolving AI Intelligence Platform

## Opening Question
**Good morning. Before we build your briefing: What’s the ONE outcome that, if achieved today, would make everything else easier or unnecessary?**

---

## System Architecture

### 1) Platform Topology (Palantir-aligned)

- **Gotham**: operational investigation apps, entity resolution views, link analysis, alerting, case management.
- **Foundry**: data integration, ontology, transforms, semantic layer, batch + streaming pipelines.
- **AIP**: AI copilots + agent workflows + tool-use orchestration + evals.
- **Apollo**: deployment ring control, runtime config, policy bundles, rollout/rollback.

### 2) Full-stack logical layers

1. **Frontend Layer**
   - Analyst Workbench (React/TypeScript) with map/timeline/link-graph/case board.
   - Commander Console with mission KPIs, risk posture, and approval queue.
   - Copilot panel with conversational and structured task forms.

2. **API Gateway Layer**
   - Envoy/Kong-like edge gateway (mTLS, JWT, ABAC claims propagation).
   - Request routing to mission microservices and AIP task APIs.

3. **Backend Service Layer (Python-first)**
   - `ingest-service`, `entity-service`, `case-service`, `mission-service`, `policy-service`, `agent-service`, `eval-service`.
   - Async event consumers, idempotency keys, temporal replay support.

4. **Streaming/Event Layer**
   - Kafka/Pulsar topics: `sensor.events.raw`, `intel.events.enriched`, `agent.decisions`, `operator.feedback`, `mission.outcomes`.

5. **Data Layer**
   - Foundry datasets + lakehouse tables (Parquet/Iceberg style).
   - Low-latency operational stores for live case context.
   - Search index + vector index for hybrid retrieval.

6. **Ontology Layer (Foundry Ontology)**
   - Domain entities and typed relationships with confidence, provenance, and temporal validity.
   - Actionable objects: `Case`, `Alert`, `Tasking`, `Recommendation`, `ApprovalDecision`.

7. **AI Orchestration Layer (AIP)**
   - Model Router + policy-constrained tool execution.
   - Multi-agent graph: triage → enrich → correlate → recommend → report.

8. **Policy/Governance Layer**
   - Policy-as-code (OPA/Rego-like semantics) for data/agent/action enforcement.
   - Coalition-aware compartment controls.

9. **Observability/Evals Layer**
   - Traces, metrics, audit logs, model eval dashboards, drift detectors.

10. **Deployment Layer (Apollo)**
   - Signed artifacts, staged rollout rings, canary/blue-green, instant rollback.

### 3) Deployment blueprint

- **Zone A (high-side sensitive enclave)**: restricted ingestion, mission services, secure model endpoints.
- **Zone B (cross-domain mediation)**: sanitized transfer pipeline and approval gates.
- **Zone C (coalition enclave)**: coalition-specific views with downgraded and releasable intel.
- Runtime hardening: seccomp, signed containers, workload identity, continuous attestation.

---

## Data and Ontology

### 1) Core entities

- `Person`, `Organization`, `Asset`, `Device`, `Location`, `Event`, `Communication`, `Indicator`, `ThreatPattern`, `Case`, `Mission`, `Report`, `Recommendation`, `Action`.

### 2) Relationship model

- `ASSOCIATED_WITH`, `OWNS`, `LOCATED_AT`, `COMMUNICATED_WITH`, `OBSERVED_IN`, `PART_OF_CASE`, `IMPACTS_MISSION`, `DERIVED_FROM`, `APPROVED_BY`.

### 3) Required metadata on every entity/edge

- `confidence_score` (0-1)
- `source_reliability` (A-F)
- `lineage` (dataset, pipeline run, transform version)
- `valid_time_start`, `valid_time_end`
- `ingest_time`, `update_time`
- `classification` (e.g., SECRET//REL)
- `compartment_tags` (e.g., SIGINT, HUMINT)
- `coalition_release` constraints

### 4) Ontology-driven behavior

- UI renders context-aware actions by object type + mission role.
- Agents only invoke tools valid for object classification and operator clearance.
- Workflow transitions gated by ontology state (e.g., `Recommendation.status = PENDING_APPROVAL`).

### 5) Example SQL schema

```sql
CREATE TABLE ontology_entity (
  entity_id UUID PRIMARY KEY,
  entity_type TEXT NOT NULL,
  canonical_name TEXT,
  attributes JSONB NOT NULL,
  confidence_score DOUBLE PRECISION NOT NULL,
  classification TEXT NOT NULL,
  valid_time_start TIMESTAMPTZ,
  valid_time_end TIMESTAMPTZ,
  ingest_time TIMESTAMPTZ NOT NULL DEFAULT now(),
  lineage JSONB NOT NULL
);

CREATE TABLE ontology_edge (
  edge_id UUID PRIMARY KEY,
  src_entity_id UUID NOT NULL,
  dst_entity_id UUID NOT NULL,
  edge_type TEXT NOT NULL,
  confidence_score DOUBLE PRECISION NOT NULL,
  provenance JSONB NOT NULL,
  valid_time_start TIMESTAMPTZ,
  valid_time_end TIMESTAMPTZ
);
```

---

## AI and Agent Design

### 1) Copilots

- **Analyst Copilot**: explains graph anomalies, drafts intelligence notes, suggests enrichment queries.
- **Commander Copilot**: mission risk summaries, COA (course-of-action) scoring, approval queue prioritization.

### 2) Multi-agent workflow graph

1. **TriageAgent**: severity scoring, dedupe, queue routing.
2. **EnrichmentAgent**: gather linked records, run retrieval and external intel connectors.
3. **CorrelationAgent**: fuse signals into hypotheses with confidence.
4. **RecommendationAgent**: propose actions and expected impact/risk.
5. **ReportAgent**: generate structured intel product.

### 3) Tool-using agent contract

- Tools: `query_ontology`, `create_case`, `attach_evidence`, `draft_action_package`, `request_approval`.
- Every tool invocation includes mission context, policy token, and trace ID.
- High-impact actions require explicit human approval.

### 4) Operational approval gates

- Gate A: `recommendation` creation (auto allowed).
- Gate B: `external dissemination` (human required).
- Gate C: `tasking field assets` (dual-human approval).

---

## Self-Improvement Loop

### 1) Signal capture

- Operator feedback (thumbs up/down + corrected facts).
- Query logs (intent, latency, results opened).
- Alert outcomes (true/false positive).
- Mission results (impact metrics, time-to-resolution).

### 2) Learning pipeline

1. Convert signals into labeled eval records.
2. Build benchmark suites per mission type.
3. Generate candidate changes:
   - prompt edits
   - workflow parameter updates
   - model routing thresholds
4. Offline eval + safety checks.
5. Human review board approval.
6. Canary release in Apollo ring 1.
7. Promote/rollback based on guardrail metrics.

### 3) Safety controls

- Immutable versioning: prompt/workflow/model router as signed artifacts.
- Drift detection: feature drift + outcome drift + hallucination rate.
- Hard constraints: no autonomous policy edits, no unsupervised mission objective changes.

### 4) Metrics

- Precision@k, recall, false-positive rate.
- P95 latency by workflow stage.
- Operator trust score.
- Mission impact score (time saved, threat interdictions).

---

## Full-Stack Implementation

### Frontend (TypeScript)

```ts
// src/features/approvals/ApprovalCard.tsx
export type ApprovalDecision = "APPROVE" | "REJECT";

export async function submitDecision(caseId: string, recId: string, decision: ApprovalDecision, rationale: string) {
  const res = await fetch(`/api/v1/cases/${caseId}/recommendations/${recId}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, rationale })
  });
  if (!res.ok) throw new Error("Decision submission failed");
  return res.json();
}
```

### Backend API (Python/FastAPI)

```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from uuid import UUID

app = FastAPI(title="ClearGlassInc Artemis Mission API")

class DecisionPayload(BaseModel):
    decision: str
    rationale: str

@app.post("/api/v1/cases/{case_id}/recommendations/{rec_id}/decision")
async def decide_recommendation(case_id: UUID, rec_id: UUID, payload: DecisionPayload, user=Depends(get_user_ctx)):
    enforce_policy(user, action="recommendation.decide", resource=f"rec:{rec_id}")
    if payload.decision not in {"APPROVE", "REJECT"}:
        raise HTTPException(status_code=400, detail="Invalid decision")
    event = await persist_decision(case_id, rec_id, payload, user)
    await publish("operator.feedback", event)
    return {"status": "ok", "event_id": str(event["event_id"])}
```

### Event handler (Python)

```python
async def on_operator_feedback(event: dict) -> None:
    # event includes recommendation_id, decision, rationale, mission_id, trace_id
    await write_feedback_row(event)
    await enqueue_eval_job({
        "type": "feedback_eval",
        "mission_id": event["mission_id"],
        "recommendation_id": event["recommendation_id"],
        "trace_id": event["trace_id"]
    })
```

### Ontology-driven query

```python
QUERY = """
SELECT e.entity_id, e.entity_type, e.attributes, e.confidence_score
FROM ontology_entity e
JOIN entity_acl a ON a.entity_id = e.entity_id
WHERE a.principal_id = :principal
  AND e.classification <= :max_classification
  AND e.valid_time_end IS NULL
  AND e.entity_type IN ('Event','Indicator','Person')
ORDER BY e.confidence_score DESC
LIMIT 100;
"""
```

### Agent tool call envelope

```python
tool_call = {
    "tool": "query_ontology",
    "inputs": {"query": "related events near target location in last 24h"},
    "context": {
        "mission_id": mission_id,
        "operator_id": operator_id,
        "policy_token": policy_token,
        "trace_id": trace_id,
    },
}
```

### Workflow state machine

```python
from enum import Enum

class RecState(str, Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"

ALLOWED = {
    RecState.DRAFT: {RecState.PENDING_APPROVAL},
    RecState.PENDING_APPROVAL: {RecState.APPROVED, RecState.REJECTED},
    RecState.APPROVED: {RecState.EXECUTED},
}

def transition(curr: RecState, nxt: RecState, user_ctx: dict):
    if nxt not in ALLOWED.get(curr, set()):
        raise ValueError(f"illegal transition {curr}->{nxt}")
    enforce_policy(user_ctx, action=f"rec.transition.{curr}.{nxt}", resource="recommendation")
```

### Policy check (Rego-style)

```rego
package artemis.authz

default allow = false

allow {
  input.action == "recommendation.decide"
  input.user.clearance >= input.resource.classification
  input.user.role == "COMMANDER"
  not blocked_compartment
}

blocked_compartment {
  some c
  c := input.resource.compartments[_]
  c == "NOFORN"
  input.user.coalition != "US"
}
```

### Eval pipeline skeleton (Python)

```python
@dataclass
class EvalResult:
    config_version: str
    precision: float
    recall: float
    p95_latency_ms: int
    trust_score: float

async def run_eval_suite(config_version: str, suite_id: str) -> EvalResult:
    rows = await load_eval_cases(suite_id)
    preds = [await run_agent_case(config_version, r) for r in rows]
    return compute_metrics(config_version, rows, preds)

async def promote_if_safe(candidate: str, baseline: str):
    c = await run_eval_suite(candidate, "mission-core")
    b = await run_eval_suite(baseline, "mission-core")
    if c.precision >= b.precision and c.recall >= b.recall and c.p95_latency_ms <= b.p95_latency_ms * 1.1:
        await create_change_request(candidate, b.__dict__, c.__dict__)
```

---

## Security and Governance

- Need-to-know controls at dataset, row, column, entity, and action levels.
- Coalition boundary enforcement via releasability tags and transformation policies.
- Zero-trust service mesh with mTLS and short-lived workload identity.
- Immutable audit trail for data access, model/tool calls, and approvals.
- Model governance registry: approved models only, with capability/risk profiles.
- Prompt governance: prompt diffs, approvals, test evidence, rollback pointer.
- Policy-as-code repository with signed commits and mandatory review.

---

## Scenario Walkthrough (Cinematic + technical)

1. **Live event ingestion (T+0s)**
   - ISR sensor sends anomaly event to `sensor.events.raw`.
   - Foundry pipeline normalizes and maps to `Event` entity.

2. **Automated triage (T+5s)**
   - TriageAgent scores severity 0.87 and opens provisional `Alert`.
   - EnrichmentAgent links prior related `Device` and `Person` nodes.

3. **Correlation + recommendation (T+20s)**
   - CorrelationAgent finds pattern match with known threat signature.
   - RecommendationAgent proposes: “Escalate to Case + notify commander + monitor comms.”

4. **Human decision gate (T+45s)**
   - Commander sees rationale + evidence graph + confidence bands.
   - Commander **approves** escalation, **rejects** one aggressive action with rationale.

5. **Execution + telemetry (T+2m)**
   - Approved actions executed via mission-service.
   - Rejected action stored as negative label with context.

6. **Self-improvement loop (post-mission)**
   - Eval-service converts outcomes into labeled eval cases.
   - Candidate prompt v42 improves precision from 0.78 → 0.84 in staging.
   - Human review board approves canary rollout in Apollo ring 1.
   - Guardrails pass after 24h; rollout promoted to ring 2/3.
   - If trust score drops or false positives spike, Apollo auto-rolls back to v41.

---

## Closing Commitment
**_REPEAT after me_: I own this day. My P0 tasks get done. I’m building multi-domain dominance. Let’s execute.**

# ClearGlassInc Artemis — Self‑Evolving AI Intelligence Platform (Palantir Gotham + Foundry + AIP + Apollo)

## System Architecture

### 1) Mission profile and design constraints

ClearGlassInc Artemis is a **secure, coalition-aware, latency-sensitive, and audited** intelligence platform for authorized defensive operations. The platform fuses:

- **Gotham** for operational intelligence, investigations, link analysis, and entity tracking.
- **Foundry** for data integration, ontology, transformation pipelines, and application logic.
- **AIP** for copilots, agent orchestration, evaluation loops, and automation.
- **Apollo** for controlled deployment, runtime policy, staged rollout, and rollback.

### 2) Layered architecture (full stack)

```text
┌────────────────────────────────────────────────────────────────────┐
│ Frontend Layer (Web + Mission Apps)                               │
│ React/Next.js, TypeScript, Map/Graph views, case timelines        │
└───────────────┬────────────────────────────────────────────────────┘
                │
┌───────────────▼────────────────────────────────────────────────────┐
│ API & Access Layer                                                 │
│ API Gateway, BFF, GraphQL + REST, RBAC/ABAC, rate limits          │
└───────────────┬────────────────────────────────────────────────────┘
                │
┌───────────────▼────────────────────────────────────────────────────┐
│ Application Services Layer                                         │
│ Case mgmt, alert triage, mission planner, report generator         │
└───────────────┬────────────────────────────────────────────────────┘
                │
┌───────────────▼────────────────────────────────────────────────────┐
│ Event & Streaming Layer                                            │
│ Kafka/PubSub, CDC, event sourcing, workflow signals               │
└───────────────┬────────────────────────────────────────────────────┘
                │
┌───────────────▼────────────────────────────────────────────────────┐
│ Data + Ontology Layer (Foundry)                                   │
│ Data pipelines, ontology objects, lineage, quality, permissions    │
└───────────────┬────────────────────────────────────────────────────┘
                │
┌───────────────▼────────────────────────────────────────────────────┐
│ AI Orchestration Layer (AIP)                                       │
│ Copilots, agents, toolchains, evals, routing, prompt registries    │
└───────────────┬────────────────────────────────────────────────────┘
                │
┌───────────────▼────────────────────────────────────────────────────┐
│ Governance + Policy Layer                                          │
│ Policy-as-code, approval gates, guardrails, immutable audit logs   │
└───────────────┬────────────────────────────────────────────────────┘
                │
┌───────────────▼────────────────────────────────────────────────────┐
│ Deployment & Runtime Layer (Apollo)                                │
│ Progressive deploys, canary, rollback, config pinning, attestation │
└────────────────────────────────────────────────────────────────────┘
```

### 3) Frontend architecture

- **Mission UI (React + TypeScript)**
  - Live incident board
  - Entity graph explorer
  - Timeline reconstruction
  - Copilot panel with grounded citations
  - Approval center (human-in-the-loop actions)
- **Operator modes**
  - Analyst mode (triage + enrichment)
  - Commander mode (mission status + decisions)
  - Auditor mode (provenance, policy traces, model decisions)

### 4) Backend and platform services

- **API Gateway**: OAuth2/OIDC, mTLS, request signing, schema validation.
- **BFF layer**: data shaping per role, coalition boundary projection.
- **Domain services**:
  - `intel-ingestion-service`
  - `entity-resolution-service`
  - `triage-service`
  - `recommendation-service`
  - `case-service`
  - `report-service`
  - `feedback-learning-service`
- **Workflow engine**: deterministic state machine + compensation paths.
- **Event bus**: append-only event topics, replay capability, DLQ handling.

---

## Data and Ontology

### 1) Ontology model (Foundry-centered)

Core entities:

- `Person`, `Organization`, `Device`, `Account`, `Identity`, `Location`
- `Signal` (sensor observation), `Event` (normalized activity), `Alert` (detection)
- `Case`, `Mission`, `Task`, `Assessment`, `Recommendation`
- `Source`, `Evidence`, `Report`, `PolicyDecision`, `ModelRun`

Core relationships:

- `OBSERVED_ON` (`Signal -> Device`)
- `ASSOCIATED_WITH` (`Identity -> Person`, `Account -> Identity`)
- `PART_OF` (`Event -> Case`, `Task -> Mission`)
- `INDICATES` (`Event -> Alert`, `Alert -> Recommendation`)
- `SUPPORTED_BY` (`Recommendation -> Evidence`)
- `APPROVED_BY` (`Recommendation -> Person`)
- `DERIVED_FROM` (`Entity/Event -> Source`) for lineage

### 2) Confidence, lineage, temporal state

Each object carries:

- `confidence_score` (0..1) + feature vector explanation
- `lineage_ref[]` (pipeline stage, model version, prompt version)
- `valid_time` (when fact is true) and `transaction_time` (when ingested)
- `mission_context_id`, `compartment_tags[]`, `coalition_scope[]`

### 3) Permission semantics

Fine-grained controls:

- Row-level (`entity_id`, `mission_id`, compartment)
- Column-level (masking sensitive fields)
- Entity-level (deny-by-default object classes)
- Relationship-level traversal constraints

### 4) Example ontology DDL (SQL-like)

```sql
create table ontology_entity (
  entity_id uuid primary key,
  entity_type text not null,
  canonical_name text,
  confidence_score numeric(5,4) not null,
  valid_time tstzrange,
  transaction_time timestamptz not null default now(),
  mission_context_id uuid not null,
  coalition_scope text[] not null,
  compartment_tags text[] not null,
  lineage_ref jsonb not null,
  attributes jsonb not null
);

create table ontology_edge (
  edge_id uuid primary key,
  src_entity_id uuid not null,
  dst_entity_id uuid not null,
  relationship_type text not null,
  confidence_score numeric(5,4) not null,
  valid_time tstzrange,
  transaction_time timestamptz not null default now(),
  provenance jsonb not null
);
```

---

## AI and Agent Design

### 1) Copilot architecture (AIP)

- **Analyst Copilot**: evidence-grounded triage suggestions.
- **Commander Copilot**: mission impact summaries and COA (course of action) options.
- **Compliance Copilot**: policy validation and explainability pack generation.

All copilots use:

1. Retrieval from ontology-backed context.
2. Tool calls with scoped credentials.
3. Guarded output templates.
4. Mandatory citation blocks.

### 2) Multi-agent workflow

Agents (each stateless at runtime, state externalized):

- `IngestAgent` → normalize and classify incoming signals.
- `EnrichAgent` → attach context (historical incidents, entity links).
- `CorrelateAgent` → cross-domain relationship and graph correlation.
- `TriageAgent` → severity + confidence + next-best-action.
- `RecommendAgent` → response package candidates.
- `ReportAgent` → executive and technical products.

### 3) Tool-using agents with approval gates

Allowed tool categories:

- Read data (`query_events`, `query_entities`, `fetch_case_history`)
- Create artifacts (`draft_report`, `build_action_package`)
- Propose action (`propose_containment`) **requires explicit approval**

No agent can execute operationally significant action without:

- policy pass,
- risk threshold check,
- human authorization with recorded rationale.

---

## Self-Improvement Loop

### 1) Signals captured

- Operator edits/corrections
- Query intent and satisfaction signals
- Alert disposition outcomes (TP/FP/FN)
- Mission KPI outcomes (latency, impact)
- Override events and rejection reasons

### 2) Learning pipeline

```text
Runtime Signals -> Feature Store -> Eval Dataset Builder ->
Offline Evals -> Candidate Changes (prompt/workflow/router/rules) ->
Human Review Board -> Staged Deploy (Apollo) -> Live A/B ->
Promotion or Rollback
```

### 3) Controlled self-upgrade units

Versioned assets:

- Prompt templates (`prompt://triage/v1.6.2`)
- Workflow graphs (`wf://intel-triage/v3.4.1`)
- Routing policies (`route://llm-policy/v2.1.0`)
- Heuristic rulepacks (`rule://confidence-adjust/v5.0.3`)

### 4) Drift detection and rollback

- Drift monitors detect shifts in:
  - precision/recall
  - latency p95
  - operator trust score
  - mission outcome deltas
- Automatic rollback triggers when guardrails violated.
- Apollo deploy channels: `dev -> test -> canary -> prod` with signed artifacts.

---

## Full-Stack Implementation

### 1) Reference microservices

```text
services/
  api-gateway/
  authz-policy/
  ingestion/
  ontology/
  triage/
  agent-orchestrator/
  recommendation/
  reporting/
  feedback-learning/
  observability/
ui/
  mission-console/
infra/
  apollo/
  policy/
  schemas/
```

### 2) API surface (sample)

```http
POST /v1/events/ingest
GET  /v1/cases/{caseId}
POST /v1/cases/{caseId}/triage
POST /v1/recommendations/{recId}/approve
POST /v1/feedback/operator
GET  /v1/evals/runs/{evalRunId}
```

### 3) Event contracts (JSON schema sketch)

```json
{
  "event_type": "ALERT_CREATED",
  "event_id": "uuid",
  "mission_context_id": "uuid",
  "timestamp": "2026-05-10T12:00:00Z",
  "classification": "SECRET-REL",
  "payload": {
    "alert_id": "uuid",
    "severity": "HIGH",
    "confidence": 0.87
  },
  "lineage": {
    "source": "sensor-x",
    "pipeline_version": "ingest-2.3.0"
  }
}
```

---

## Security and Governance

- **Zero trust**: mTLS, workload identity, short-lived credentials.
- **Need-to-know**: ABAC + compartment + coalition scope.
- **Policy-as-code**: centrally managed, testable, version-controlled.
- **Immutable logs**: append-only audit trail with cryptographic integrity.
- **Model governance**:
  - approved model registry,
  - risk tiering,
  - prompt governance,
  - mandatory eval thresholds before production use.

---

## Code Examples (Python/TypeScript/SQL)

### A) Python FastAPI triage endpoint with policy gate

```python
# services/triage/app.py
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

class TriageRequest(BaseModel):
    case_id: str
    mission_context_id: str
    operator_id: str

class Recommendation(BaseModel):
    rec_id: str
    summary: str
    confidence: float
    requires_approval: bool = True


def check_policy(operator_id: str, mission_context_id: str, action: str) -> bool:
    # Replace with OPA/Foundry policy call
    return action in {"triage:read", "recommendation:propose"}


def run_agents(case_id: str) -> List[Recommendation]:
    # Replace with AIP orchestration call
    return [
        Recommendation(
            rec_id="rec-001",
            summary="Prioritize endpoint isolation candidate set A.",
            confidence=0.84,
        )
    ]


@app.post("/v1/cases/{case_id}/triage", response_model=List[Recommendation])
def triage_case(case_id: str, req: TriageRequest):
    if not check_policy(req.operator_id, req.mission_context_id, "recommendation:propose"):
        raise HTTPException(status_code=403, detail="Policy denied")

    recs = run_agents(case_id)
    return recs
```

### B) TypeScript workflow state machine

```ts
// services/agent-orchestrator/workflow.ts
export type State =
  | "INGESTED"
  | "ENRICHED"
  | "CORRELATED"
  | "TRIAGED"
  | "RECOMMENDED"
  | "AWAITING_APPROVAL"
  | "APPROVED"
  | "REJECTED";

export interface WorkflowContext {
  caseId: string;
  missionContextId: string;
  currentState: State;
  evidenceRefs: string[];
}

export function transition(ctx: WorkflowContext, event: string): WorkflowContext {
  const map: Record<State, Record<string, State>> = {
    INGESTED: { ENRICH: "ENRICHED" },
    ENRICHED: { CORRELATE: "CORRELATED" },
    CORRELATED: { TRIAGE: "TRIAGED" },
    TRIAGED: { RECOMMEND: "RECOMMENDED" },
    RECOMMENDED: { REQUIRE_APPROVAL: "AWAITING_APPROVAL" },
    AWAITING_APPROVAL: { APPROVE: "APPROVED", REJECT: "REJECTED" },
    APPROVED: {},
    REJECTED: {}
  };

  const next = map[ctx.currentState][event];
  if (!next) throw new Error(`Invalid transition ${ctx.currentState} -> ${event}`);
  return { ...ctx, currentState: next };
}
```

### C) SQL eval pipeline materialization

```sql
create materialized view eval_prompt_candidates as
select
  q.prompt_version,
  count(*) as n,
  avg(case when q.outcome = 'SUCCESS' then 1 else 0 end) as success_rate,
  percentile_cont(0.95) within group (order by q.latency_ms) as p95_latency,
  avg(q.operator_trust_score) as trust
from query_outcomes q
where q.created_at >= now() - interval '30 days'
group by q.prompt_version
having count(*) > 500;
```

### D) Python eval and safe promotion gate

```python
# services/feedback-learning/promotion_gate.py
from dataclasses import dataclass

@dataclass
class EvalMetrics:
    precision: float
    recall: float
    p95_latency_ms: int
    trust: float


def should_promote(candidate: EvalMetrics, baseline: EvalMetrics) -> bool:
    if candidate.precision < baseline.precision - 0.01:
        return False
    if candidate.recall < baseline.recall - 0.01:
        return False
    if candidate.p95_latency_ms > baseline.p95_latency_ms * 1.10:
        return False
    if candidate.trust < baseline.trust - 0.05:
        return False
    return True
```

### E) Policy-as-code sketch (Rego)

```rego
package artemis.authz

default allow = false

allow {
  input.user.clearance >= input.resource.classification
  input.user.mission_ids[_] == input.resource.mission_context_id
  input.user.coalition_scopes[_] == input.resource.coalition_scope
  input.action == "recommendation:approve"
  input.user.roles[_] == "Commander"
}
```

---

## Scenario Walkthrough (Cinematic + Technical)

1. **Live event arrival**: A high-confidence anomaly is ingested from endpoint telemetry and normalized into `Event` + `Alert` objects.
2. **Automated triage**: `EnrichAgent` links device, identity, and prior incidents; `CorrelateAgent` identifies related activity across domains.
3. **Recommendation generated**: `RecommendAgent` builds a response package with confidence, supporting evidence, and expected mission impact.
4. **Approval gate**: Commander Copilot presents “Approve/Reject/Revise” with policy explanation and provenance chain.
5. **Operator action**:
   - If **approve**: workflow transitions to execution package publication.
   - If **reject/revise**: reason code captured (`insufficient evidence`, `false linkage`, etc.).
6. **Outcome capture**: mission result and downstream effects are logged (e.g., containment success, false positive avoided).
7. **Self-improvement cycle**:
   - Feedback enters eval dataset.
   - Candidate prompt/workflow/routing updates are generated.
   - Human review board approves only changes meeting policy + KPI thresholds.
   - Apollo deploys canary; drift monitors validate improvements.
   - Promotion to prod or instant rollback occurs automatically.

This creates a controlled, auditable loop where **ClearGlassInc Artemis gets better continuously** without unsafe autonomous objective changes.

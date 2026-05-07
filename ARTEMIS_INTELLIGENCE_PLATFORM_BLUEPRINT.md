# ClearGlassInc Artemis — Self-Evolving AI Intelligence Platform (Palantir Gotham + Foundry + AIP + Apollo)

## System Architecture

### 1. End-to-End Layered Architecture

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Frontend Mission Apps (Web UI, Ops Console, Command COP, Mobile Edge)  │
└───────────────┬──────────────────────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────────────────────┐
│ API Edge: mTLS Ingress, API Gateway, OIDC, PDP/PEP, Rate & DLP Guards  │
└───────────────┬──────────────────────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────────────────────┐
│ Domain Backend: Case, Entity, Mission, Alert, Recommendation Services   │
│ + Orchestration Runtime + Workflow State Machine + Tool Registry         │
└───────────────┬──────────────────────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────────────────────┐
│ Event Fabric: Kafka/Pulsar, CDC, Stream Processing, Replay, DLQ         │
└───────────────┬──────────────────────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────────────────────┐
│ Foundry Data Plane: Connectors, Pipelines, Ontology, Feature Sets       │
│ Lakehouse, Data Products, Lineage, Data Contracts                        │
└───────────────┬──────────────────────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────────────────────┐
│ Retrieval Plane: Graph + Full-text + Vector + Temporal Index            │
└───────────────┬──────────────────────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────────────────────┐
│ AIP Intelligence Plane: Copilots, Agent Swarms, Evals, Model Router     │
│ Prompt/Workflow Registry + Guardrails + Simulation Sandbox               │
└───────────────┬──────────────────────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────────────────────┐
│ Governance/Observability: OTel, Metrics, Tracing, Audit, Policy-as-Code │
└───────────────┬──────────────────────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────────────────────┐
│ Apollo Control Plane: Progressive Delivery, Rollback, Runtime Kill-Switch│
└──────────────────────────────────────────────────────────────────────────┘
```

### 2. Precise Palantir Role Mapping
- **Gotham**: live operational picture, investigations, entity link analysis, case timelines.
- **Foundry**: data integration, ontology-backed app logic, reproducible pipelines, lineage.
- **AIP**: copilots, agent execution, eval harnesses, model/prompt/workflow routing.
- **Apollo**: deployment rings, hardened upgrades, remote policy rollout, instant rollback.

### 3. Runtime Topology (Coalition-Aware)
- **Tier-0 Edge**: gateway, authn, malware inspection, schema firewall.
- **Tier-1 Mission Core**: operational services, graph APIs, approval workflows.
- **Tier-2 Restricted**: high-side datasets/models, cross-domain guards.
- **Tier-3 Coalition Exchange**: releasability transformer + redaction broker.

---

## Data and Ontology

### 1. Canonical Ontology for ClearGlassInc Artemis

**Entity classes**
- `Person`, `Org`, `Asset`, `Device`, `GeoCell`, `Event`, `Signal`, `Case`, `Mission`, `Alert`, `Hypothesis`, `Recommendation`, `ActionPackage`, `Outcome`.

**Relationship classes**
- `COMMUNICATED_WITH`, `LOCATED_AT`, `ASSOCIATED_WITH`, `OBSERVED_IN`, `PART_OF_MISSION`, `TRIGGERED_ALERT`, `SUPPORTS_HYPOTHESIS`, `PROPOSES_ACTION`, `APPROVED_BY`, `EXECUTED_AS`, `RESULTED_IN`.

**Mandatory metadata**
- Confidence (`0..1`), source reliability (`A..F`), classification, releasability, tenant/coalition boundary, temporal validity (`valid_from`, `valid_to`), provenance hash.

### 2. SQL + Graph Schema (Representative)

```sql
CREATE TABLE artemis_entity (
  entity_id            TEXT PRIMARY KEY,
  entity_type          TEXT NOT NULL,
  canonical_name       TEXT,
  attributes_json      JSONB NOT NULL,
  confidence           DOUBLE PRECISION NOT NULL,
  classification       TEXT NOT NULL,
  releasability_tags   TEXT[] NOT NULL,
  need_to_know_tags    TEXT[] NOT NULL,
  mission_scope        TEXT[] NOT NULL,
  lineage_ref          TEXT NOT NULL,
  valid_from_ts        TIMESTAMPTZ NOT NULL,
  valid_to_ts          TIMESTAMPTZ,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE artemis_relation (
  relation_id          TEXT PRIMARY KEY,
  src_entity_id        TEXT NOT NULL REFERENCES artemis_entity(entity_id),
  dst_entity_id        TEXT NOT NULL REFERENCES artemis_entity(entity_id),
  relation_type        TEXT NOT NULL,
  confidence           DOUBLE PRECISION NOT NULL,
  mission_id           TEXT NOT NULL,
  evidence_refs        TEXT[] NOT NULL,
  valid_from_ts        TIMESTAMPTZ NOT NULL,
  valid_to_ts          TIMESTAMPTZ
);
```

### 3. Permissions as First-Class Ontology Constraints
Every ontology object carries policy labels; agent tools auto-include `mission_scope`, `classification`, and `coalition` filters before query execution.

---

## AI and Agent Design

### 1. Copilot Suite
- **Analyst Copilot**: triage and confidence explanations.
- **Commander Copilot**: mission impact projections and action options.
- **Watchfloor Copilot**: anomaly watch + escalation guidance.

### 2. Multi-Agent Workflow Graph

```text
Signal Ingest -> Triage Agent -> Enrichment Agent -> Correlation Agent
            -> Hypothesis Agent -> Recommendation Agent -> Approval Gate
            -> Execution Integrator (only after approval)
```

### 3. Tool Contract (Policy-bound)
```python
from pydantic import BaseModel, Field

class ToolCall(BaseModel):
    tool_name: str
    mission_id: str
    justification: str = Field(min_length=20)
    requested_scope: list[str]
    inputs: dict

ALLOWED_TOOLS = {
    "query_ontology",
    "open_case",
    "draft_action_package",
    "request_approval",
    "write_intel_brief",
}
```

Operationally significant tools (`execute_tasking`, `notify_partner_force`) are disabled unless human approval token exists.

---

## Self-Improvement Loop

### 1. Feedback Capture
Ingest structured feedback streams:
- `operator.corrections`
- `recommendation.accept_reject`
- `alert.truth_labels`
- `mission.outcomes`
- `latency.slo_breaches`

### 2. Closed-Loop Optimization Pipeline
1. **Collect** telemetry and outcomes.
2. **Curate** eval datasets (stratified by mission type/clearance).
3. **Evaluate** prompts, workflows, model routes.
4. **Propose patch**: prompt/workflow/routing heuristic change.
5. **Simulate** on replay corpus.
6. **Require human review** (Ops + Security + Mission Lead).
7. **Canary via Apollo**.
8. **Observe + rollback automatically** on policy/metric regression.

### 3. Drift Detection Rules
- Embedding centroid shift > threshold.
- False positive rate delta > 8% vs baseline.
- Approval override ratio worsens for 3 consecutive windows.

---

## Full-Stack Implementation

### 1. Frontend (TypeScript/React)
- Live mission event board, graph explorer, timeline, recommendation panel.
- “Why this recommendation?” panel: evidence nodes + policy checks + model route.
- Dual approval UX: operational + legal/policy confirmation.

### 2. API Gateway
- OIDC/JWT + mTLS client cert binding.
- OPA/rego policy check at request ingress.
- Content-based DLP for outbound text.

### 3. Python Service Mesh (FastAPI)
- `ingest-service`
- `entity-resolution-service`
- `mission-service`
- `agent-orchestrator-service`
- `approval-service`
- `eval-service`

### 4. Streaming/Data
- Kafka topics: raw/enriched/correlated/recommendations/approvals/outcomes.
- Lakehouse tables for replay + model evaluation.
- Graph DB for relation traversals, vector DB for semantic recall.

---

## Security and Governance

### 1. Zero-Trust + Need-to-Know
- SPIFFE identities for every workload.
- ABAC+RBAC hybrid with mission context attributes.
- Entity-level authorization check before every read.

### 2. Immutable Provenance
- Append-only audit ledger with hash chaining.
- Every AI output stores `{model_version, prompt_version, workflow_version, tool_trace_id}`.

### 3. Policy-as-Code (Rego)
```rego
package artemis.authz

default allow = false

allow {
  input.user.clearance_level >= input.resource.classification_level
  input.user.mission_tags[_] == input.resource.mission_tag
  not blocked_coalition(input.user.coalition, input.resource.releasability)
}
```

---

## Code Examples

### A) FastAPI: Policy-Enforced Ontology Query
```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

app = FastAPI(title="ClearGlassInc Artemis API")

class QueryRequest(BaseModel):
    mission_id: str
    query: str
    classification: str

async def authorize(req: QueryRequest, user=Depends(...)):
    allowed = await policy_engine.allow(user=user, resource={
        "mission_id": req.mission_id,
        "classification": req.classification,
    })
    if not allowed:
        raise HTTPException(status_code=403, detail="Denied by policy")

@app.post("/ontology/query")
async def ontology_query(req: QueryRequest, _=Depends(authorize)):
    return await ontology_store.semantic_query(req.query, mission_id=req.mission_id)
```

### B) Event Handler: Recommendation Generation
```python
async def on_correlated_signal(event: dict):
    context = await retrieval_bundle(event["mission_id"], event["entity_ids"])
    rec = await agent_runtime.run_workflow(
        workflow="recommendation_v12",
        inputs={"event": event, "context": context},
        policy_mode="strict"
    )
    await bus.publish("recommendations.proposed", rec)
```

### C) Workflow State Machine (Approval Gates)
```python
from enum import Enum

class State(str, Enum):
    TRIAGED = "TRIAGED"
    ENRICHED = "ENRICHED"
    CORRELATED = "CORRELATED"
    RECOMMENDED = "RECOMMENDED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"

VALID_TRANSITIONS = {
    State.RECOMMENDED: {State.PENDING_APPROVAL},
    State.PENDING_APPROVAL: {State.APPROVED, State.REJECTED},
    State.APPROVED: {State.EXECUTED},
}
```

### D) Evaluation Pipeline Skeleton
```python
def eval_candidate(candidate_version: str, baseline_version: str, dataset: list[dict]):
    cand = run_eval(candidate_version, dataset)
    base = run_eval(baseline_version, dataset)

    gates = {
        "precision": cand["precision"] >= base["precision"] - 0.01,
        "recall": cand["recall"] >= base["recall"],
        "p95_latency_ms": cand["p95_latency_ms"] <= base["p95_latency_ms"] * 1.05,
        "trust_score": cand["trust_score"] >= base["trust_score"],
    }
    return {"candidate": cand, "baseline": base, "gates": gates, "approved": all(gates.values())}
```

---

## Scenario Walkthrough (Cinematic + Technical)

1. **21:14:02Z**: A maritime SIGINT event hits `signals.raw`.
2. **21:14:03Z**: Triage agent flags anomaly (confidence 0.81), opens case draft.
3. **21:14:05Z**: Enrichment + correlation agents connect vessel, comms device, and prior sanction-linked org.
4. **21:14:08Z**: Recommendation agent drafts: “Escalate to mission commander; request ISR retask.”
5. **21:14:09Z**: Policy engine blocks direct execution; moves to `PENDING_APPROVAL`.
6. **21:14:20Z**: Commander approves with edited constraints (timebox + coalition redaction).
7. **21:14:21Z**: Action package executes via authorized integration.
8. **T+4h**: Outcome labeled true positive with high mission impact.
9. **Daily learning cycle**: eval service compares v12 workflow to v13 candidate; v13 improves recall + operator trust.
10. **Next day**: Apollo canary rollout to 10% mission cells; no regressions, then full rollout.

This is how ClearGlassInc Artemis continuously improves **without** autonomous goal drift: optimization is bounded by policy, measured by evals, and released only with human authorization.

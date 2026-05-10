# ClearGlassInc Artemis — Self-Evolving Intelligence Platform (Gotham + Foundry + AIP + Apollo)

## System Architecture

### 1) Frontend (Operator/Commander Web)
- **Stack:** Next.js + TypeScript + GraphQL + WebSockets + Mapbox/Deck.gl + Monaco-based workflow editor.
- **Apps:**
  - Analyst Copilot Workspace
  - Commander Mission Console
  - Case Timeline + Entity Graph Explorer
  - AI Change Review Board (prompt/workflow/model proposals)
- **Runtime features:** streaming answer tokens, provenance panel, confidence bars, coalition-filtered views, one-click approval/reject actions.

### 2) Backend + API Gateway
- **Gateway:** Envoy + OPA sidecar (policy check before route).
- **Core services (Python/FastAPI):**
  - `intel-query-service`
  - `entity-resolution-service`
  - `agent-orchestrator-service`
  - `decision-support-service`
  - `feedback-capture-service`
  - `self-improvement-service`
  - `audit-provenance-service`
- **Protocols:** GraphQL for UI aggregation, gRPC for service-to-service, Kafka for event-driven workloads.

### 3) Data/Ontology Layer (Foundry)
- **Foundry pipelines:** batch + streaming transforms, ontology-first datasets, lineage-backed semantic models.
- **Data zones:** landing, conformed, mission, restricted compartments.
- **Storage:** lakehouse tables (Delta/Iceberg style), vector index, temporal graph projections.

### 4) Operational Layer (Gotham)
- Investigations, case management, watchlists, alerts, entity tracking, operator workflows.
- Gotham objects bind to Foundry ontology IDs for synchronized evidence and mission context.

### 5) AI Layer (AIP)
- Copilots, multi-agent workflows, evaluation harnesses, model router, prompt registry.
- Tools: ontology query, geo-temporal correlation, case creation, intel report drafting, action package generation.

### 6) Deployment + Runtime Control (Apollo)
- Progressive deployment rings (lab → staging → coalition subset → global).
- Signed artifacts, runtime attestation, remote feature flags, instant rollback.
- Per-cluster policy bundles and model allowlists.

### 7) Observability
- OpenTelemetry traces, Prometheus metrics, immutable event logs, eval dashboards.
- Mission KPIs: precision@k, recall, time-to-triage, action acceptance rate, operator trust score, latency percentiles.

---

## Data and Ontology

### Canonical Entity Types
- `Person`, `Organization`, `Asset`, `Device`, `Location`, `Event`, `Signal`, `Case`, `Mission`, `ActionPackage`, `ModelVersion`, `PromptVersion`, `WorkflowVersion`.

### Relationship Types
- `ASSOCIATED_WITH`, `OWNS`, `LOCATED_AT`, `OBSERVED_IN`, `PART_OF_CASE`, `AFFECTS_MISSION`, `DERIVED_FROM`, `TRIGGERED_BY`, `APPROVED_BY`.

### Required Metadata Columns
- `confidence_score` (0..1)
- `classification_level`
- `coalition_tags[]`
- `lineage_upstream_ids[]`
- `valid_time_start`, `valid_time_end`
- `ingest_time`
- `source_reliability`
- `policy_labels[]`
- `explanation_ref`

### Ontology-Driven Behavior
- Agents receive an **ontology slice** constrained by mission + permissions.
- Tool calls are typed against ontology schemas; outputs are rejected if schema/policy invalid.
- Temporal reasoning uses event-time windows and state transitions.

```sql
-- Example ontology-backed signal table
CREATE TABLE ontology.signal_event (
  signal_id STRING PRIMARY KEY,
  mission_id STRING,
  entity_refs ARRAY<STRING>,
  signal_type STRING,
  confidence_score DOUBLE,
  payload JSON,
  valid_time_start TIMESTAMP,
  valid_time_end TIMESTAMP,
  ingest_time TIMESTAMP,
  coalition_tags ARRAY<STRING>,
  classification_level STRING,
  lineage_upstream_ids ARRAY<STRING>
);
```

---

## AI and Agent Design

### Copilots
1. **Analyst Copilot**
   - NL query → ontology query plan → evidence bundle → draft assessment.
2. **Commander Copilot**
   - Summarizes mission status, compares response options, surfaces risk and policy constraints.

### Multi-Agent Workflow Graph
- `triage_agent` → `enrichment_agent` → `correlation_agent` → `risk_scoring_agent` → `recommendation_agent` → `human_approval_gate`.
- All agents are tool-constrained and policy-wrapped.

### Tooling Contract (AIP)
```python
from pydantic import BaseModel
from typing import Literal, List

class ToolContext(BaseModel):
    user_id: str
    mission_id: str
    clearance: str
    coalition_tags: List[str]

class ToolResult(BaseModel):
    status: Literal["ok", "denied", "error"]
    data: dict
    provenance_ids: List[str]

async def query_ontology(ctx: ToolContext, cypher: str) -> ToolResult:
    # Policy engine checks row/entity constraints before execution
    ...
```

### Approval Gates
- Any action with operational impact requires:
  - confidence threshold met
  - policy pass
  - human approval token
  - dual-authorization for high-risk compartments

---

## Self-Improvement Loop

### Signal Capture
- Operator thumbs up/down, corrections, overrides, time-to-decision, mission outcomes, false-positive/false-negative tagging.

### Improvement Pipeline
1. **Collect telemetry** → event bus.
2. **Build eval datasets** stratified by mission type + coalition domain.
3. **Run candidate changes**:
   - prompt variant
   - workflow branching logic
   - model routing policy
4. **Offline eval** (precision/recall/latency/safety).
5. **Canary online A/B** in Apollo ring.
6. **Human review board** approves promotion.
7. **Versioned release + rollback plan**.

### Drift + Rollback
- Drift detectors on label distribution, confidence calibration, retrieval relevance.
- Auto-pause + rollback when guardrails violated.

```python
class ChangeProposal(BaseModel):
    proposal_id: str
    type: Literal["prompt", "workflow", "router", "heuristic"]
    current_version: str
    candidate_version: str
    expected_gain: float
    safety_risk: float
    eval_report_uri: str
    requires_human_approval: bool = True

async def promote_change(proposal: ChangeProposal, approver: str):
    assert proposal.requires_human_approval
    # write immutable audit record
    # call Apollo deployment API for ring promotion
    # attach rollback pointer
```

---

## Full-Stack Implementation Blueprint

### Web UI (TypeScript)
```ts
// app/api/copilot/route.ts
export async function POST(req: Request) {
  const body = await req.json();
  const res = await fetch(process.env.GATEWAY_URL + "/copilot/query", {
    method: "POST",
    headers: { "content-type": "application/json", "authorization": req.headers.get("authorization") ?? "" },
    body: JSON.stringify(body)
  });
  return new Response(res.body, { status: res.status });
}
```

### Backend Service (Python/FastAPI)
```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel

app = FastAPI()

class CopilotRequest(BaseModel):
    mission_id: str
    query: str

@app.post("/copilot/query")
async def copilot_query(req: CopilotRequest, principal=Depends(...)):
    # 1) policy check
    # 2) plan tools
    # 3) execute agent graph
    # 4) stream response + provenance
    return {"answer": "...", "provenance": ["ev_123", "case_88"]}
```

### Event Bus Contract
```json
{
  "event_type": "operator_feedback.recorded",
  "event_id": "uuid",
  "timestamp": "2026-05-10T12:00:00Z",
  "mission_id": "m-42",
  "payload": {
    "artifact_id": "intel-report-998",
    "rating": "downvote",
    "reason": "false association",
    "correction": {"entity_id": "person-7", "remove_link": "org-3"}
  }
}
```

### Workflow State Machine
```python
from enum import Enum

class IntelState(str, Enum):
    INGESTED = "ingested"
    TRIAGED = "triaged"
    ENRICHED = "enriched"
    CORRELATED = "correlated"
    RECOMMENDED = "recommended"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTED = "executed"
    CLOSED = "closed"
```

### Policy-as-Code (OPA/Rego)
```rego
package artemis.authz

default allow = false

allow {
  input.user.clearance >= input.resource.classification
  input.user.coalition_tags[_] == input.resource.coalition_tags[_]
  not input.resource.compartment in input.user.denied_compartments
}
```

---

## Security and Governance
- Zero-trust service identity (mTLS, SPIFFE/SPIRE).
- Need-to-know enforcement at API, query, and entity edges.
- Compartment + coalition boundary checks on every retrieval.
- Immutable provenance ledger for data, prompts, model versions, and actions.
- Model governance:
  - approved model registry
  - risk tiering
  - red-team test suite
  - explainability minimums
- Prompt governance:
  - signed prompt templates
  - diff-based approvals
  - automatic prompt injection scanning

---

## Code Examples (Self-Upgrade Eval Pipeline)

```python
async def run_eval_pipeline(dataset_id: str, candidate_router: str):
    baseline = await evaluate_router("router_v12", dataset_id)
    candidate = await evaluate_router(candidate_router, dataset_id)

    delta_precision = candidate["precision"] - baseline["precision"]
    delta_latency = candidate["p95_latency_ms"] - baseline["p95_latency_ms"]
    safety_violations = candidate["policy_violations"]

    decision = {
      "promote": delta_precision >= 0.03 and delta_latency <= 40 and safety_violations == 0,
      "reason": {
        "delta_precision": delta_precision,
        "delta_latency": delta_latency,
        "safety_violations": safety_violations,
      }
    }
    return decision
```

```python
async def process_feedback_event(evt: dict):
    # Normalize operator corrections into supervised eval examples
    example = {
      "input_query": evt["payload"].get("query", ""),
      "expected_entities": evt["payload"].get("expected_entities", []),
      "bad_links": evt["payload"].get("bad_links", []),
      "mission_id": evt["mission_id"],
    }
    await write_eval_example(example)
```

---

## Scenario Walkthrough (Cinematic + Technical)

1. **Live event ingress:** UAV ISR feed + SIGINT metadata enters Foundry streaming pipeline; entity resolver links a device to an active watchlist case.
2. **Automated triage:** Triage agent scores anomaly 0.91, correlation agent finds matching route pattern over last 14 days.
3. **Recommendation:** Recommendation agent produces 3 response options with risk, confidence, and required approvals.
4. **Human decision:** Commander rejects Option A, approves Option B with edited geographic boundary.
5. **Execution:** Gotham case updated, action package dispatched, all steps logged with provenance IDs.
6. **Learning loop:** rejection/approval + boundary correction becomes eval signal; workflow proposes tighter geofence heuristic.
7. **Governed upgrade:** candidate heuristic passes offline eval, then 10% canary in Apollo ring, then review board approval for full rollout.
8. **Rollback readiness:** if false positives rise > 2% for 30 minutes, Apollo auto-rolls back to previous workflow version.

Result: **ClearGlassInc Artemis** improves continuously while keeping humans in command and every change auditable, reversible, and policy-compliant.

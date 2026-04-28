# ClearGlassInc Artemis — Self-Evolving AI Intelligence Platform (Gotham + Foundry + AIP + Apollo)

## System Architecture

### 1) Mission and Design Constraints
ClearGlassInc Artemis is designed for secure, coalition-aware, multi-domain intelligence operations where latency, explainability, and auditability are mandatory. The platform fuses live + historical data, reasons in real time, proposes workflow/model/prompt improvements, and only promotes those changes through explicit human-approved guardrails.

### 2) Platform Mapping (Palantir-Precise)
- **Gotham**: Operational intelligence, investigations, entity tracking, link/timeline analysis, case management.
- **Foundry**: Data integration, data products, Ontology, pipeline orchestration, lineage, application logic backing objects.
- **AIP**: AI copilots, agent runtime, tool contracts, eval harnesses, model routing, workflow automation.
- **Apollo**: Secure delivery, staged rollout, runtime policy updates, drift-triggered rollback.

### 3) End-to-End Topology
```text
[Web UI (React/TypeScript) + Mission Ops Console + Explainability Panels]
                    |
        [API Gateway + mTLS + OIDC + OPA PDP + Rate Limits]
                    |
[Backend Services (Python/FastAPI + Async Workers + State Machines)]
  |- intelligence-api
  |- case-workflow-service
  |- ontology-query-service
  |- feedback-eval-service
  |- policy-decision-service
  |- inference-router-service
                    |
          [Event Bus: Kafka (topics) + Schema Registry]
                    |
   -----------------------------------------------------------
   |                        Data Plane                         |
   |  Foundry Pipelines + Ontology + Lakehouse + Features     |
   |  Vector Index + Graph Store + Search + Temporal Tables   |
   -----------------------------------------------------------
                    |
         [AIP Agent Runtime + Copilots + Eval Registry]
                    |
      [Gotham Case Graph + Investigations + Mission Timelines]
                    |
 [Apollo: deployment rings, policy bundles, health gates, rollback]
```

### 4) Layered Responsibilities
- **Frontend layer**: mission dashboard, triage queues, AI copilot chat, action approval queue, evidence provenance explorer.
- **Backend layer**: deterministic business logic, workflow state machine, command execution APIs, decision orchestration.
- **Data layer**: streaming ingest + batch harmonization + searchable intel products + feature store.
- **Ontology layer**: operational entities/relationships with confidence, temporal state, lineage, permissions.
- **AI orchestration layer**: agent graph, tool invocation policies, model routing by task/security zone.
- **Policy layer**: RBAC + ABAC + need-to-know + coalition/compartment boundaries.
- **Observability layer**: metrics, traces, policy decision logs, eval dashboards, immutable audit chain.
- **Deployment layer**: Apollo progressive promotion, ring-based canary, auto rollback.

---

## Data and Ontology

### 1) Ontology Model (Foundry Ontology Objects)
```yaml
Entity:
  Mission:
    keys: [mission_id]
    attrs: [name, theater, priority, start_ts, end_ts, classification]

  Signal:
    keys: [signal_id]
    attrs: [source_type, source_id, observed_at, ingested_at, confidence, mission_id]

  EntityNode:
    keys: [entity_id]
    attrs: [entity_type, canonical_name, aliases, confidence, first_seen, last_seen]

  Event:
    keys: [event_id]
    attrs: [event_type, event_ts, geohash, severity, confidence, mission_id]

  IntelAssessment:
    keys: [assessment_id]
    attrs: [summary, analytic_judgment, confidence, model_version, analyst_id]

  Recommendation:
    keys: [recommendation_id]
    attrs: [action_type, rationale, risk, urgency, status, mission_id]

  ActionPackage:
    keys: [action_pkg_id]
    attrs: [recommended_by, approvals_required, approved_by, executed_at, status]

  FeedbackRecord:
    keys: [feedback_id]
    attrs: [operator_id, disposition, correction, outcome_label, created_at]

Relationship:
  - SIGNAL_SUPPORTS_EVENT (Signal -> Event)
  - EVENT_INVOLVES_ENTITY (Event -> EntityNode)
  - ASSESSMENT_REFERENCES_EVENT (IntelAssessment -> Event)
  - RECOMMENDS_ACTION (Recommendation -> ActionPackage)
  - FEEDBACK_ON_RECOMMENDATION (FeedbackRecord -> Recommendation)
  - MISSION_CONTAINS_EVENT (Mission -> Event)
```

### 2) Confidence, Temporal State, Lineage
- **Confidence**: every extracted/derived object has calibrated confidence and supporting evidence IDs.
- **Temporal**: bitemporal fields for mission truth vs system ingestion timeline.
- **Lineage**: pipeline ID, transform hash, source dataset references, model/prompt/workflow versions.

```sql
CREATE TABLE intel_event_fact (
  event_id TEXT PRIMARY KEY,
  mission_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  event_ts TIMESTAMPTZ NOT NULL,
  observed_at TIMESTAMPTZ NOT NULL,
  ingested_at TIMESTAMPTZ NOT NULL,
  confidence NUMERIC NOT NULL,
  evidence_refs JSONB NOT NULL,
  valid_from TIMESTAMPTZ,
  valid_to TIMESTAMPTZ,
  lineage_ref TEXT NOT NULL,
  classification TEXT NOT NULL,
  releasability JSONB NOT NULL,
  compartment_tags JSONB NOT NULL
);
```

### 3) Permissions Model in Data
- Row/column/entity-level policy annotations attached at ingest.
- Dynamic projection for coalition partners (field masking, entity suppression, confidence degradation bands when required).
- Ontology query API enforces policy before result materialization.

---

## AI and Agent Design

### 1) Copilots
- **Analyst Copilot**: “what changed?”, entity/event correlation explanation, confidence decomposition.
- **Commander Copilot**: recommended response options, mission impact simulation, reversibility analysis.
- **Policy Copilot**: why action is blocked/allowed, what permissions are missing.

### 2) Multi-Agent Workflow Graph
```text
IngestAgent -> NormalizeAgent -> TriageAgent -> EnrichmentAgent -> CorrelationAgent
             -> SummarizationAgent -> RecommendationAgent -> ApprovalGateAgent -> ExecuteAgent
```

### 3) Tool-Using Agent Contracts
Each tool has typed input/output schema, latency budget, and policy classification.

```python
# services/agents/tool_contracts.py
from pydantic import BaseModel, Field
from typing import Literal, List

class QueryOntologyIn(BaseModel):
    mission_id: str
    cypher: str
    max_rows: int = Field(default=200, le=2000)

class QueryOntologyOut(BaseModel):
    rows: list[dict]
    lineage_refs: List[str]

class OpenCaseIn(BaseModel):
    mission_id: str
    title: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    evidence_ids: list[str]

class OpenCaseOut(BaseModel):
    case_id: str
    status: Literal["OPENED"]
```

### 4) Approval Gates for Operationally Significant Actions
- Any action with real-world operational impact transitions to `PENDING_HUMAN_APPROVAL`.
- Commander/authorized role must approve with reason code.
- Agent cannot bypass policy or approval state machine.

---

## Self-Improvement Loop

### 1) Feedback Signals Captured
- Operator edits (what AI suggested vs what human changed).
- Approval outcomes (approved/rejected/overridden).
- Mission outcome labels (success, false positive, delayed detection).
- Query usage patterns + abandoned recommendations.
- Latency and trust telemetry by mission profile.

### 2) Controlled Improvement Lifecycle
```text
Runtime events -> feature extraction -> eval dataset builder -> offline evals
-> candidate prompt/workflow/router proposal -> shadow deployment
-> human review board -> Apollo canary ring -> full promotion or rollback
```

### 3) Versioning and Change Control
- `prompt_version`, `workflow_version`, `router_version`, `policy_bundle_version` captured per decision.
- Candidate changes are immutable artifacts with diff metadata and signer identity.
- Safe rollback target always available (N-1 stable ring).

### 4) Drift Detection
- Statistical drift monitors on event type distributions, confidence calibration, precision/recall by theater.
- Alert thresholds trigger automatic freeze of self-improvement promotions.

### 5) Promotion Guardrails
```python
# services/evals/gating.py
from dataclasses import dataclass

@dataclass
class GateMetrics:
    precision: float
    recall: float
    p95_latency_ms: int
    operator_trust: float
    mission_success_rate: float


def can_promote(candidate: GateMetrics, baseline: GateMetrics) -> tuple[bool, str]:
    if candidate.precision < baseline.precision - 0.01:
        return False, "precision_regression"
    if candidate.recall < baseline.recall - 0.02:
        return False, "recall_regression"
    if candidate.p95_latency_ms > int(baseline.p95_latency_ms * 1.1):
        return False, "latency_regression"
    if candidate.operator_trust < baseline.operator_trust:
        return False, "trust_regression"
    if candidate.mission_success_rate < baseline.mission_success_rate:
        return False, "mission_impact_regression"
    return True, "eligible_for_human_review"
```

---

## Full-Stack Implementation

### 1) Web UI (TypeScript)
```ts
// ui/src/features/recommendations/approveRecommendation.ts
export async function approveRecommendation(
  recommendationId: string,
  decision: "APPROVE" | "REJECT",
  reason: string,
) {
  const res = await fetch(`/api/v1/recommendations/${recommendationId}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, reason }),
  });

  if (!res.ok) throw new Error(`Approval request failed: ${res.status}`);
  return res.json();
}
```

### 2) API Gateway + Backend (Python/FastAPI)
```python
# services/intelligence_api/main.py
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from services.policy.auth import authorize
from services.orchestrator import run_intel_query

app = FastAPI(title="ClearGlassInc Artemis Intelligence API")

class IntelQuery(BaseModel):
    mission_id: str
    question: str
    context_filters: dict = {}

@app.post("/v1/intel/query")
async def intel_query(req: IntelQuery, user=Depends(authorize)):
    if req.mission_id not in user["mission_scopes"]:
        raise HTTPException(status_code=403, detail="Mission scope denied")
    return await run_intel_query(req.model_dump(), user)
```

### 3) Event Streaming + Handler
```python
# services/feedback_eval/consumer.py
import json
from aiokafka import AIOKafkaConsumer

async def consume_feedback(loop_handler):
    consumer = AIOKafkaConsumer(
        "artemis.feedback.v1",
        bootstrap_servers="kafka:9092",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    await consumer.start()
    try:
        async for msg in consumer:
            await loop_handler(msg.value)
    finally:
        await consumer.stop()
```

### 4) Ontology-Driven Query Service
```python
# services/ontology/query_service.py
async def fetch_recent_high_risk_events(db, mission_id: str, limit: int = 50):
    sql = """
    SELECT event_id, event_ts, event_type, confidence, evidence_refs
    FROM intel_event_fact
    WHERE mission_id = :mission_id
      AND confidence >= 0.75
      AND event_ts >= NOW() - INTERVAL '24 hours'
    ORDER BY event_ts DESC
    LIMIT :limit
    """
    return await db.fetch_all(sql, values={"mission_id": mission_id, "limit": limit})
```

### 5) Model Router / Inference Layer
```python
# services/inference/router.py
TASK_ROUTE = {
    "summarization": ["model-secure-small", "model-secure-large"],
    "entity_resolution": ["model-ner-precision"],
    "recommendation": ["model-reasoning-large", "model-fallback"],
}


def route_model(task: str, classification: str, latency_budget_ms: int) -> str:
    candidates = TASK_ROUTE.get(task, ["model-fallback"])
    if classification in {"SECRET", "TOP_SECRET"}:
        return candidates[0]  # enclave-first model endpoint
    return candidates[0] if latency_budget_ms < 900 else candidates[-1]
```

### 6) Workflow State Machine
```python
# services/workflow/state_machine.py
from enum import Enum

class DecisionState(str, Enum):
    PROPOSED = "PROPOSED"
    PENDING_HUMAN_APPROVAL = "PENDING_HUMAN_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"

TRANSITIONS = {
    DecisionState.PROPOSED: {DecisionState.PENDING_HUMAN_APPROVAL},
    DecisionState.PENDING_HUMAN_APPROVAL: {DecisionState.APPROVED, DecisionState.REJECTED},
    DecisionState.APPROVED: {DecisionState.EXECUTED},
    DecisionState.REJECTED: set(),
    DecisionState.EXECUTED: set(),
}
```

### 7) Observability and Eval Dashboards
- **Metrics**: precision, recall, latency p95/p99, approval acceptance rate, override ratio, mission outcome uplift.
- **Tracing**: per request span across gateway -> agents -> tools -> policy checks.
- **Dashboards**: operator trust trend, drift monitor, release ring health, policy deny reasons.

---

## Security and Governance

### 1) Need-to-Know + Compartmentalization
- ABAC attributes: mission, clearance, coalition, compartment tags, purpose-of-use.
- RBAC role checks for operational actions.
- Entity/row/column filters before query result return.

### 2) Zero-Trust Execution
- mTLS everywhere, workload identity, signed service-to-service JWT.
- Least-privilege short-lived credentials for tool calls.
- Runtime attestation checks for enclave-bound inference workloads.

### 3) Immutable Provenance + Audit
```sql
CREATE TABLE immutable_audit_log (
  audit_id TEXT PRIMARY KEY,
  prev_hash TEXT,
  curr_hash TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  action_type TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  policy_decision JSONB NOT NULL,
  prompt_version TEXT,
  workflow_version TEXT,
  model_route_version TEXT,
  created_at TIMESTAMPTZ NOT NULL
);
```

### 4) Policy-as-Code (OPA/Rego)
```rego
package artemis.authz

default allow = false

allow {
  input.user.clearance >= input.resource.classification
  input.user.mission_id == input.resource.mission_id
  some tag
  input.resource.need_to_know_tags[tag]
  input.user.entitlements[tag]
}

allow_operational_action {
  allow
  input.action.requires_commander == true
  input.user.roles[_] == "mission_commander"
}
```

### 5) Governance of Models/Prompts/Workflows
- Change proposals generated by eval service only.
- Human review board approval required (Ops + Security + Mission).
- Apollo rollout policy: 5% shadow -> 10% canary -> 50% ring -> 100% stable.

---

## Code Examples

### 1) Agent Orchestrator (Python)
```python
# services/agents/orchestrator.py
from services.inference.router import route_model
from services.policy.engine import authorize_tool

async def run_triage_flow(ctx, tools, llm_client, user):
    model = route_model(task="recommendation", classification=ctx["classification"], latency_budget_ms=1200)

    await authorize_tool(user=user, tool_name="query_ontology", mission_id=ctx["mission_id"])
    events = await tools.query_ontology(mission_id=ctx["mission_id"], window_hours=24)

    prompt = {
        "task": "triage_and_recommend",
        "mission_context": ctx,
        "events": events,
    }
    recommendation = await llm_client.generate(model=model, prompt=prompt)

    recommendation["state"] = "PENDING_HUMAN_APPROVAL"
    return recommendation
```

### 2) Policy Check Wrapper
```python
# services/policy/engine.py
from fastapi import HTTPException

async def authorize_tool(user: dict, tool_name: str, mission_id: str):
    if mission_id not in user.get("mission_scopes", []):
        raise HTTPException(403, f"Tool {tool_name}: mission scope denied")
    if tool_name in {"open_case", "execute_action"} and "mission_commander" not in user.get("roles", []):
        raise HTTPException(403, f"Tool {tool_name}: commander role required")
```

### 3) Eval Dataset Builder
```python
# services/evals/dataset_builder.py
from typing import Iterable

def build_eval_rows(events: Iterable[dict]) -> list[dict]:
    rows = []
    for e in events:
        rows.append({
            "query": e["prompt_input"],
            "ai_output": e["model_output"],
            "human_decision": e.get("operator_decision"),
            "outcome_label": e.get("mission_outcome"),
            "prompt_version": e["prompt_version"],
            "workflow_version": e["workflow_version"],
            "model_route_version": e["model_route_version"],
        })
    return rows
```

### 4) Workflow Upgrade Proposal Object
```python
# services/improvement/proposals.py
from pydantic import BaseModel

class UpgradeProposal(BaseModel):
    proposal_id: str
    prompt_diff: dict
    workflow_diff: dict
    router_diff: dict
    eval_summary: dict
    risk_notes: list[str]
    approval_state: str = "PENDING_REVIEW"
```

---

## Scenario Walkthrough

### “Red Horizon” Live Event (End-to-End)
1. **T+00s — Event Ingest**: A maritime SIGINT + imagery burst is ingested into Foundry streaming datasets with coalition tagging and mission `M-2041`.
2. **T+03s — Triage**: TriageAgent flags anomalous vessel behavior (confidence 0.82), links entities in Gotham case graph, and opens/updates `Case C-9012`.
3. **T+06s — Correlation**: CorrelationAgent fuses historical shipping patterns, sanctions watchlists, and recent comms metadata; risk elevates to HIGH.
4. **T+09s — Recommendation**: RecommendationAgent proposes `ActionPackage AP-551`: ISR retask + legal review + partner advisory draft.
5. **T+12s — Approval Gate**: Commander approves ISR retask, rejects partner advisory due to releasability conflict (policy copilot explains deny path).
6. **T+16s — Execution**: ExecuteAgent dispatches approved ISR retask via integration adapter; all policy decisions are hash-linked in immutable audit log.
7. **T+6h — Outcome Capture**: Operation confirms true positive; operator feedback notes the advisory recommendation was over-eager under low corroboration depth.
8. **T+24h — Self-Improvement Pipeline**:
   - Feedback/evidence joins eval corpus.
   - Candidate prompt update penalizes advisory recommendation when corroboration depth < 2 and confidence < 0.85.
   - Offline eval shows improved precision (+2.8%), neutral recall, stable latency.
   - Review board approves proposal.
9. **T+30h — Apollo Rollout**: Candidate deploys to 10% canary ring; no regressions after observation window.
10. **T+36h — Promotion**: Apollo promotes to stable. Future recommendations show fewer false partner advisories with preserved mission success.

Result: ClearGlassInc Artemis continuously improves at machine speed while remaining human-governed, policy-bounded, and fully auditable.

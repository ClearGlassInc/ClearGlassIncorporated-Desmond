# ClearGlassInc Artemis — Self-Evolving Intelligence Platform Blueprint

## System Architecture

### 1) Platform topology (Gotham + Foundry + AIP + Apollo)

```text
[Sensors/Feeds/Partner APIs/SIGINT HUMINT OSINT ERP CRM Billing]
                 |
          [Ingestion Gateway]
      (schema registry, trust scoring, PKI)
                 |
      [Streaming Bus: Kafka/Pulsar]
        |                 |
[Hot Path Triage]    [Cold Path Lakehouse]
(Flink/Spark Str)    (Foundry datasets)
        |                 |
    [Foundry Ontology + Data Products + Pipelines]
                 |
  [AIP Agent Runtime + Copilots + Eval Engine + Model Router]
                 |
   [Mission APIs / Case Services / Recommendation Services]
                 |
 [Gotham Case Mgmt + Link Analysis + Investigative Timelines]
                 |
[Apollo Deployment Rings + Runtime Policy + Rollback Controller]
                 |
[Operator UI: Analyst Console + Commander COP + Governance Console]
```

### 2) Layer-by-layer design
- **Frontend**: TypeScript React + GraphQL subscriptions for live incident streams, approval inbox, ontology graph explorer.
- **Backend**: Python microservices (FastAPI + asyncio) for deterministic mission logic and AI orchestration.
- **Data**: Foundry as source-of-truth data plane (batch + streaming transforms, lineage, ontology).
- **Ontology**: Entities + links + confidence + bitemporal facts + coalition partitions.
- **AI Orchestration**: AIP copilots, tool-using agents, prompt/workflow registries, eval gates.
- **Policy**: ABAC + RBAC + mission context constraints via policy-as-code.
- **Observability**: OTel traces, model telemetry, eval dashboards, immutable audit stream.
- **Deployment**: Apollo rings (dev→staging→mission-canary→prod), health SLO gates, automated rollback.

---

## Data and Ontology

### 1) Ontology model (Foundry Ontology)

```yaml
entities:
  Mission:
    fields: [mission_id, name, priority, status, coalition_scope, classification]
  Actor:
    fields: [actor_id, actor_type, aliases, confidence, country, watchlist_status]
  Event:
    fields: [event_id, ts_event, ts_ingest, source, event_type, raw_payload_ref, confidence]
  Asset:
    fields: [asset_id, asset_type, owner, location, criticality, lifecycle_state]
  Alert:
    fields: [alert_id, rule_id, severity, score, rationale, state]
  Case:
    fields: [case_id, mission_id, opened_at, status, owner, sla_due_at]
  Recommendation:
    fields: [rec_id, case_id, action_type, expected_impact, risk_score, status]
  ApprovalDecision:
    fields: [decision_id, rec_id, approver, decision, reason, decided_at]
  FeedbackSignal:
    fields: [feedback_id, source, label, correction, confidence_delta, outcome]

relationships:
  - EVENT_OBSERVED_ACTOR: Event -> Actor
  - EVENT_TARGETED_ASSET: Event -> Asset
  - EVENT_TRIGGERED_ALERT: Event -> Alert
  - ALERT_ESCALATED_TO_CASE: Alert -> Case
  - CASE_HAS_RECOMMENDATION: Case -> Recommendation
  - RECOMMENDATION_REQUIRES_DECISION: Recommendation -> ApprovalDecision
  - FEEDBACK_ON_RECOMMENDATION: FeedbackSignal -> Recommendation
  - MISSION_CONTAINS_CASE: Mission -> Case
```

### 2) Bitemporal + lineage + confidence
```sql
CREATE TABLE ontology_event_fact (
  fact_id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL,
  predicate TEXT NOT NULL,
  object_id TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  valid_from TIMESTAMPTZ NOT NULL,
  valid_to TIMESTAMPTZ,
  observed_at TIMESTAMPTZ NOT NULL,
  ingested_at TIMESTAMPTZ NOT NULL,
  source_system TEXT NOT NULL,
  source_record_id TEXT NOT NULL,
  transform_version TEXT NOT NULL,
  lineage_hash TEXT NOT NULL,
  classification TEXT NOT NULL,
  coalition_scope TEXT[] NOT NULL
);
```

### 3) How ontology drives behavior
- Human workflow: analysts pivot from `Event -> Alert -> Case -> Recommendation` with full provenance.
- AI workflow: agent tools receive ontology-constrained query views filtered by mission scope and clearance.
- Every recommendation must cite supporting ontology edges + confidence + lineage.

---

## AI and Agent Design

### 1) Copilot roles (AIP)
- **Analyst Copilot**: explain anomalies, suggest triage paths, generate evidence-backed briefs.
- **Commander Copilot**: compare COAs (courses of action), mission impact simulation, risk tradeoffs.
- **Governance Copilot**: explains policy blocks, required approvals, and compliance rationale.

### 2) Multi-agent orchestration
```text
IntakeAgent
  -> TriageAgent
  -> EnrichmentAgent
  -> CorrelationAgent
  -> RecommenderAgent
  -> PolicyGateAgent
  -> ApprovalAgent
  -> ExecutionAgent
  -> AfterActionLearningAgent
```

### 3) Tool-using agents (strict contracts)
```python
from pydantic import BaseModel

class QueryOntologyInput(BaseModel):
    mission_id: str
    entity_type: str
    filters: dict

class CreateCaseInput(BaseModel):
    mission_id: str
    alert_id: str
    reason: str

class ProposeActionInput(BaseModel):
    case_id: str
    action_type: str
    evidence_ids: list[str]

ALLOWED_TOOLS = {
    "query_ontology": QueryOntologyInput,
    "create_case": CreateCaseInput,
    "propose_action": ProposeActionInput,
    "request_approval": dict,
}
```

### 4) Approval gates
- Operationally significant actions (`asset quarantine`, `task force dispatch`, `external notification`) are **never auto-executed**.
- Required: policy evaluation + human approval + mission audit record.

---

## Self-Improvement Loop

### 1) Signal collection
- Operator edits, rejected recommendations, accepted recommendations, SLA outcomes.
- Query logs (intent, context window, tool usage, hallucination reports).
- Mission KPIs (precision, recall, false positive burden, response latency, trust rating).

### 2) Improvement pipeline
```text
feedback_stream
  -> label_normalizer
  -> eval_set_builder
  -> candidate_generator(prompt/workflow/router)
  -> offline_eval_harness
  -> shadow_deploy
  -> human change board approval
  -> Apollo canary rollout
  -> full rollout or rollback
```

### 3) Guardrails + drift detection
```python
SAFETY_GUARDS = {
    "min_precision_delta": -0.01,
    "min_recall_delta": -0.02,
    "max_p95_latency_delta_ms": 120,
    "operator_trust_delta": 0.0,
    "policy_violation_count": 0,
}

def eligible_for_promotion(metrics: dict, baseline: dict) -> bool:
    return (
        metrics["precision"] - baseline["precision"] >= SAFETY_GUARDS["min_precision_delta"]
        and metrics["recall"] - baseline["recall"] >= SAFETY_GUARDS["min_recall_delta"]
        and metrics["p95_latency_ms"] - baseline["p95_latency_ms"] <= SAFETY_GUARDS["max_p95_latency_delta_ms"]
        and metrics["operator_trust"] - baseline["operator_trust"] >= SAFETY_GUARDS["operator_trust_delta"]
        and metrics["policy_violations"] <= SAFETY_GUARDS["policy_violation_count"]
    )
```

### 4) Versioning and rollback
- Version all prompts/workflows/router policies as immutable artifacts (`prompt:vX`, `workflow:vY`, `router:vZ`).
- Apollo maintains deployment manifests with one-click rollback + automated rollback triggers.

---

## Full-Stack Implementation

### 1) Web UI (TypeScript)
```tsx
// web/src/features/cases/ApprovalQueue.tsx
export function ApprovalQueue({ items, onDecision }) {
  return (
    <section>
      <h2>Operational Approvals</h2>
      {items.map((it) => (
        <article key={it.recId}>
          <h3>{it.actionType}</h3>
          <p>Risk: {it.riskScore}</p>
          <button onClick={() => onDecision(it.recId, "APPROVE")}>Approve</button>
          <button onClick={() => onDecision(it.recId, "REJECT")}>Reject</button>
        </article>
      ))}
    </section>
  );
}
```

### 2) API gateway + backend services (Python)
```python
# api/main.py
from fastapi import FastAPI, Depends
from services.policy import authorize
from services.case_service import create_case_from_alert

app = FastAPI(title="ClearGlassInc Artemis Mission API")

@app.post("/v1/alerts/{alert_id}/cases")
async def open_case(alert_id: str, user=Depends(authorize("case:create"))):
    return await create_case_from_alert(alert_id=alert_id, user=user)

@app.post("/v1/recommendations/{rec_id}/decision")
async def decide(rec_id: str, decision: dict, user=Depends(authorize("approval:decide"))):
    # decision = {"value":"APPROVE|REJECT", "reason":"..."}
    return {"rec_id": rec_id, "status": "recorded", "by": user["id"]}
```

### 3) Event bus handler
```python
# services/triage_consumer.py
import json
from aiokafka import AIOKafkaConsumer

async def consume_events():
    consumer = AIOKafkaConsumer("mission.events", bootstrap_servers="kafka:9092")
    await consumer.start()
    try:
      async for msg in consumer:
          event = json.loads(msg.value)
          # score, correlate, emit alert candidate
          # write provenance + telemetry
    finally:
      await consumer.stop()
```

### 4) Search/RAG layer
```python
# services/retrieval.py
async def retrieve_case_context(case_id: str, user_scope: dict) -> dict:
    graph_hits = await query_graph(case_id=case_id, scope=user_scope)
    vector_hits = await query_vector(index="intel-briefs", query=case_id, scope=user_scope)
    return {"graph": graph_hits, "vector": vector_hits}
```

### 5) Model router
```python
# services/model_router.py
ROUTES = {
    "summarization": ["gpt-4.1-mini", "fallback-local-llm"],
    "high_risk_reasoning": ["gpt-4.1", "fallback-gpt-4.1-mini"],
}

def route_task(task_type: str, latency_budget_ms: int, classification: str) -> str:
    candidates = ROUTES[task_type]
    if classification in {"TOP_SECRET", "COALITION_RESTRICTED"}:
        return candidates[0]  # approved hardened path
    return candidates[0] if latency_budget_ms > 400 else candidates[-1]
```

### 6) Workflow state machine
```python
# services/workflow.py
from enum import Enum

class CaseState(str, Enum):
    NEW = "NEW"
    TRIAGED = "TRIAGED"
    RECOMMENDED = "RECOMMENDED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    EXECUTED = "EXECUTED"
    CLOSED = "CLOSED"

ALLOWED = {
    CaseState.NEW: {CaseState.TRIAGED},
    CaseState.TRIAGED: {CaseState.RECOMMENDED},
    CaseState.RECOMMENDED: {CaseState.PENDING_APPROVAL},
    CaseState.PENDING_APPROVAL: {CaseState.EXECUTED, CaseState.CLOSED},
    CaseState.EXECUTED: {CaseState.CLOSED},
}
```

### 7) Evals pipeline
```sql
CREATE TABLE eval_run (
  eval_run_id TEXT PRIMARY KEY,
  candidate_version TEXT NOT NULL,
  baseline_version TEXT NOT NULL,
  dataset_snapshot_id TEXT NOT NULL,
  precision DOUBLE PRECISION,
  recall DOUBLE PRECISION,
  f1 DOUBLE PRECISION,
  p95_latency_ms DOUBLE PRECISION,
  trust_score DOUBLE PRECISION,
  policy_violations INTEGER,
  created_at TIMESTAMPTZ NOT NULL
);
```

---

## Security and Governance

### 1) Need-to-know and coalition controls
- AuthN: enterprise IdP + hardware-backed MFA + short-lived tokens.
- AuthZ: ABAC (`mission`, `classification`, `compartment`, `role`) + RBAC overlays.
- Data enforcement: row/column/entity-level filters in query services and Foundry policy layers.

### 2) Zero-trust execution
- Every service call mTLS + SPIFFE identities.
- Tool execution sandboxed with signed tool manifests.
- No direct model-to-database access; all access via policy-enforced tool layer.

### 3) Model/prompt governance
- Prompt registry with approvals, diff history, and deprecation windows.
- Model allowlist by mission classification.
- Policy-as-code (OPA/Rego) checks before tool invocation.

### 4) Immutable provenance and audit
- Append-only audit stream (WORM storage).
- Every recommendation includes: `evidence_ids`, `lineage_hash`, `policy_decision_id`, `model_version`.

---

## Code Examples

```python
# services/policy.py
from fastapi import HTTPException

def authorize(permission: str):
    async def _dep(user=...):
        # evaluate ABAC/RBAC against mission context
        allowed = True
        if not allowed:
            raise HTTPException(status_code=403, detail=f"Denied: {permission}")
        return {"id": "operator-123", "perms": [permission]}
    return _dep
```

```python
# services/self_improvement.py
async def propose_upgrade(candidate: dict, eval_metrics: dict, baseline: dict):
    if not eligible_for_promotion(eval_metrics, baseline):
        return {"status": "rejected", "reason": "guardrails"}
    return {
      "status": "pending_human_review",
      "candidate": candidate,
      "required_signoffs": ["AI Governance Lead", "Mission Owner"],
    }
```

```python
# services/feedback_ingest.py
async def ingest_feedback(feedback: dict):
    # feedback = {rec_id, operator_id, label, correction, outcome}
    # write feedback event, recalculate trust metrics, enqueue eval refresh
    return {"ok": True, "queued_eval_refresh": True}
```

---

## Scenario Walkthrough

1. **Live event arrival**: a coalition sensor emits anomalous movement; stream lands on `mission.events` with classification and mission tags.
2. **Triage**: TriageAgent scores severity 0.91, links to known Actor and critical Asset in ontology.
3. **Enrichment/correlation**: EnrichmentAgent pulls historical pattern matches + Gotham case links.
4. **Recommendation**: RecommenderAgent proposes `ACTION: increase surveillance + create priority case`, cites 7 ontology evidence edges.
5. **Policy gate**: PolicyGateAgent validates coalition sharing boundary and need-to-know.
6. **Human decision**: Commander approves surveillance increase, rejects escalation action due to collateral risk.
7. **Execution**: approved action is executed, case status transitions to `EXECUTED`.
8. **Outcome feedback**: after 6 hours, mission result indicates true positive, but escalation rejection also validated.
9. **Learning loop**: feedback updates eval dataset; candidate prompt adjusts escalation threshold explanation format.
10. **Safe promotion**: candidate passes offline + shadow evals, then awaits governance signoff; Apollo canaries to 10% ring.
11. **Continuous improvement**: metrics improve precision + operator trust while policy violations remain zero.

This yields a platform that improves at machine speed while preserving explicit human authority, policy compliance, and mission assurance for **ClearGlassInc Artemis**.

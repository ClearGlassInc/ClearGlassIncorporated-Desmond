# ClearGlassInc Artemis — Self-Evolving Intelligence Platform (Palantir Gotham + Foundry + AIP + Apollo)

## 1) System Architecture

### 1.1 Mission Profile
ClearGlassInc Artemis is a secure, coalition-aware, low-latency intelligence platform that fuses live and historical data, supports operational decisions, and safely improves AI behavior through human-approved upgrades.

### 1.2 Layered Architecture (Full Stack)
```text
┌────────────────────────────────────────────────────────────────────┐
│ Web UI (React/Next.js) + Mission Console + Analyst Copilot        │
├────────────────────────────────────────────────────────────────────┤
│ API Gateway (FastAPI/Envoy) + GraphQL + WebSocket event streams   │
├────────────────────────────────────────────────────────────────────┤
│ Backend Microservices (Python)                                     │
│  - Case Service  - Entity Service  - Alert Service  - Report Svc  │
│  - Feedback Service - Eval Service - Policy Decision Service       │
├────────────────────────────────────────────────────────────────────┤
│ Event/Streaming Layer (Kafka/PubSub + CDC + stream processors)     │
├────────────────────────────────────────────────────────────────────┤
│ Foundry Data Layer + Ontology + Pipeline Builder + Lineage         │
│ Gotham Operational Layer (investigations, graph/entity tracking)   │
├────────────────────────────────────────────────────────────────────┤
│ AIP Agent Orchestration + Copilots + Workflow Runtime + Evals      │
├────────────────────────────────────────────────────────────────────┤
│ Model Router (policy-aware) + Inference Endpoints + RAG Retrieval  │
├────────────────────────────────────────────────────────────────────┤
│ Policy-as-Code + AuthN/AuthZ + ABAC/RBAC + compartment boundaries  │
├────────────────────────────────────────────────────────────────────┤
│ Observability (metrics/logs/traces/evals dashboards)               │
├────────────────────────────────────────────────────────────────────┤
│ Apollo Delivery Plane (progressive deploy, rollback, canary, kill) │
└────────────────────────────────────────────────────────────────────┘
```

### 1.3 Platform Mapping (Palantir-specific)
- **Gotham**: operational graph exploration, entity resolution, investigation timelines, case-driven workflows.
- **Foundry**: data integration, ontology objects/links, transformations, lineage, mission applications.
- **AIP**: copilots, agent toolchains, prompt/eval framework, HITL automation.
- **Apollo**: runtime policy rollout, workload release channels, rollback/containment, environment drift management.

---

## 2) Data and Ontology

### 2.1 Canonical Entity Model
```sql
-- Foundry-like logical schema (portable to warehouse)
CREATE TABLE entity (
  entity_id            TEXT PRIMARY KEY,
  entity_type          TEXT NOT NULL,         -- PERSON, ORG, DEVICE, LOCATION, EVENT
  display_name         TEXT,
  confidence_score     DOUBLE PRECISION,      -- 0.0 - 1.0
  first_seen_ts        TIMESTAMP,
  last_seen_ts         TIMESTAMP,
  mission_context_id   TEXT,
  classification_level TEXT,                  -- U, C, S, TS...
  coalition_tag        TEXT,                  -- e.g., US, FVEY, NATO
  status               TEXT,
  created_at           TIMESTAMP,
  updated_at           TIMESTAMP
);

CREATE TABLE relationship (
  rel_id               TEXT PRIMARY KEY,
  src_entity_id        TEXT NOT NULL,
  dst_entity_id        TEXT NOT NULL,
  rel_type             TEXT NOT NULL,         -- COMMUNICATED_WITH, OWNS, LOCATED_AT
  confidence_score     DOUBLE PRECISION,
  valid_from_ts        TIMESTAMP,
  valid_to_ts          TIMESTAMP,
  source_ref           TEXT,
  lineage_id           TEXT,
  mission_context_id   TEXT,
  classification_level TEXT,
  coalition_tag        TEXT
);

CREATE TABLE event_fact (
  event_id             TEXT PRIMARY KEY,
  event_type           TEXT,
  event_ts             TIMESTAMP,
  payload_json         JSONB,
  source_system        TEXT,
  source_event_id      TEXT,
  lineage_id           TEXT,
  confidence_score     DOUBLE PRECISION,
  mission_context_id   TEXT,
  classification_level TEXT,
  coalition_tag        TEXT
);
```

### 2.2 Ontology Design Principles
1. **Temporal truth**: all important relationships have `valid_from`/`valid_to`.
2. **Lineage and provenance**: every entity/link/event has `lineage_id` and `source_ref`.
3. **Confidence-aware reasoning**: downstream agents consume confidence and uncertainty bands.
4. **Mission context binding**: explicit linkage to operation, task force, or incident.
5. **Security labels as first-class fields**: row/entity permissions enforced at query and tool layers.

### 2.3 Ontology Drives AI Behavior
- Agent tool calls require ontology type signatures (e.g., `Entity<Person>`, `Link<CommunicatedWith>`).
- Planner avoids actions on low-confidence entities unless analyst approval is provided.
- Retrieval scope is bounded by mission context, clearance, and coalition partition.

---

## 3) AI and Agent Design

### 3.1 Copilots
- **Analyst Copilot**: triage support, graph explanation, timeline synthesis, report drafts.
- **Commander Copilot**: mission-level risk summaries, recommended COAs, confidence deltas.

### 3.2 Multi-Agent Workflow
```text
Ingest Agent -> Enrichment Agent -> Correlation Agent -> Risk Scoring Agent
-> Recommendation Agent -> Human Approval Gate -> Action Agent
-> Outcome Capture Agent -> Eval/Improvement Agent
```

### 3.3 Tooling Interface (Python)
```python
from pydantic import BaseModel
from typing import Literal, Dict, Any

class ToolContext(BaseModel):
    user_id: str
    mission_context_id: str
    clearance: str
    coalition_tag: str

class ToolResult(BaseModel):
    success: bool
    payload: Dict[str, Any]
    evidence_refs: list[str]

class AgentTool:
    name: str
    requires_approval: bool = False

    async def run(self, ctx: ToolContext, args: Dict[str, Any]) -> ToolResult:
        raise NotImplementedError

class OpenCaseTool(AgentTool):
    name = "open_case"
    requires_approval = True

    async def run(self, ctx: ToolContext, args: Dict[str, Any]) -> ToolResult:
        # policy check + write case object
        return ToolResult(success=True, payload={"case_id": "CASE-2026-001"}, evidence_refs=[])
```

### 3.4 Operational Approval Gates
- Any action that creates/updates real operations (case escalation, notifications, tasking) is `requires_approval=True`.
- Dual-control approval for high-impact actions (e.g., cross-domain dissemination).

---

## 4) Self-Improvement Loop

### 4.1 Signals Captured
- Prompt transcripts, user edits, analyst overrides, false-positive/false-negative outcomes.
- Alert closure outcomes, mission KPI movements, latency/cost traces.

### 4.2 Improvement Pipeline
```text
Signals -> Feature Store -> Eval Dataset Builder -> Candidate Generator
-> Offline Evals -> Safety/Policy Tests -> Human Review Board
-> Canary Deploy (Apollo) -> Live A/B Eval -> Promote/Rollback
```

### 4.3 Versioned Artifacts
- `prompt_version`
- `workflow_version`
- `router_policy_version`
- `model_bundle_version`
- `policy_bundle_version`

### 4.4 Drift Detection + Rollback
```python
def detect_drift(baseline_precision: float, live_precision: float,
                 baseline_latency_ms: float, live_latency_ms: float) -> bool:
    precision_drop = baseline_precision - live_precision
    latency_increase = live_latency_ms - baseline_latency_ms
    return precision_drop > 0.05 or latency_increase > 120

async def safe_promote_or_rollback(metrics, apollo_client):
    if detect_drift(metrics.base_p, metrics.live_p, metrics.base_l, metrics.live_l):
        await apollo_client.rollback(channel="prod", reason="quality_drift_detected")
    else:
        await apollo_client.promote(channel="prod")
```

### 4.5 Human-Governed Autonomy Rule
The system can **propose** upgrades automatically, but cannot self-apply high-impact behavior changes without explicit reviewer approval and policy checks.

---

## 5) Full-Stack Implementation Blueprint

### 5.1 Frontend (React/Next.js)
- Mission dashboard with live event stream.
- Entity graph, timeline, confidence overlays, provenance panel.
- Copilot chat with cited evidence, action cards, and approval UX.

### 5.2 API Gateway (FastAPI + GraphQL)
```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel

app = FastAPI(title="ClearGlassInc Artemis API")

class AskCopilotRequest(BaseModel):
    mission_context_id: str
    query: str

@app.post("/copilot/ask")
async def ask_copilot(req: AskCopilotRequest, user=Depends(...)):
    # 1) authorize mission scope
    # 2) retrieve ontology-grounded context
    # 3) call AIP agent orchestrator
    return {"answer": "...", "citations": ["entity:E-123", "event:EV-9"]}
```

### 5.3 Streaming Layer
```python
# Kafka consumer pseudo-implementation
async def consume_events(loop_forever=True):
    while loop_forever:
        msg = await broker.receive(topic="intel.raw.events")
        normalized = normalize_event(msg)
        await foundry_writer.write("event_fact", normalized)
        await broker.publish("intel.enrichment.requested", normalized)
```

### 5.4 Workflow State Machine
```python
from enum import Enum

class AlertState(str, Enum):
    NEW = "NEW"
    ENRICHED = "ENRICHED"
    CORRELATED = "CORRELATED"
    RECOMMENDED = "RECOMMENDED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    ACTIONED = "ACTIONED"
    CLOSED = "CLOSED"

ALLOWED = {
    AlertState.NEW: {AlertState.ENRICHED},
    AlertState.ENRICHED: {AlertState.CORRELATED},
    AlertState.CORRELATED: {AlertState.RECOMMENDED},
    AlertState.RECOMMENDED: {AlertState.AWAITING_APPROVAL, AlertState.CLOSED},
    AlertState.AWAITING_APPROVAL: {AlertState.ACTIONED, AlertState.CLOSED},
    AlertState.ACTIONED: {AlertState.CLOSED},
}
```

### 5.5 Model Router (Policy + Cost + Latency)
```python
def route_model(task_type: str, data_classification: str, latency_budget_ms: int):
    if data_classification in {"S", "TS"}:
        return "onprem-secure-llm-v3"
    if task_type == "summarization" and latency_budget_ms < 1200:
        return "fast-ops-llm"
    return "deep-reasoner-llm"
```

### 5.6 Eval Pipeline
```python
def evaluate_candidate(candidate_version: str, dataset: list[dict]) -> dict:
    tp = fp = fn = 0
    total_latency = 0
    for sample in dataset:
        pred = run_candidate(candidate_version, sample)
        tp += int(pred["label"] == sample["label"] == 1)
        fp += int(pred["label"] == 1 and sample["label"] == 0)
        fn += int(pred["label"] == 0 and sample["label"] == 1)
        total_latency += pred["latency_ms"]

    precision = tp / (tp + fp + 1e-9)
    recall = tp / (tp + fn + 1e-9)
    avg_latency = total_latency / max(len(dataset), 1)
    return {"precision": precision, "recall": recall, "avg_latency_ms": avg_latency}
```

---

## 6) Security and Governance

### 6.1 Access Control
- Hybrid **RBAC + ABAC** with mission attributes and need-to-know.
- Row/column/entity guards at query time and tool execution time.
- Coalition boundaries enforced with mandatory `coalition_tag` filters.

### 6.2 Zero-Trust Execution
- Each service has workload identity.
- Mutual TLS between services.
- Signed request claims for mission scope.

### 6.3 Immutable Audit + Provenance
- Append-only operational logs for decisions, prompts, approvals, and actions.
- Hash-chained event ledger for tamper evidence.

### 6.4 Policy-as-Code Example (OPA/Rego)
```rego
package artemis.authz

default allow = false

allow {
  input.user.clearance_rank >= input.resource.required_clearance_rank
  input.user.coalition_tag == input.resource.coalition_tag
  input.user.mission_ids[_] == input.resource.mission_context_id
}
```

---

## 7) Scenario Walkthrough (End-to-End)

1. A live maritime anomaly event arrives on `intel.raw.events`.
2. Ingest Agent normalizes schema, stamps lineage, stores in Foundry dataset.
3. Enrichment Agent links vessel entity, owner org, port history, prior alerts.
4. Correlation Agent finds pattern match with prior sanctioned routing behavior.
5. Recommendation Agent proposes: “Open Priority-2 Case and issue analyst review package.”
6. Policy engine marks as operationally significant -> approval required.
7. Analyst accepts with one correction (changes risk reason code).
8. Action Agent opens Gotham case + generates commander brief.
9. Outcome after 48h confirms risk was valid.
10. Feedback pipeline captures analyst correction + successful outcome.
11. Improvement service generates a prompt/workflow candidate that better explains reason code selection.
12. Candidate passes offline eval, security tests, and reviewer approval.
13. Apollo canary deploys candidate to 10% missions.
14. Live metrics show +4.2% precision, -8% time-to-decision, no policy violations.
15. Candidate is promoted globally; previous version retained for instant rollback.

---

## 8) Implementation Notes (Production Readiness)

- Start with one mission domain and expand after eval stability.
- Keep prompt, workflow, and routing changes independently versioned.
- Require human approval for policy/risk threshold changes.
- Build “explain why” UX everywhere: confidence, provenance, and policy decisions.
- Treat eval quality as a first-class SLO alongside latency and uptime.

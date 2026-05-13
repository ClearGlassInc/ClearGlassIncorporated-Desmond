# ClearGlassInc Artemis — Self-Evolving AI Intelligence Platform (Production Blueprint)

## System Architecture

### 1. End-to-End Layered Architecture (Gotham + Foundry + AIP + Apollo)

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ Frontend Experience Layer                                                              │
│  - Analyst Workbench (map/timeline/entity graph/case board)                            │
│  - Commander COP (decision dashboard, COA compare, approval console)                   │
│  - Governance Console (policy diffs, model/prompt release approvals)                   │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ API Edge Layer                                                                         │
│  - API Gateway (REST + GraphQL + WebSocket + gRPC transcoding)                         │
│  - Context Broker (mission context, tenant, coalition compartment)                     │
│  - AuthN/AuthZ adapter (OIDC/SAML, device trust, mTLS, ABAC/RBAC)                      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ Domain Services Layer (Foundry app logic + Gotham operational integration)             │
│  - Alert Intake Service           - Entity Resolution Service                           │
│  - Case Management Service        - Mission Orchestration Service                       │
│  - Intelligence Product Service   - Approval Workflow Service                           │
│  - Feedback & Eval Service        - Policy Decision Point (PDP)                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                        ┌─────────────┴─────────────┐
                        ▼                           ▼
┌──────────────────────────────────────┐  ┌──────────────────────────────────────────────┐
│ Data + Ontology Layer (Foundry)     │  │ AI Orchestration Layer (AIP)                 │
│ - Ontology objects/links/actions     │  │ - Copilots + multi-agent runtime              │
│ - Streaming/batch transforms         │  │ - Prompt registry + tool registry             │
│ - Lineage + provenance + bitemporal  │  │ - Model router + eval harness                 │
│ - Data products (bronze/silver/gold) │  │ - Policy-constrained action planner           │
└──────────────────────────────────────┘  └──────────────────────────────────────────────┘
                        │                           │
                        └─────────────┬─────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ Policy, Audit, and Observability                                                       │
│ - Policy-as-code (OPA/Rego), risk controls, approval gates                             │
│ - Immutable audit ledger (who/what/when/why/version hash)                              │
│ - Telemetry: tracing, logs, metrics, eval scorecards                                   │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ Deployment + Runtime Control (Apollo)                                                  │
│ - Signed artifacts, progressive rollout rings, health gates                             │
│ - Runtime kill-switches, rollback by prompt/workflow/model independently               │
│ - Cross-domain secure distribution with coalition-aware policy bundles                 │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Platform Responsibilities (precise terminology)
- **Gotham**: operational intelligence, case tracking, entity/event timeline, investigator workflows.
- **Foundry**: ingestion, integration, ontology, pipeline logic, governed data products.
- **AIP**: copilots, agent workflows, tool-using automation, evaluations, model routing.
- **Apollo**: secure delivery/control plane for deploy, rollback, and runtime governance.

### 3. Critical Control Planes
1. **Data Control Plane** (schema + lineage + quality).
2. **Agent Control Plane** (prompt/workflow/versioned plans).
3. **Policy Control Plane** (permissions + action constraints).
4. **Delivery Control Plane** (Apollo rollouts + rollback).

---

## Data and Ontology

### 1. Canonical Ontology (Foundry)

#### Entities
- `Person`, `Organization`, `Device`, `Vehicle`, `Location`, `Asset`
- `Event`, `Signal`, `Alert`, `Case`, `Mission`, `Task`, `ActionPackage`
- `IntelProduct`, `Hypothesis`, `Evidence`, `ModelDecision`, `Approval`

#### Relationships
- `OBSERVED_AT`, `ASSOCIATED_WITH`, `OWNS`, `USES`, `TRAVELED_TO`
- `DERIVED_FROM`, `SUPPORTS_HYPOTHESIS`, `CONTRADICTS_HYPOTHESIS`
- `PART_OF_CASE`, `PART_OF_MISSION`, `TRIGGERED_ALERT`
- `REQUIRES_APPROVAL`, `APPROVED_BY`, `REJECTED_BY`

#### Required Attributes
- `confidence_score` (float 0..1)
- `source_reliability` (A-F)
- `classification_level` + `releasability_tags`
- `coalition_boundary` + `compartment`
- `valid_time_start`, `valid_time_end` (world time)
- `txn_time_start`, `txn_time_end` (system time)
- `lineage_id`, `transform_version`, `evidence_hash`
- `policy_tags`, `need_to_know_labels`

### 2. Temporal + Lineage Semantics
- **Bitemporal** storage is mandatory to support retrospective intelligence reconstruction.
- Each feature emitted into AI context includes a provenance tuple:
  `(source_system, ingestion_job, transform_dag, ontology_version, hash)`.
- Agents can only cite facts with non-expired `valid_time` or explicitly mark stale context.

### 3. Permissions as Ontology-Aware Constraints
- **Entity-level** filtering for case visibility.
- **Property-level** redaction for sensitive attributes.
- **Edge-level** filtering to hide relationship topology across coalition boundaries.
- **Action-level** constraints for operational verbs (e.g., no tasking without commander approval).

---

## AI and Agent Design

### 1. Copilot Roles
- **Analyst Copilot**: summarize events, enrich entities, suggest hypotheses, draft intel notes.
- **Commander Copilot**: compare courses of action (COAs), expose confidence/risk tradeoffs.
- **Governance Copilot**: explain policy decisions, justify blocked actions, generate audit narratives.

### 2. Multi-Agent Workflow Graph

```text
IntakeAgent
  -> TriageAgent
  -> EnrichmentAgent
  -> CorrelationAgent
  -> RiskScoringAgent
  -> RecommendationAgent
  -> ApprovalGateAgent
  -> ExecutionAgent (human token required)
  -> OutcomeAgent
  -> LearningAgent
```

### 3. Tooling API (AIP tools)
- `query_ontology(filters, mission_ctx)`
- `search_evidence(query, compartments)`
- `open_case(payload)`
- `create_action_package(payload)`
- `request_approval(action_id, approver_role)`
- `record_outcome(outcome_payload)`

### 4. Hard Safety Boundaries
- Agents cannot grant themselves new permissions.
- Agents cannot auto-promote prompt/workflow/model versions.
- Operational actions require signed approval tokens with expiration.

---

## Self-Improvement Loop

### 1. Signal Collection
Collect and normalize:
- Operator edits and explicit feedback.
- Alert dispositions (TP/FP/FN) and mission outcomes.
- Latency, token cost, model route, and tool usage traces.
- Approval/rejection reasons and downstream action success rates.

### 2. Closed-Loop Improvement Pipeline
1. **Log Capture** → event bus topic `feedback.events`.
2. **Feature Engineering** → Foundry dataset `eval_features`.
3. **Eval Set Builder** → stratified datasets by mission type/compartment.
4. **Candidate Generator** → prompt/workflow/router rule proposals.
5. **Offline Eval Harness** → precision/recall/latency/trust score.
6. **Policy Gate** → reject changes violating thresholds.
7. **Human Review Board** → approve/reject with rationale.
8. **Apollo Canary** → ring deploy in pilot cell.
9. **Post-Deploy Monitors** → drift, trust, mission KPI checks.
10. **Promote/Rollback** with immutable decision records.

### 3. Versioning and Rollback
- Version dimensions are independent:
  - `prompt_version`
  - `workflow_version`
  - `router_version`
  - `policy_bundle_version`
- Rollback may target one dimension without global system rollback.

### 4. Drift Detection
- Data drift: PSI/KL divergence over key features.
- Label drift: TP/FP rate changes by mission segment.
- Behavior drift: approval rejection-rate anomalies by agent step.

---

## Full-Stack Implementation

### 1. Web UI (TypeScript, Next.js)
- Real-time incident stream + map overlays.
- Entity graph explorer with provenance panel.
- Copilot chat with source-cited reasoning.
- Approval console with policy explanation and diff view.

### 2. API Gateway + BFF
- `POST /v1/events/intake`
- `GET /v1/cases/{id}`
- `POST /v1/agent/plan`
- `POST /v1/actions/{id}/approve`
- GraphQL endpoint for UI composition.

### 3. Backend Services (Python)
- `ingest_service`
- `ontology_query_service`
- `agent_orchestrator_service`
- `approval_service`
- `eval_service`

### 4. Event and Streaming Layer
- Kafka/PubSub topics:
  - `intel.raw`
  - `intel.enriched`
  - `alerts.triaged`
  - `actions.pending_approval`
  - `actions.executed`
  - `feedback.events`
  - `eval.results`

### 5. Data Warehouse / Lakehouse
- Bronze: raw immutable source events.
- Silver: normalized, deduplicated, ontology-aligned records.
- Gold: mission-ready marts + agent feature views.

### 6. Retrieval and Search
- Hybrid retrieval: keyword + vector + graph neighborhood.
- Mission-aware context packer enforces policy filters before model context assembly.

### 7. Model Router / Inference
- Routing based on:
  - mission criticality
  - latency budget
  - classification level
  - required reasoning depth

### 8. Observability + Eval Dashboard
- OpenTelemetry spans for each agent/tool step.
- Dashboards: precision@k, recall, FPR, MTTD, MTTR, trust score, approval SLA.

---

## Security and Governance

### 1. Zero-Trust Architecture
- mTLS everywhere.
- Workload identity + signed service tokens.
- No implicit network trust.

### 2. Need-to-Know Access
- ABAC (attributes: clearance, mission, compartment) + RBAC (role baseline).
- Row/column/entity/relationship/action-level enforcement.

### 3. Coalition and Compartment Controls
- Cross-domain guards for releasability tags.
- Policy evaluation at query time and action time.

### 4. Immutable Provenance and Audit
- Append-only signed audit records:
  - user/agent identity
  - data read/write scope
  - prompt/workflow/model versions
  - policy decision IDs
  - approval artifacts

### 5. Policy-as-Code and Model Governance
- OPA/Rego policy bundles are versioned and signed.
- Prompt governance includes banned patterns and release checklists.
- Model governance includes mission suitability matrix and failure-mode controls.

---

## Code Examples

### 1) Python FastAPI Ingest Service

```python
# services/ingest_service/main.py
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from uuid import uuid4

app = FastAPI(title="ClearGlassInc Artemis Ingest")

class IncomingSignal(BaseModel):
    source: str
    mission_id: str
    signal_type: str
    payload: dict
    observed_at: datetime
    classification: str = Field(pattern=r"^(CUI|SECRET|TS)$")

@app.post("/v1/events/intake")
def intake(signal: IncomingSignal, x_request_id: str | None = Header(default=None)):
    if signal.classification == "TS" and signal.mission_id.startswith("coalition-"):
        raise HTTPException(status_code=403, detail="TS signal blocked for coalition mission")

    event_id = str(uuid4())
    envelope = {
        "event_id": event_id,
        "request_id": x_request_id or str(uuid4()),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "signal": signal.model_dump()
    }
    # publish_to_topic("intel.raw", envelope)
    return {"status": "accepted", "event_id": event_id}
```

### 2) Python Agent Orchestrator (state machine)

```python
# services/agent_orchestrator/workflow.py
from enum import Enum
from dataclasses import dataclass

class Step(str, Enum):
    TRIAGE = "triage"
    ENRICH = "enrich"
    CORRELATE = "correlate"
    RECOMMEND = "recommend"
    APPROVAL = "approval"
    EXECUTE = "execute"

@dataclass
class WorkflowState:
    mission_id: str
    case_id: str | None
    current_step: Step
    recommendation: dict | None
    approved: bool = False


def run_step(state: WorkflowState, tools):
    if state.current_step == Step.TRIAGE:
        triage = tools.triage_event(state.mission_id)
        state.current_step = Step.ENRICH
        return triage

    if state.current_step == Step.ENRICH:
        context = tools.query_ontology({"mission_id": state.mission_id})
        state.current_step = Step.CORRELATE
        return context

    if state.current_step == Step.CORRELATE:
        graph = tools.correlate_entities(state.mission_id)
        state.current_step = Step.RECOMMEND
        return graph

    if state.current_step == Step.RECOMMEND:
        state.recommendation = tools.generate_recommendation(state.mission_id)
        state.current_step = Step.APPROVAL
        return state.recommendation

    if state.current_step == Step.APPROVAL:
        token = tools.request_human_approval(state.recommendation)
        state.approved = token.get("approved", False)
        state.current_step = Step.EXECUTE if state.approved else Step.RECOMMEND
        return token

    if state.current_step == Step.EXECUTE:
        if not state.approved:
            raise RuntimeError("Execution blocked: no approval")
        return tools.execute_action_package(state.recommendation)
```

### 3) TypeScript API Gateway Policy Check

```typescript
// gateway/src/policy.ts
export type PolicyInput = {
  subject: { id: string; role: string; clearance: string };
  action: string;
  resource: { type: string; id: string; compartment: string; classification: string };
  mission: { id: string; coalition: string };
};

export async function authorize(input: PolicyInput): Promise<void> {
  const decision = await fetch("http://pdp:8181/v1/data/artemis/allow", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input })
  }).then(r => r.json());

  if (!decision.result?.allow) {
    throw new Error(`DENY: ${decision.result?.reason ?? "policy_violation"}`);
  }
}
```

### 4) Rego Policy-as-Code (approval gate)

```rego
package artemis

default allow := false

allow if {
  input.action == "execute_action_package"
  input.subject.role == "commander"
  clearance_allows
  same_compartment
}

clearance_allows if {
  input.subject.clearance == "TS"
}

same_compartment if {
  input.resource.compartment == input.mission.id
}
```

### 5) SQL Eval Dataset Builder

```sql
-- foundry/sql/build_eval_dataset.sql
CREATE OR REPLACE TABLE eval_dataset_daily AS
SELECT
  a.alert_id,
  a.mission_id,
  a.alert_type,
  a.model_route,
  a.prompt_version,
  a.workflow_version,
  f.operator_label,
  f.operator_confidence,
  o.outcome,
  o.time_to_resolution_seconds,
  a.created_at
FROM alerts_scored a
LEFT JOIN feedback_events f ON a.alert_id = f.alert_id
LEFT JOIN mission_outcomes o ON a.case_id = o.case_id
WHERE a.created_at >= CURRENT_DATE - INTERVAL '7 day';
```

### 6) Python Self-Upgrade Candidate Evaluator

```python
# services/eval_service/candidate_eval.py
from dataclasses import dataclass

@dataclass
class Metrics:
    precision: float
    recall: float
    latency_ms_p95: float
    trust_score: float


def should_promote(baseline: Metrics, candidate: Metrics) -> bool:
    if candidate.precision < baseline.precision - 0.01:
        return False
    if candidate.recall < baseline.recall - 0.02:
        return False
    if candidate.latency_ms_p95 > baseline.latency_ms_p95 * 1.10:
        return False
    if candidate.trust_score < baseline.trust_score:
        return False
    return True
```

---

## Scenario Walkthrough (Cinematic, technically credible)

1. **Live Event Ingest**  
   A SIGINT burst from a border sensor enters `intel.raw` with `SECRET` classification. Ingest service normalizes, stamps lineage, and emits to `intel.enriched`.

2. **Automated Triage and Correlation**  
   TriageAgent assigns elevated risk due to pattern match with prior smuggling route. EnrichmentAgent pulls linked `Vehicle` and `Person` entities from Foundry ontology. CorrelationAgent identifies convergence with an open Gotham case timeline.

3. **Recommendation Generated**  
   RecommendationAgent drafts an action package: task ISR drone corridor sweep + notify joint cell + open priority sub-case. Confidence is 0.82, risk rationale included with cited evidence hashes.

4. **Human Approval Gate**  
   ApprovalGateAgent requests commander sign-off. Policy checks verify commander clearance, mission compartment, and coalition boundaries. Commander rejects drone tasking (weather risk) but approves notification + sub-case creation.

5. **Execution and Outcome Logging**  
   ExecutionAgent performs only approved actions. OutcomeAgent records response timing and downstream mission result.

6. **Learning Loop Activation**  
   Feedback pipeline labels rejected drone recommendation as context-missed (weather feature absent). Candidate workflow patch introduces mandatory weather context retrieval before ISR recommendations.

7. **Safe Self-Upgrade**  
   Eval harness shows +4.1% precision, no recall loss, +2.7% latency (under threshold). Review board approves. Apollo canaries to pilot cell, monitors remain healthy, then promotes globally.

8. **Audit and Provenance**  
   Every step (data read, model route, prompt/workflow versions, approval decision, deployment promotion) is immutably logged and queryable for after-action review.

---

## Artemis IV Core Backend Kickstart (Python-first precision implementation)

### Recommended first build slice: Real-time GDELT ingestion pipeline

```python
# services/gdelt_ingest/app.py
import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx
from aiokafka import AIOKafkaProducer
from fastapi import FastAPI

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

@dataclass
class GdeltConfig:
    query: str = "(cyber OR malware OR ransomware)"
    mode: str = "ArtList"
    format: str = "json"
    max_records: int = 100

app = FastAPI(title="Artemis IV GDELT Ingest")
producer: AIOKafkaProducer | None = None

@app.on_event("startup")
async def startup() -> None:
    global producer
    producer = AIOKafkaProducer(bootstrap_servers="redpanda:9092")
    await producer.start()

@app.on_event("shutdown")
async def shutdown() -> None:
    if producer:
        await producer.stop()

async def fetch_gdelt(cfg: GdeltConfig) -> list[dict[str, Any]]:
    params = {
        "query": cfg.query,
        "mode": cfg.mode,
        "format": cfg.format,
        "maxrecords": cfg.max_records,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(GDELT_URL, params=params)
        resp.raise_for_status()
        return resp.json().get("articles", [])

@app.post("/v1/ingest/gdelt/poll")
async def poll_once() -> dict[str, Any]:
    assert producer is not None
    records = await fetch_gdelt(GdeltConfig())
    sent = 0
    for r in records:
        event = {
            "source": "gdelt",
            "event_time": r.get("seendate") or datetime.now(timezone.utc).isoformat(),
            "title": r.get("title"),
            "url": r.get("url"),
            "domain": r.get("domain"),
            "lang": r.get("language"),
            "lineage": {"pipeline": "gdelt_ingest_v1", "emitted_at": datetime.now(timezone.utc).isoformat()},
        }
        await producer.send_and_wait("intel.raw", json.dumps(event).encode("utf-8"))
        sent += 1
    return {"status": "ok", "sent": sent}


async def scheduler() -> None:
    while True:
        try:
            await poll_once()
        except Exception as exc:  # logged/observed via OTEL in production
            print(f"gdelt-poll-error: {exc}")
        await asyncio.sleep(30)
```

### Python policy guard before any operational action

```python
# services/policy/guard.py
from dataclasses import dataclass

@dataclass
class Subject:
    user_id: str
    role: str
    clearance: str
    compartments: list[str]

@dataclass
class Action:
    name: str
    sensitivity: str
    mission_compartment: str


def authorize(subject: Subject, action: Action) -> tuple[bool, str]:
    if action.sensitivity == "operational" and subject.role not in {"commander", "ops_lead"}:
        return False, "role_block"
    if subject.clearance not in {"SECRET", "TS"}:
        return False, "clearance_block"
    if action.mission_compartment not in subject.compartments:
        return False, "compartment_block"
    return True, "allow"
```

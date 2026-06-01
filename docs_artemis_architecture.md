# ClearGlassInc Artemis — Mission-Grade Self-Evolving Intelligence Platform Blueprint

## System Architecture

### 1) End-to-End Full-Stack Topology (Gotham + Foundry + AIP + Apollo)

```text
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ UX Layer (Web + Mobile Secure Client)                                                   │
│  - Analyst Workbench: Entity graph, timeline, map, case board                           │
│  - Commander COP: COA simulator, risk matrix, approval console                           │
│  - Governance Console: policy diffs, model/prompt release board                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ Edge/API Layer                                                                           │
│  - Envoy/API Gateway: REST + GraphQL + WebSocket + gRPC-web                             │
│  - Context Broker: coalition boundary, mission, classification, releasability           │
│  - PDP/PIP adapter: OPA policy decision + identity attributes                            │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ Service Mesh Domain Layer                                                                │
│  - Intake (GDELT/NVD/ADS-B/USGS)  - Fusion/Correlation  - Case Management               │
│  - Alerting/Risk Scoring          - Action Packaging   - Approval & Execution           │
│  - Feedback/Eval Capture          - PromptOps/WorkflowOps                                │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                       │                                            │
                       ▼                                            ▼
┌─────────────────────────────────────────────┐      ┌─────────────────────────────────────┐
│ Foundry Data/Ontology Plane                 │      │ AIP Agentic AI Plane                │
│ - Bronze/Silver/Gold data products          │      │ - Copilots + multi-agent runtime    │
│ - Ontology objects/links/actions            │      │ - Tool registry + planner           │
│ - Data lineage + quality contracts          │      │ - Model routing + eval harness      │
│ - Bitemporal entity state                    │      │ - Guardrailed self-improvement      │
└─────────────────────────────────────────────┘      └─────────────────────────────────────┘
                       │                                            │
                       └──────────────────────────┬─────────────────┘
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ Security/Observability/Governance Plane                                                  │
│ - Zero trust, mTLS SPIFFE IDs, ABAC + ReBAC                                              │
│ - OpenTelemetry traces/logs/metrics + eval scorecards                                    │
│ - Immutable audit ledger for data/model/prompt/workflow decisions                        │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ Apollo Delivery Plane                                                                     │
│ - Signed artifacts, canary rings, blast-radius control, progressive rollout              │
│ - Per-component rollback: prompt/workflow/router/model/policy independently              │
│ - Runtime kill-switches and mission-mode degradation controls                             │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2) Control Planes
- **Data Control Plane**: schema registry, quality checks, lineage, retention.
- **Knowledge Control Plane**: ontology versioning, graph integrity, bitemporal state.
- **AI Control Plane**: prompt registry, tool contracts, eval gates, router policies.
- **Policy Control Plane**: OPA bundles, coalition constraints, approval rules.
- **Delivery Control Plane**: Apollo release rings, health checks, rollback graph.

---

## Data and Ontology

### 1) Canonical Ontology (Foundry-backed)

#### Entity Types
- `Actor(Person|Org|Group)`
- `CyberAsset(Device|IP|Domain|Certificate|SoftwareComponent)`
- `GeoAsset(Location|Facility|Route|AirTrack)`
- `IntelArtifact(Event|Signal|Report|IOC|CVE|Case|Mission|Task|ActionPackage)`
- `GovernanceArtifact(PolicyDecision|Approval|ModelRelease|PromptRelease)`

#### Relationship Types
- `OBSERVED_AT`, `ATTRIBUTED_TO`, `INDICATES`, `TARGETS`, `PART_OF_CASE`, `PART_OF_MISSION`
- `SUPPORTS`, `CONTRADICTS`, `DERIVED_FROM`, `REQUIRES_APPROVAL`, `EXECUTED_BY`

#### Mandatory Metadata
- Confidence tuple: `confidence`, `source_reliability`, `model_agreement`
- Provenance tuple: `source_system`, `ingestion_job`, `transform_version`, `evidence_hash`
- Temporal tuple: `valid_start/end`, `txn_start/end`
- Security tuple: `classification`, `releasability`, `compartment`, `need_to_know`

### 2) SQL Foundation (PostgreSQL + Timescale + pgvector)

```sql
create table intel_event (
  event_id uuid primary key,
  event_type text not null,
  payload jsonb not null,
  confidence numeric(5,4) not null,
  classification text not null,
  compartment text not null,
  valid_time tstzrange not null,
  txn_time tstzrange not null,
  lineage_id text not null,
  created_at timestamptz not null default now()
);

create table entity_edge (
  edge_id uuid primary key,
  src_entity uuid not null,
  dst_entity uuid not null,
  relation text not null,
  confidence numeric(5,4) not null,
  valid_time tstzrange not null,
  txn_time tstzrange not null,
  policy_tags text[] not null,
  evidence_hash text not null
);

create table prompt_release (
  release_id uuid primary key,
  prompt_family text not null,
  version text not null,
  metrics jsonb not null,
  approved_by text,
  approved_at timestamptz,
  status text not null check (status in ('candidate','approved','rolled_back','rejected'))
);
```

---

## AI and Agent Design

### 1) Copilot and Agent Roles
- **Analyst Copilot**: triage, enrichment, evidence graph explanation.
- **Commander Copilot**: COA synthesis with mission risk and confidence envelope.
- **Governance Copilot**: “why blocked/allowed” policy explanation with citations.

### 2) Multi-Agent Pipeline (AIP)

```yaml
workflow: intel-response-v3
steps:
  - intake_agent
  - triage_agent
  - enrichment_agent
  - correlation_agent
  - threat_scoring_agent
  - recommendation_agent
  - approval_gate_agent
  - execution_agent
  - outcome_agent
  - learning_agent
hard_guards:
  - no_operational_execution_without_human_approval: true
  - no_policy_change_by_agents: true
  - no_cross_compartment_data_leakage: true
```

### 3) Python Tool Contract Example

```python
from pydantic import BaseModel, Field
from typing import Literal, List

class MissionContext(BaseModel):
    mission_id: str
    coalition: str
    classification: Literal["U", "C", "S", "TS"]
    compartments: List[str]

class QueryOntologyInput(BaseModel):
    query: str
    k: int = Field(default=25, ge=1, le=200)
    context: MissionContext

class ToolResult(BaseModel):
    rows: list[dict]
    citations: list[str]

async def query_ontology_tool(inp: QueryOntologyInput) -> ToolResult:
    # policy-filtered query generated by ontology planner
    sql = "select * from ontology_search($1, $2, $3, $4)"
    rows = await db.fetch(sql, inp.query, inp.k, inp.context.coalition, inp.context.compartments)
    return ToolResult(rows=[dict(r) for r in rows], citations=[r["lineage_id"] for r in rows])
```

---

## Self-Improvement Loop

### 1) Learning Signals
- Explicit analyst feedback (`thumbs`, corrections, rationale).
- Alert outcome labels (TP/FP/FN), response success/failure.
- Latency, route choice, token cost, abstention rate.
- Approval outcomes and rollback incidents.

### 2) Improvement Lifecycle
1. Ingest signals into `feedback.events` stream.
2. Materialize eval datasets stratified by mission type + compartment.
3. Generate prompt/workflow/router candidates.
4. Run offline eval harness and policy guard tests.
5. Human approval board review.
6. Apollo canary (Ring0->Ring2).
7. Promote or auto-rollback on regression.

### 3) Drift + Safety
- Data drift: PSI/KL thresholds.
- Behavior drift: rising rejection/override rates.
- Trust drift: operator confidence trend and unresolved case delay.

### 4) Python Eval Pipeline Skeleton

```python
@dataclass
class EvalResult:
    candidate_id: str
    precision: float
    recall: float
    p95_latency_ms: int
    trust_score: float
    policy_violations: int


def pass_gate(r: EvalResult) -> bool:
    return (
        r.precision >= 0.87 and
        r.recall >= 0.82 and
        r.p95_latency_ms <= 1200 and
        r.trust_score >= 0.75 and
        r.policy_violations == 0
    )


def choose_release(champion: EvalResult, challenger: EvalResult) -> str:
    if pass_gate(challenger) and challenger.precision - champion.precision >= 0.02:
        return "promote_challenger"
    return "retain_champion"
```

---

## Full-Stack Implementation

### 1) Frontend (Next.js + TypeScript + Deck.gl)
- Real-time threat layer overlays with WebSocket delta updates.
- Ontology graph with evidence/citation side panel.
- Approval modal requiring reason codes + hardware-backed auth.

### 2) API Gateway/BFF
- `POST /v1/intel/intake`
- `POST /v1/agents/plan`
- `POST /v1/actions/{id}/approve`
- `POST /v1/feedback`
- `GET /v1/evals/releases`

### 3) Python Backend Services
- `ingest_service` (connectors, schema validation)
- `fusion_service` (entity resolution + correlation)
- `agent_runtime_service` (AIP orchestration)
- `approval_service` (workflow + policy checks)
- `evalops_service` (offline/online evals)

### 4) Eventing
- Redpanda/Kafka topics: `intel.raw`, `intel.enriched`, `alert.triaged`, `action.pending`, `feedback.events`, `eval.results`.

### 5) Workflow State Machine (Python)

```python
from enum import Enum

class ActionState(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    ROLLED_BACK = "rolled_back"

ALLOWED = {
    ActionState.DRAFT: {ActionState.PENDING_APPROVAL},
    ActionState.PENDING_APPROVAL: {ActionState.APPROVED, ActionState.REJECTED},
    ActionState.APPROVED: {ActionState.EXECUTED, ActionState.ROLLED_BACK},
    ActionState.REJECTED: set(),
    ActionState.EXECUTED: {ActionState.ROLLED_BACK},
    ActionState.ROLLED_BACK: set(),
}


def transition(state: ActionState, nxt: ActionState) -> ActionState:
    if nxt not in ALLOWED[state]:
        raise ValueError(f"invalid transition {state}->{nxt}")
    return nxt
```

---

## Security and Governance

- Need-to-know and coalition-aware ABAC/ReBAC on rows, columns, entities, and graph edges.
- Policy-as-code (OPA/Rego) for runtime decisions and prompt/action constraints.
- Immutable provenance and append-only audit ledger for every agent/tool/action decision.
- Zero-trust execution with workload identity, mTLS, short-lived credentials.
- Prompt governance + model governance with explicit approval chain and signed releases.

```rego
package artemis.approval

default allow = false

allow {
  input.action.risk <= 0.45
  input.user.role == "Commander"
  input.user.clearance >= input.action.required_clearance
  input.context.compartment in input.user.compartments
}
```

---

## Code Examples

### 1) Event Handler (Python/FastAPI)

```python
from fastapi import FastAPI, Header, HTTPException

app = FastAPI()

@app.post("/v1/intel/intake")
async def intake(event: dict, x_mission_id: str = Header(...)):
    if not await policy.can_ingest(event, mission_id=x_mission_id):
        raise HTTPException(403, "policy denied")
    normalized = normalize_event(event)
    await bus.publish("intel.raw", normalized)
    return {"status": "accepted", "event_id": normalized["event_id"]}
```

### 2) Model Router Snippet

```python

def route_model(task: str, sensitivity: str, latency_budget_ms: int) -> str:
    if sensitivity in {"S", "TS"}:
        return "local-llm-secure-70b"
    if task == "triage" and latency_budget_ms < 700:
        return "local-llm-fast-8b"
    return "local-llm-accuracy-34b"
```

### 3) Approval Gate

```python
async def approve_action(action_id: str, user: UserCtx) -> dict:
    action = await actions.get(action_id)
    decision = await opa.evaluate("artemis/approval", {"action": action, "user": user.dict()})
    if not decision["allow"]:
        return {"status": "denied", "reason": "policy"}
    await actions.update_state(action_id, "approved")
    await audit.log("action_approved", action_id=action_id, actor=user.user_id)
    return {"status": "approved"}
```

---

## Scenario Walkthrough (Cinematic + Technical)

1. **Live event ingestion**: A new NVD CVE + GDELT infrastructure unrest signal enters `intel.raw` within 300 ms.
2. **Fusion**: `fusion_service` links CVE -> vendor asset inventory -> exposed business units in the mission compartment.
3. **Agent triage**: Triage and correlation agents generate a severity-0.81 action package and COA options.
4. **Recommendation**: Commander Copilot recommends temporary segmentation + patch acceleration; cites evidence lineage IDs.
5. **Human gate**: Commander approves in approval console with dual-control signature.
6. **Execution**: Action pushed to orchestrator playbook; confirmation flows back as `actions.executed`.
7. **Outcome learning**: Incident closes with no downtime. System records TP label, operator trust +0.06, and updates eval corpus.
8. **Self-upgrade proposal**: LearningAgent proposes prompt v3.18 improving triage precision by 2.6% in offline replay.
9. **Governed release**: Human review approves; Apollo canary deploys to Ring0. No regressions after 24h, then global promote.

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

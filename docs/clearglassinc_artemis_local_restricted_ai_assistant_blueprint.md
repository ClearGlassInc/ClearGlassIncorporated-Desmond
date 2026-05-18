# ClearGlassInc Artemis — Local Restricted-Network Self-Evolving AI Intelligence Platform

## System Architecture

### Mission Objective
Build a **local-first, restricted-egress, human-governed, self-improving** intelligence platform for **ClearGlassInc Artemis** using:
- **Gotham** (operational intelligence, investigations, entity tracking)
- **Foundry** (data integration, ontology, pipelines, operational applications)
- **AIP** (copilots, agents, tool-use, evals)
- **Apollo** (secure deployment, staged rollout, rollback, runtime governance)

### 1) Reference Topology (Zero-Trust, Coalition-Aware)

```mermaid
flowchart TB
  subgraph Z0[Zone 0: Operator Access]
    UI[Artemis Mission UI\n(React/TS)]
    CMD[Commander Console]
  end

  subgraph Z1[Zone 1: Application Plane]
    GW[API Gateway\nJWT+mTLS+PDP hook]
    ORCH[Agent Orchestrator\n(AIP workflow runtime)]
    CASE[Case Management Service]
    NOTIF[Alert/Notification Service]
  end

  subgraph Z2[Zone 2: Data Plane]
    FDRY[Foundry Data Products]
    ONT[Ontology Service]
    FEAT[Feature + Eval Store]
    LAKE[Lakehouse/Warehouse]
    VEC[Vector + Hybrid Search]
  end

  subgraph Z3[Zone 3: Model Plane]
    MRT[Model Router]
    LLMR[Local Reasoning LLM]
    LLMS[Local Summarization LLM]
    EMB[Local Embedding Model]
    RERANK[Local Reranker]
  end

  subgraph Z4[Zone 4: Governance/Control]
    PDP[Policy Decision Point]
    AUDIT[Immutable Audit Ledger]
    EVAL[Eval + Drift Engine]
    REG[Prompt/Workflow Registry]
    APOLLO[Apollo Rollout Controller]
  end

  UI --> GW
  CMD --> GW
  GW --> ORCH
  ORCH --> FDRY
  ORCH --> ONT
  ORCH --> VEC
  ORCH --> MRT
  ORCH --> CASE
  ORCH --> EVAL
  MRT --> LLMR
  MRT --> LLMS
  MRT --> EMB
  MRT --> RERANK
  GW -.authz.-> PDP
  ORCH -.authz.-> PDP
  ORCH --> AUDIT
  EVAL --> REG
  REG --> APOLLO
```

### 2) Restricted-Network Enforcement Model
- **Default deny egress** at host firewall + CNI/NetworkPolicy.
- **Allowlist-only internal DNS** for model/tool endpoints.
- **No external model APIs** in production runtime profiles.
- **DLP preflight** before model and tool invocation.
- **Prompt/output hashing** and signed audit events.
- **Sidecar policy checks** (PDP call before every sensitive tool action).

### 3) Logical Component Boundaries
- **Frontend layer:** secure mission UX, approval queue, provenance views.
- **Backend layer:** orchestration APIs, case workflows, policy enforcement adapters.
- **Data layer:** Foundry pipelines, ontology, feature materialization, lineage.
- **AI orchestration layer:** planner + specialists + evaluator + guardrails.
- **Policy layer:** ABAC/RBAC/ReBAC, coalition compartments, legal constraints.
- **Observability layer:** logs, metrics, traces, eval dashboards, policy decision traces.
- **Deployment layer:** Apollo progressive delivery, health gates, rollback pins.

---

## Data and Ontology

### 1) Canonical Entity Model (Foundry Ontology)

```python
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List

from pydantic import BaseModel, Field

class Classification(str, Enum):
    U = "UNCLASSIFIED"
    C = "CONFIDENTIAL"
    S = "SECRET"
    TS = "TOP_SECRET"

class Confidence(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    method: str  # model_voting, analyst_verified, sensor_fusion
    rationale: Optional[str] = None

class LineageRef(BaseModel):
    dataset_rid: str
    transform_rid: str
    input_record_ids: List[str]
    output_record_id: str
    commit_sha: str
    timestamp: datetime

class MissionScope(BaseModel):
    mission_id: str
    coalition_id: str
    compartments: List[str]
    caveats: List[str] = []

class Entity(BaseModel):
    entity_id: str
    entity_type: str  # Person, Organization, Device, Vehicle, Location, Event, Account
    canonical_name: str
    aliases: List[str] = []
    attributes: Dict[str, str] = {}
    first_seen_at: datetime
    last_seen_at: datetime
    classification: Classification
    mission_scope: MissionScope
    confidence: Confidence
    lineage: LineageRef

class Relationship(BaseModel):
    relationship_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str  # owns, controls, traveled_to, transferred_to, contacted
    valid_from: datetime
    valid_to: Optional[datetime] = None
    temporal_state: str  # active, stale, revoked
    confidence: Confidence
    mission_scope: MissionScope
    lineage: LineageRef
```

### 2) Permission Semantics in Ontology
- **Row-level:** entity visibility by mission + coalition + clearance.
- **Column-level:** redact sensitive attributes (e.g., HUMINT source ids).
- **Entity-level:** operation rights (`read`, `link`, `escalate`, `open_case`).
- **Relationship-level:** cross-compartment traversal constraints.

### 3) Ontology-Driven Workflow Control
- Agents receive **context envelopes** built from ontology constraints.
- Retrieval engine enforces `mission_scope` + `classification <= clearance` filters.
- Case actions derive legal/policy obligations from entity/relationship tags.

---

## AI and Agent Design

### 1) Agent Topology (AIP)
- **Analyst Copilot:** investigation assistance, timeline synthesis, hypothesis support.
- **Commander Copilot:** option generation, action packages, decision impact previews.
- **Triage Agent:** event severity ranking and queue placement.
- **Enrichment Agent:** entity resolution, context expansion, confidence recalibration.
- **Correlation Agent:** pattern detection across time/entity/mission graphs.
- **Recommendation Agent:** recommends actions with alternatives and confidence deltas.
- **Compliance Agent:** pre-action legal/policy checks and evidence pack validation.

### 2) Tool-Use Contract with Policy Gate

```python
from dataclasses import dataclass
from typing import Any, Dict, Protocol

@dataclass
class AuthContext:
    actor_id: str
    mission_id: str
    coalition_id: str
    clearance: str
    compartments: list[str]

@dataclass
class ToolCall:
    name: str
    args: Dict[str, Any]
    auth: AuthContext

@dataclass
class ToolOutcome:
    ok: bool
    data: Dict[str, Any]
    policy_trace_id: str
    audit_event_id: str

class PDP(Protocol):
    def authorize(self, subject: dict, action: str, resource: dict, context: dict) -> dict: ...

class AuditLog(Protocol):
    def append(self, event: dict) -> str: ...

class ToolRuntime:
    def __init__(self, pdp: PDP, audit: AuditLog, tool_registry: Dict[str, Any]):
        self.pdp = pdp
        self.audit = audit
        self.tool_registry = tool_registry

    def execute(self, call: ToolCall) -> ToolOutcome:
        decision = self.pdp.authorize(
            subject={
                "actor_id": call.auth.actor_id,
                "clearance": call.auth.clearance,
                "compartments": call.auth.compartments,
            },
            action=f"tool:{call.name}",
            resource={"mission_id": call.auth.mission_id, "coalition_id": call.auth.coalition_id},
            context=call.args,
        )
        if not decision["allow"]:
            event_id = self.audit.append({"type": "tool_denied", "tool": call.name, "decision": decision})
            return ToolOutcome(False, {"error": "policy_denied"}, decision["trace_id"], event_id)

        handler = self.tool_registry[call.name]
        result = handler(**call.args)
        event_id = self.audit.append({"type": "tool_executed", "tool": call.name, "result_meta": str(type(result))})
        return ToolOutcome(True, {"result": result}, decision["trace_id"], event_id)
```

### 3) Operational Approval Gates
Any operation with mission impact (`open_case`, `task_asset`, `issue_alert`, `escalate`) must pass:
1. policy check,
2. confidence threshold,
3. human approval,
4. post-action audit seal.

---

## Self-Improvement Loop

### 1) Signal Capture
Inputs captured continuously:
- Analyst feedback (`accept`, `edit`, `reject`, free-text rationale)
- Operator corrections (entity merge/split, relationship edits)
- Query logs + retrieval misses
- Alert outcomes (TP/FP/FN) and mission outcomes
- Latency and tool-failure telemetry

### 2) Improvement Artifacts
- Prompt candidates (instruction deltas)
- Workflow graph candidates (state/transition updates)
- Router policies (model/tool selection rules)
- Confidence calibration tables
- Guardrail rule refinements

### 3) Lifecycle
1. Candidate generated from feedback miner.
2. Candidate versioned in registry (`prompt_v`, `workflow_v`, `router_v`).
3. Offline eval (quality + safety + latency + policy compliance).
4. Human review board approval.
5. Apollo canary rollout (1% → 10% → 50% → 100%).
6. Drift monitor and auto-rollback on breach.

### 4) Improvement Controller (Python)

```python
from dataclasses import dataclass

@dataclass
class EvalScore:
    precision: float
    recall: float
    p95_latency_ms: int
    trust_score: float
    policy_violations: int

class UpgradeGuard:
    def __init__(self, max_latency_delta=100, max_recall_drop=0.005):
        self.max_latency_delta = max_latency_delta
        self.max_recall_drop = max_recall_drop

    def approve(self, base: EvalScore, cand: EvalScore) -> tuple[bool, str]:
        if cand.policy_violations > 0:
            return False, "policy violations present"
        if cand.precision < base.precision:
            return False, "precision regression"
        if cand.recall < base.recall - self.max_recall_drop:
            return False, "recall regression"
        if cand.p95_latency_ms - base.p95_latency_ms > self.max_latency_delta:
            return False, "latency regression"
        if cand.trust_score < base.trust_score:
            return False, "operator trust regression"
        return True, "approved"
```

### 5) Drift Detection
- Monitor feature distribution shift (PSI/KS).
- Monitor output calibration drift.
- Monitor policy-denial rate anomalies.
- Trigger rollback when thresholds crossed for N consecutive windows.

---

## Full-Stack Implementation

### 1) Web UI (React + TypeScript)
- Mission workbench: event stream + graph timeline + case pane.
- Copilot panel: recommendations, confidence, rationale, provenance.
- Approval center: one-click approve/reject with reason capture.
- Audit explorer: searchable policy traces and model/prompt versions.

### 2) API Gateway
Responsibilities:
- JWT validation + mTLS service auth
- Request classification and DLP pre-scan
- Rate-limit by tenant/mission
- Attach policy context headers for downstream services

### 3) Backend Services (Python/FastAPI)
- `orchestrator-service`
- `case-service`
- `ontology-query-service`
- `policy-adapter-service`
- `eval-service`
- `audit-service`

```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel

app = FastAPI(title="artemis-orchestrator")

class RecommendRequest(BaseModel):
    mission_id: str
    event_id: str
    actor_id: str

@app.post("/v1/recommend")
def recommend(req: RecommendRequest):
    # 1) hydrate context from Foundry/ontology
    # 2) retrieve scoped evidence
    # 3) run triage+correlation agents
    # 4) return recommendation package
    return {
        "mission_id": req.mission_id,
        "event_id": req.event_id,
        "status": "recommended",
        "requires_approval": True,
    }
```

### 4) Event Bus / Streaming
Topic taxonomy:
- `intel.raw.events`
- `intel.triaged.events`
- `intel.enriched.events`
- `intel.correlated.events`
- `agent.recommendations`
- `operator.approvals`
- `mission.outcomes`
- `eval.regression.alerts`

### 5) Data Warehouse/Lakehouse
- Bronze/Silver/Gold patterns for batch + streaming convergence.
- Time-travel tables for reproducible investigations and eval replay.
- Feature materialization for models and eval cohorts.

### 6) Search/Retrieval
- Hybrid retrieval pipeline:
  1) ontology graph neighborhood lookup,
  2) vector similarity,
  3) lexical constraints,
  4) policy filter,
  5) rerank.

### 7) Model Router / Inference

```python
from typing import Literal

INTERNAL_ENDPOINTS = {
    "reasoner_v5": "http://reasoner.model.svc.cluster.local:8080",
    "summarizer_v4": "http://summarizer.model.svc.cluster.local:8080",
}

TASK_ROUTE = {
    "triage": "reasoner_v5",
    "correlate": "reasoner_v5",
    "summarize": "summarizer_v4",
}

def route(task: Literal["triage", "correlate", "summarize"]) -> str:
    model_key = TASK_ROUTE[task]
    return INTERNAL_ENDPOINTS[model_key]
```

### 8) Observability
- OpenTelemetry traces across UI→API→agent→tool path.
- SLO dashboards: `p95 latency`, `precision@k`, `policy violation rate`, `approval cycle time`.
- Eval dashboards: baseline vs candidate by mission/cohort.

---

## Security and Governance

### 1) Need-to-Know Enforcement
- ABAC (clearance + compartment + mission role) + RBAC (functional role).
- ReBAC for relationship traversal permissions in graph operations.
- Coalition boundary policies with explicit cross-domain release workflows.

### 2) Policy-as-Code (Rego)

```rego
package artemis.authz

default allow = false

allow {
  input.subject.clearance_rank >= input.resource.classification_rank
  input.subject.mission_roles[_] == "intel_operator"
  input.subject.compartments[_] == input.resource.compartment
  input.action == "tool:open_case"
  input.context.mission_id == input.resource.mission_id
}

deny_reason[msg] {
  not allow
  msg := "insufficient clearance or mission scope"
}
```

### 3) Immutable Provenance + Audit
- Every event includes:
  - `prompt_version`, `workflow_version`, `model_version`
  - `retrieval_doc_ids`, `policy_trace_id`, `actor_id`
  - `input_hash`, `output_hash`, `timestamp`, `signature`
- Store in append-only ledger + periodic cryptographic checkpointing.

### 4) Zero-Trust Runtime Controls
- mTLS between all services.
- Workload identity with short-lived certs.
- No long-lived static credentials.
- Signed container images and attestations enforced by admission policy.

---

## Code Examples

### A) Event Handler + Workflow State Machine

```python
from enum import Enum
from dataclasses import dataclass

class State(str, Enum):
    INGESTED = "INGESTED"
    TRIAGED = "TRIAGED"
    ENRICHED = "ENRICHED"
    CORRELATED = "CORRELATED"
    RECOMMENDED = "RECOMMENDED"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    APPROVED = "APPROVED"
    EXECUTED = "EXECUTED"
    CLOSED = "CLOSED"

ALLOWED_TRANSITIONS = {
    State.INGESTED: {State.TRIAGED},
    State.TRIAGED: {State.ENRICHED},
    State.ENRICHED: {State.CORRELATED},
    State.CORRELATED: {State.RECOMMENDED},
    State.RECOMMENDED: {State.APPROVAL_PENDING, State.CLOSED},
    State.APPROVAL_PENDING: {State.APPROVED, State.CLOSED},
    State.APPROVED: {State.EXECUTED},
    State.EXECUTED: {State.CLOSED},
}

@dataclass
class WorkflowEvent:
    mission_id: str
    event_id: str
    state: State


def transition(current: State, nxt: State) -> State:
    if nxt not in ALLOWED_TRANSITIONS.get(current, set()):
        raise ValueError(f"illegal transition {current}->{nxt}")
    return nxt
```

### B) Ontology-Scoped SQL Query

```sql
SELECT e.entity_id,
       e.canonical_name,
       r.relationship_type,
       r.target_entity_id,
       r.confidence_score
FROM ontology_entities e
JOIN ontology_relationships r ON r.source_entity_id = e.entity_id
WHERE e.mission_id = :mission_id
  AND e.coalition_id = :coalition_id
  AND e.classification_rank <= :user_clearance_rank
  AND :user_compartment = ANY(e.compartments)
  AND r.valid_to IS NULL
ORDER BY r.confidence_score DESC
LIMIT 200;
```

### C) DLP Scrubber (Source/Secret Leakage Prevention)

```python
import re

PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA|EC|OPENSSH) PRIVATE KEY-----"),
    re.compile(r"(?i)(password|token|secret|apikey)\s*[:=]\s*\S+"),
    re.compile(r"(?i)(client_secret|db_uri|jdbc:postgresql://\S+)"),
]


def scrub(text: str) -> str:
    redacted = text
    for pattern in PATTERNS:
        redacted = pattern.sub("[REDACTED_SECRET]", redacted)
    return redacted
```

### D) Eval Pipeline Skeleton

```python
class EvalPipeline:
    def __init__(self, retriever, agent_runner, scorer):
        self.retriever = retriever
        self.agent_runner = agent_runner
        self.scorer = scorer

    def run_suite(self, suite_name: str, config_version: str) -> dict:
        items = self.retriever.load_eval_suite(suite_name)
        predictions = [self.agent_runner.run(item, config_version) for item in items]
        metrics = self.scorer.compute(predictions, items)
        return {
            "suite": suite_name,
            "config_version": config_version,
            "metrics": metrics,
        }
```

---

## Scenario Walkthrough

### Incident: Cross-Border Illicit Transfer Signal
1. A live event arrives on `intel.raw.events` from a maritime sensor feed.
2. Triage Agent scores severity 0.92 due to matched route + flagged entity.
3. Enrichment Agent resolves vessel ownership changes from Foundry lineage and Gotham case history.
4. Correlation Agent links the event with three prior transfers via shared intermediary account graph edges.
5. Recommendation Agent drafts:
   - Option A: open priority case + notify coalition partner cell,
   - Option B: continue passive monitoring 6h,
   - with confidence and expected impact.
6. Compliance Agent blocks auto-action because coalition-release policy requires commander approval.
7. Commander approves Option A in the UI; `operator.approvals` emits signed decision record.
8. Case-service executes `open_case`, writes policy trace + immutable audit seal.
9. Outcome after 24h: interception successful; analyst marks recommendation as high quality but requests faster summarization.
10. Improvement loop:
   - feedback miner creates `summarizer_prompt_v28` candidate,
   - eval service shows +2.3% precision@k, -38ms p95,
   - governance approves,
   - Apollo canary deploys to 10%, then 100% with no drift alerts.

---

## Local Assistant Hardening Checklist
- [ ] Disable all external model providers and outbound internet routes.
- [ ] Enforce internal endpoint allowlist for model and tool domains.
- [ ] Apply DLP scrubber pre-prompt, pre-tool, and pre-log sink.
- [ ] Require policy decision token for every sensitive tool call.
- [ ] Persist signed immutable audit trail for prompts/tools/outputs.
- [ ] Enforce human approval for mission-impactful operations.
- [ ] Gate upgrades through eval + governance + Apollo staged rollout.
- [ ] Enable drift-triggered automatic rollback with postmortem capture.

This blueprint gives **ClearGlassInc Artemis** a concrete, implementation-ready path to secure local AI operations with controlled self-improvement and mission-grade reliability.

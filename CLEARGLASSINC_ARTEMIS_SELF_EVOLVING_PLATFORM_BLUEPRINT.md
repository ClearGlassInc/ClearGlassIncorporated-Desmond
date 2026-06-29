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

## Python-First Precision Reference Implementation

This section turns the blueprint into an implementation-oriented skeleton. It intentionally keeps all operationally significant actions behind explicit policy and human approval gates. Palantir terminology used here:

- **Gotham**: operational intelligence workspace for investigations, link analysis, entity tracking, case management, and mission timelines.
- **Foundry**: governed data integration and ontology platform for pipelines, data products, transforms, lineage, permissions, and operational applications.
- **AIP**: AI Platform layer for copilots, agent tools, model routing, evaluations, prompt governance, and automated workflows.
- **Apollo**: controlled deployment, runtime configuration, rollout, rollback, and fleet health management across secure environments.

### End-to-end service map

```text
clear-glass-artemis/
  apps/
    analyst-console/              # React/TypeScript operator UI
    commander-cop/                # mission common operating picture
    governance-console/           # prompt/workflow/model approval UI
  services/
    api-gateway/                  # FastAPI edge API, auth context, rate limits
    ingest-gateway/               # signed feed admission + schema validation
    triage-service/               # deterministic scoring + alert creation
    ontology-service/             # policy-filtered Foundry/Gotham graph access
    agent-orchestrator/           # AIP tool contracts + workflow state machines
    eval-service/                 # offline/shadow evals + promotion guardrails
    feedback-service/             # operator corrections + outcome ingestion
    policy-service/               # OPA/Rego + mission-context decisions
    audit-service/                # immutable append-only audit log
  infra/
    apollo/                       # deployment rings, canaries, rollback policies
    policies/                     # policy-as-code bundles
    observability/                # metrics, traces, dashboards, SLOs
  ontology/
    objects.yaml                  # Foundry ontology object definitions
    links.yaml                    # ontology relationship definitions
    actions.yaml                  # ontology-backed action definitions
  evals/
    datasets/                     # immutable eval snapshots
    rubrics/                      # scoring rubrics and mission KPIs
    candidates/                   # proposed prompt/workflow/router versions
```

### Precision event contract

Every live or historical observation is normalized before it can affect cases, recommendations, or evals. The same contract feeds Foundry transforms, Gotham case links, and AIP tool calls.

```python
# services/common/contracts.py
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class Classification(str, Enum):
    UNCLASSIFIED = "UNCLASSIFIED"
    CONTROLLED = "CONTROLLED"
    SECRET = "SECRET"
    COALITION_RESTRICTED = "COALITION_RESTRICTED"


class Provenance(BaseModel):
    source_system: str
    source_record_id: str
    transform_version: str
    lineage_hash: str
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MissionScope(BaseModel):
    mission_id: str
    compartments: set[str] = Field(default_factory=set)
    coalition: set[str] = Field(default_factory=set)
    classification: Classification


class ObservationEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    event_time: datetime
    ingest_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    mission: MissionScope
    confidence: float = Field(ge=0.0, le=1.0)
    payload: dict[str, Any]
    provenance: Provenance

    @field_validator("event_type")
    @classmethod
    def event_type_must_be_namespaced(cls, value: str) -> str:
        if "." not in value:
            raise ValueError("event_type must be namespaced, e.g. sensor.rf.anomaly")
        return value


class Recommendation(BaseModel):
    rec_id: UUID = Field(default_factory=uuid4)
    case_id: str
    action_type: str
    rationale: str
    evidence_ids: list[str]
    risk_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    approval_required: Literal[True] = True
```

### Foundry ontology objects and guarded actions

```yaml
# ontology/objects.yaml
objects:
  ArtemisMission:
    primaryKey: mission_id
    properties:
      mission_id: string
      name: string
      priority: integer
      classification: string
      coalition_scope: array<string>
      active_from: timestamp
      active_to: timestamp?

  ArtemisEvent:
    primaryKey: event_id
    properties:
      event_id: string
      event_type: string
      event_time: timestamp
      ingest_time: timestamp
      confidence: double
      raw_payload_ref: string
      source_system: string
      lineage_hash: string
      classification: string
      mission_id: string

  ArtemisCase:
    primaryKey: case_id
    properties:
      case_id: string
      mission_id: string
      status: string
      severity: string
      owner: string
      sla_due_at: timestamp
      created_at: timestamp

  ArtemisRecommendation:
    primaryKey: rec_id
    properties:
      rec_id: string
      case_id: string
      action_type: string
      rationale: string
      evidence_ids: array<string>
      risk_score: double
      confidence: double
      status: string
      model_version: string
      prompt_version: string
```

```yaml
# ontology/actions.yaml
actions:
  open_case_from_alert:
    object: ArtemisAlert
    requiredPermissions: ["case:create"]
    writes: [ArtemisCase, AuditEvent]
    approval: false

  approve_recommendation:
    object: ArtemisRecommendation
    requiredPermissions: ["recommendation:approve"]
    writes: [ApprovalDecision, AuditEvent]
    approval: true
    policyChecks:
      - mission_scope_allows_user
      - classification_allows_user
      - coalition_boundary_allows_release
      - recommendation_has_evidence
```

### Policy-enforced ontology query path

AIP agents never receive direct database credentials. They call tools. Tools call ontology services. Ontology services attach user, mission, classification, and coalition context to every query.

```python
# services/ontology_service/query.py
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class UserContext:
    user_id: str
    roles: frozenset[str]
    clearances: frozenset[str]
    compartments: frozenset[str]
    coalition: frozenset[str]


def build_scope_filter(user: UserContext, mission_id: str) -> dict[str, Any]:
    return {
        "mission_id": mission_id,
        "classification__in": sorted(user.clearances),
        "compartments__overlap": sorted(user.compartments),
        "coalition_scope__overlap": sorted(user.coalition),
    }


async def query_case_graph(case_id: str, mission_id: str, user: UserContext) -> dict[str, Any]:
    scope_filter = build_scope_filter(user, mission_id)
    # Adapter can target Foundry Ontology SDK, Gotham APIs, or a test double.
    graph = await foundry_ontology.search_links(
        start_object="ArtemisCase",
        start_key=case_id,
        link_types=[
            "CASE_HAS_ALERT",
            "ALERT_FROM_EVENT",
            "EVENT_OBSERVED_ACTOR",
            "EVENT_TARGETED_ASSET",
            "CASE_HAS_RECOMMENDATION",
        ],
        filters=scope_filter,
        max_depth=3,
    )
    await audit.write(
        event_type="ontology.query",
        actor=user.user_id,
        resource=case_id,
        decision="ALLOW",
        attributes={"mission_id": mission_id, "links": len(graph.get("links", []))},
    )
    return graph
```

### Agent orchestration with approval gates

```python
# services/agent_orchestrator/workflows.py
from enum import Enum
from pydantic import BaseModel


class Step(str, Enum):
    INTAKE = "INTAKE"
    TRIAGE = "TRIAGE"
    ENRICH = "ENRICH"
    CORRELATE = "CORRELATE"
    RECOMMEND = "RECOMMEND"
    POLICY_GATE = "POLICY_GATE"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    EXECUTE_APPROVED = "EXECUTE_APPROVED"
    LEARN = "LEARN"


class WorkflowState(BaseModel):
    case_id: str
    current: Step
    completed: list[Step] = []
    blocked_reason: str | None = None


TRANSITIONS = {
    Step.INTAKE: {Step.TRIAGE},
    Step.TRIAGE: {Step.ENRICH},
    Step.ENRICH: {Step.CORRELATE},
    Step.CORRELATE: {Step.RECOMMEND},
    Step.RECOMMEND: {Step.POLICY_GATE},
    Step.POLICY_GATE: {Step.HUMAN_APPROVAL},
    Step.HUMAN_APPROVAL: {Step.EXECUTE_APPROVED, Step.LEARN},
    Step.EXECUTE_APPROVED: {Step.LEARN},
}


def transition(state: WorkflowState, next_step: Step) -> WorkflowState:
    if next_step not in TRANSITIONS[state.current]:
        raise ValueError(f"Invalid transition {state.current} -> {next_step}")
    return state.model_copy(update={"current": next_step, "completed": [*state.completed, state.current]})
```

```python
# services/agent_orchestrator/tools.py
from typing import Protocol


class PolicyClient(Protocol):
    async def decide(self, action: str, subject: dict, resource: dict) -> dict: ...


async def propose_recommendation_tool(
    *,
    case_id: str,
    action_type: str,
    rationale: str,
    evidence_ids: list[str],
    user: UserContext,
    policy: PolicyClient,
) -> Recommendation:
    decision = await policy.decide(
        action="recommendation:propose",
        subject={"user_id": user.user_id, "roles": list(user.roles)},
        resource={"case_id": case_id, "evidence_ids": evidence_ids, "action_type": action_type},
    )
    if decision["allow"] is not True:
        raise PermissionError(decision.get("reason", "policy denied"))
    rec = Recommendation(
        case_id=case_id,
        action_type=action_type,
        rationale=rationale,
        evidence_ids=evidence_ids,
        risk_score=decision.get("risk_score", 1.0),
        confidence=decision.get("confidence", 0.5),
    )
    await recommendation_store.put(rec)
    await approval_queue.enqueue(rec)
    return rec
```

### Self-improvement pipeline implementation

The system can propose prompt, workflow, heuristic, and routing changes, but it cannot unilaterally promote them into mission production. Promotion requires eval gates, policy gates, immutable audit, and human signoff.

```python
# services/eval_service/promotion.py
from dataclasses import dataclass


@dataclass(frozen=True)
class EvalMetrics:
    precision: float
    recall: float
    f1: float
    p95_latency_ms: float
    operator_trust: float
    policy_violations: int
    unsafe_tool_calls: int


@dataclass(frozen=True)
class PromotionGuardrails:
    min_precision: float = 0.92
    min_recall: float = 0.84
    max_p95_latency_ms: float = 1500.0
    min_operator_trust: float = 4.2
    max_policy_violations: int = 0
    max_unsafe_tool_calls: int = 0


def evaluate_candidate(candidate: EvalMetrics, baseline: EvalMetrics, guards: PromotionGuardrails) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if candidate.precision < guards.min_precision or candidate.precision < baseline.precision - 0.01:
        reasons.append("precision regression")
    if candidate.recall < guards.min_recall or candidate.recall < baseline.recall - 0.02:
        reasons.append("recall regression")
    if candidate.p95_latency_ms > guards.max_p95_latency_ms:
        reasons.append("latency budget exceeded")
    if candidate.operator_trust < guards.min_operator_trust:
        reasons.append("operator trust below threshold")
    if candidate.policy_violations > guards.max_policy_violations:
        reasons.append("policy violation detected")
    if candidate.unsafe_tool_calls > guards.max_unsafe_tool_calls:
        reasons.append("unsafe tool call detected")
    return (len(reasons) == 0, reasons)


async def propose_self_upgrade(candidate_version: str, baseline_version: str) -> dict:
    candidate = await eval_store.metrics_for(candidate_version)
    baseline = await eval_store.metrics_for(baseline_version)
    ok, reasons = evaluate_candidate(candidate, baseline, PromotionGuardrails())
    proposal = {
        "candidate_version": candidate_version,
        "baseline_version": baseline_version,
        "eligible_for_review": ok,
        "blocking_reasons": reasons,
        "required_signoffs": ["Mission Owner", "AI Governance Lead", "Security Officer"] if ok else [],
    }
    await audit.write(event_type="self_upgrade.proposed", actor="eval-service", resource=candidate_version, decision="REVIEW" if ok else "BLOCK", attributes=proposal)
    return proposal
```

```sql
-- evals/schema.sql
CREATE TABLE feedback_signal (
  feedback_id TEXT PRIMARY KEY,
  rec_id TEXT NOT NULL,
  case_id TEXT NOT NULL,
  operator_id TEXT NOT NULL,
  signal_type TEXT NOT NULL CHECK (signal_type IN ('ACCEPT','REJECT','EDIT','OUTCOME','TRUST_SCORE')),
  label TEXT,
  correction JSONB,
  mission_outcome JSONB,
  prompt_version TEXT NOT NULL,
  workflow_version TEXT NOT NULL,
  model_version TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE upgrade_proposal (
  proposal_id TEXT PRIMARY KEY,
  artifact_type TEXT NOT NULL CHECK (artifact_type IN ('PROMPT','WORKFLOW','ROUTER','HEURISTIC','MODEL_CONFIG')),
  candidate_version TEXT NOT NULL,
  baseline_version TEXT NOT NULL,
  eval_snapshot_id TEXT NOT NULL,
  diff_summary TEXT NOT NULL,
  guardrail_status TEXT NOT NULL CHECK (guardrail_status IN ('PASS','FAIL','NEEDS_REVIEW')),
  approval_status TEXT NOT NULL CHECK (approval_status IN ('DRAFT','PENDING','APPROVED','REJECTED','ROLLED_BACK')),
  created_by TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Apollo deployment and rollback control

```yaml
# infra/apollo/artemis-agent-orchestrator.yaml
service: artemis-agent-orchestrator
artifact: registry.clearglass.internal/artemis/agent-orchestrator:${VERSION}
rings:
  - name: dev
    autoPromote: true
  - name: staging
    requires:
      - evals.pass == true
      - policy.bundle.signed == true
  - name: mission-canary
    trafficPercent: 10
    requires:
      - approvals.mission_owner == true
      - approvals.ai_governance_lead == true
    rollbackOn:
      - metric: policy_violations
        op: ">"
        value: 0
      - metric: p95_latency_ms
        op: ">"
        value: 1500
      - metric: operator_rejection_rate
        op: ">"
        value: 0.35
  - name: production
    requires:
      - canary.health == "GREEN"
      - audit.exported == true
```

### Observability and eval dashboard metrics

```python
# services/common/telemetry.py
from opentelemetry import metrics, trace

tracer = trace.get_tracer("clearglass.artemis")
meter = metrics.get_meter("clearglass.artemis")

recommendation_latency = meter.create_histogram("recommendation_latency_ms")
policy_denials = meter.create_counter("policy_denials_total")
operator_overrides = meter.create_counter("operator_overrides_total")
self_upgrade_rollbacks = meter.create_counter("self_upgrade_rollbacks_total")


def record_recommendation_metrics(*, latency_ms: float, accepted: bool, prompt_version: str) -> None:
    recommendation_latency.record(latency_ms, {"prompt_version": prompt_version})
    if not accepted:
        operator_overrides.add(1, {"prompt_version": prompt_version})
```

### Cinematic operational walkthrough

1. A live, coalition-tagged event enters the ingest gateway with a signed provenance bundle and a `COALITION_RESTRICTED` mission scope. The ingest gateway validates schema, stamps lineage, and writes the normalized event to the streaming bus and Foundry raw dataset.
2. The triage service computes deterministic features, attaches prior case context from Gotham, and creates an alert only after confidence, source reliability, and mission priority thresholds are met.
3. AIP launches the intake, enrichment, correlation, and recommender agents. Each agent uses policy-enforced tools, not raw data credentials.
4. The recommender creates an evidence-backed action package with linked ontology facts, confidence intervals, uncertainty notes, and an explicit `approval_required=true` flag.
5. The policy service blocks any cross-coalition data exposure and requires a commander approval because the recommendation could alter operational posture.
6. The commander approves the low-risk monitoring action and rejects the escalation branch, adding a structured correction: “evidence supports watch, not escalation.”
7. The feedback service converts the correction into eval labels: accepted monitoring = positive label, rejected escalation = negative label, rationale quality = partial credit.
8. The eval service generates a candidate prompt that raises the escalation evidence threshold and improves uncertainty language. Offline evals pass, shadow deployment shows lower false positives, and an upgrade proposal is sent to the governance console.
9. Human approvers sign the change. Apollo deploys to the mission-canary ring. If policy violations, latency, or rejection rate regress, Apollo rolls back automatically and records the rollback in immutable audit.
10. The platform gets better by learning decision boundaries, evidence presentation, routing latency, and workflow sequencing while never changing mission goals or executing significant actions without human approval.


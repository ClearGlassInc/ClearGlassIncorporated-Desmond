# ClearGlassInc Artemis — Self-Evolving AI Intelligence Platform

## System Architecture

### 1) Platform Topology (Palantir-Aligned)

```text
[Mission UI (Web/Command)]
        |
[API Gateway + BFF (TS)] -- [AuthN/AuthZ + PDP/PEP]
        |
  [Domain Services (Python/FastAPI)]
        |
[Event Bus (Kafka/PubSub)] ---- [Workflow Engine (Temporal/Foundry Functions)]
        |                                      |
[Lakehouse + Foundry Datasets]          [AIP Agent Orchestrator]
        |                                      |
[Ontology + Knowledge Graph] <----> [Model Router + Tool Registry]
        |
[Search/RAG: lexical+vector+graph retrieval]
        |
[Observability + Evals + Drift + Governance]
        |
[Apollo Delivery: staged rollout, canary, rollback]
```

### 2) Layer-by-layer implementation blueprint

- **Frontend layer**: React/TypeScript mission console with role-aware widgets (watchlist, case board, timeline, map, confidence overlays).
- **Backend/API layer**: FastAPI services behind API Gateway. BFF pattern for UI aggregation.
- **Data layer**: Foundry pipelines for batch + streaming ingest, quality checks, schema contracts.
- **Ontology layer**: Entities/relations as typed ontology objects used by analysts + agents.
- **AI orchestration layer**: AIP copilots, multi-agent plans, tool-use constraints, approval gates.
- **Policy layer**: Policy-as-code (OPA/Rego + Foundry policy bindings) for row/column/entity/action control.
- **Observability layer**: OpenTelemetry traces, eval dashboards, model/perf regression monitors.
- **Deployment layer**: Apollo ring deployments (dev->staging->ops), signed artifacts, instant rollback.

### 3) Service map

| Service | Stack | Purpose |
|---|---|---|
| `mission-ui` | React/TS | Operator/commander interface |
| `api-gateway` | Envoy/Kong | Routing, authn, rate limit |
| `intel-api` | FastAPI | Cases, alerts, entities APIs |
| `ontology-service` | Python | Ontology writes/reads + lineage |
| `agent-orchestrator` | AIP SDK | Multi-agent execution + approvals |
| `model-router` | Python | Model/prompt/workflow selection |
| `eval-engine` | Python + SQL | Continuous evals and scorecards |
| `feedback-service` | FastAPI | Captures corrections and outcomes |
| `policy-engine` | OPA/Rego | PDP decisions + explainability |
| `audit-ledger` | Append-only store | Immutable action/provenance logs |

---

## Data and Ontology

### 1) Core ontology primitives

#### Entities
- `Person`, `Organization`, `Asset`, `Device`, `Location`, `Event`, `Signal`, `Case`, `Mission`, `Report`, `ActionPackage`, `Indicator`.

#### Relationships
- `ASSOCIATED_WITH`, `OWNS`, `USES`, `LOCATED_AT`, `PARTICIPATED_IN`, `TRIGGERED`, `INVESTIGATES`, `SUPPORTS_MISSION`, `DERIVED_FROM`.

#### Required metadata on every node/edge
- `confidence_score` (0–1)
- `source_refs[]`
- `lineage_id`
- `first_seen_at`, `last_seen_at`
- `valid_time` and `transaction_time` (bitemporal)
- `classification`, `compartment`, `coalition_tags[]`
- `policy_labels[]`

### 2) Example ontology schema (SQL + graph mapping)

```sql
create table ontology_entity (
  entity_id uuid primary key,
  entity_type text not null,
  canonical_name text not null,
  attrs jsonb not null default '{}',
  confidence numeric(4,3) not null,
  classification text not null,
  coalition_tags text[] not null default '{}',
  lineage_id uuid not null,
  valid_start timestamptz,
  valid_end timestamptz,
  tx_start timestamptz not null default now(),
  tx_end timestamptz,
  created_by text not null
);

create table ontology_relation (
  rel_id uuid primary key,
  src_entity_id uuid not null,
  rel_type text not null,
  dst_entity_id uuid not null,
  confidence numeric(4,3) not null,
  evidence jsonb not null default '[]',
  lineage_id uuid not null,
  valid_start timestamptz,
  valid_end timestamptz,
  tx_start timestamptz not null default now(),
  tx_end timestamptz
);
```

### 3) How ontology drives humans + AI

- Human analysts navigate **entity-centric workspaces**; every view resolves through ontology permissions.
- Agents call tools that are ontology-scoped (`get_entity_neighbors`, `open_case`, `draft_report`).
- Confidence + lineage gates what AI can recommend vs what requires manual verification.
- Mission context selects retrieval subgraphs and coalition-safe views.

---

## AI and Agent Design

### 1) Copilot modes

- **Analyst Copilot**: explains links, proposes hypotheses, drafts intel notes.
- **Commander Copilot**: mission risk summary, decision options, likely impact.
- **Watch Officer Copilot**: real-time triage and escalation recommendations.

### 2) Multi-agent workflow

1. **Triage Agent**: classifies event severity and mission relevance.
2. **Enrichment Agent**: resolves entities, attaches evidence, computes confidence.
3. **Correlation Agent**: finds cross-case links and anomaly patterns.
4. **Summarization Agent**: produces role-based briefing.
5. **Recommendation Agent**: produces action package with confidence + policy checks.

### 3) Tool-using agent contract

```python
from pydantic import BaseModel, Field
from typing import Literal, List

class ToolCall(BaseModel):
    name: Literal[
        "query_ontology", "search_intel", "open_case",
        "create_action_package", "submit_for_approval"
    ]
    args: dict
    reason: str

class AgentDecision(BaseModel):
    objective: str
    calls: List[ToolCall]
    confidence: float = Field(ge=0.0, le=1.0)
    needs_human_approval: bool
```

### 4) Approval gates for consequential actions

- Auto-executable: low-risk summarization/enrichment.
- Human-required: case creation in sensitive compartments, cross-coalition dissemination, operational recommendations.
- Dual approval: high-impact actions (policy label `OPS_CRITICAL`).

---

## Self-Improvement Loop

### 1) Learning signals captured

- Explicit feedback: thumbs up/down, correction text, edited reports.
- Implicit feedback: time-to-resolution, reopen rate, accepted/rejected recommendations.
- Outcome metrics: mission success tags, false positive/negative adjudication.
- Operational telemetry: latency, token spend, tool-failure rates.

### 2) Improvement pipeline

```text
Signals -> Feature Store -> Eval Set Builder -> Candidate Generator
       -> Offline Evals (quality/safety/cost)
       -> Shadow Deployment -> A/B/C Online Evals
       -> Human Review Board -> Apollo Progressive Rollout
       -> Continuous Monitoring -> Auto-Rollback if guardrails violated
```

### 3) Versioning and rollback model

- Version every artifact: prompt (`p_vN`), workflow graph (`wf_vN`), router policy (`rt_vN`), model config (`m_vN`).
- Store immutable eval reports with signed checksum.
- Rollback triggers:
  - precision drop > 5%
  - policy violations > threshold
  - p95 latency breach > SLO for 3 windows
- Apollo supports ring rollback to last known-good bundle.

### 4) Drift detection

- Data drift: PSI/KS on key features.
- Concept drift: rising disagreement between model confidence and adjudicated outcomes.
- Prompt drift: reduced factual grounding score / increased unsupported claims.

---

## Full-Stack Implementation

### 1) Web UI (TypeScript/React)

```tsx
// src/features/cases/CaseTriagePanel.tsx
export function CaseTriagePanel({ eventId }: { eventId: string }) {
  const { data } = useQuery(["triage", eventId], () => api.get(`/v1/triage/${eventId}`));

  return (
    <section>
      <h3>AI Triage</h3>
      <p>Severity: {data?.severity}</p>
      <p>Confidence: {(data?.confidence * 100).toFixed(1)}%</p>
      <PolicyBadge labels={data?.policy_labels ?? []} />
      <button onClick={() => api.post(`/v1/action-packages/${eventId}/submit`)}>
        Submit for Approval
      </button>
    </section>
  );
}
```

### 2) API Gateway route policy

```yaml
# gateway/routes.yaml
routes:
  - path: /v1/cases/*
    methods: [GET, POST]
    auth:
      required: true
      scopes: [cases:read, cases:write]
    policy:
      enforce_entity_labels: true
      coalition_boundary_check: true
```

### 3) Backend service (Python/FastAPI)

```python
# services/intel_api/main.py
from fastapi import FastAPI, Depends, HTTPException
from .policy import authorize
from .repo import CaseRepo

app = FastAPI()
repo = CaseRepo()

@app.post("/v1/cases/{case_id}/actions")
def create_action(case_id: str, payload: dict, ctx=Depends(authorize("cases:write"))):
    if payload.get("impact") == "high" and not ctx.user.has_dual_authority:
        raise HTTPException(403, "Dual authorization required")
    return repo.create_action(case_id, payload, actor=ctx.user.id)
```

### 4) Event handler and workflow kick-off

```python
# services/streaming/handlers.py
def on_live_signal(event: dict):
    emit("intel.signal.received", event)

    triage_job = {
      "event_id": event["id"],
      "mission_id": event["mission_id"],
      "priority": "realtime"
    }
    emit("workflow.triage.requested", triage_job)
```

### 5) Workflow state machine (Temporal-style)

```python
from enum import Enum

class State(str, Enum):
    INGESTED = "INGESTED"
    TRIAGED = "TRIAGED"
    ENRICHED = "ENRICHED"
    CORRELATED = "CORRELATED"
    RECOMMENDED = "RECOMMENDED"
    APPROVED = "APPROVED"
    EXECUTED = "EXECUTED"
    CLOSED = "CLOSED"

ALLOWED = {
  State.INGESTED: [State.TRIAGED],
  State.TRIAGED: [State.ENRICHED],
  State.ENRICHED: [State.CORRELATED],
  State.CORRELATED: [State.RECOMMENDED],
  State.RECOMMENDED: [State.APPROVED],
  State.APPROVED: [State.EXECUTED],
  State.EXECUTED: [State.CLOSED],
}
```

### 6) Ontology-driven query endpoint

```python
# services/ontology/query.py
def get_case_neighborhood(case_id: str, hops: int, clearance: str):
    cypher = """
    MATCH (c:Case {id: $case_id})-[*1..$hops]-(n)
    WHERE n.classification <= $clearance
    RETURN n LIMIT 500
    """
    return graph.run(cypher, case_id=case_id, hops=hops, clearance=clearance)
```

### 7) Model routing policy

```python
# services/model_router/router.py
from dataclasses import dataclass

@dataclass
class RouteInput:
    task: str
    classification: str
    latency_budget_ms: int
    requires_tool_use: bool


def route(inp: RouteInput) -> str:
    if inp.classification in {"TS", "SCI"}:
        return "onprem-secure-llm-v4"
    if inp.task == "summarization" and inp.latency_budget_ms < 1200:
        return "distilled-brief-8b"
    if inp.requires_tool_use:
        return "planner-toolformer-70b"
    return "general-reasoner-32b"
```

### 8) Policy-as-code (Rego)

```rego
package clearglass.policy

default allow = false

allow {
  input.user.scopes[_] == "cases:read"
  input.resource.classification <= input.user.clearance
  coalition_ok
}

coalition_ok {
  every tag in input.resource.coalition_tags {
    input.user.coalition_tags[_] == tag
  }
}
```

### 9) Eval pipeline (Python + SQL)

```python
# services/evals/run_eval.py
def run_prompt_eval(candidate_prompt_id: str):
    dataset = load_dataset("intel_adjudicated_eval_v12")
    scores = evaluate(candidate_prompt_id, dataset)

    if scores["precision"] < 0.91 or scores["policy_violation_rate"] > 0.002:
        mark_rejected(candidate_prompt_id, scores)
        return "rejected"

    create_shadow_deployment(candidate_prompt_id)
    return "shadow"
```

```sql
-- eval scoreboard
select
  candidate_id,
  avg(precision) as precision,
  avg(recall) as recall,
  percentile_cont(0.95) within group (order by latency_ms) as p95_latency,
  avg(policy_violation::int)::float as policy_violation_rate
from eval_runs
where run_date >= now() - interval '7 day'
group by candidate_id
order by precision desc;
```

---

## Security and Governance

### 1) Zero-trust and least privilege

- Mutual TLS between services.
- Workload identity (short-lived tokens, no static secrets where possible).
- Explicit service-to-service authorization policies.

### 2) Need-to-know controls

- ABAC + RBAC hybrid:
  - role grants base permissions.
  - attributes (clearance, mission assignment, coalition tags) gate data access.
- Row/column/entity-level filtering in all query paths.

### 3) Governance controls

- **Prompt governance**: approved prompt registry, signed versions, change tickets.
- **Model governance**: approved model catalog with risk tiering.
- **Workflow governance**: state-machine signatures + policy lint checks.
- **Audit**: append-only ledger for every tool call, decision, approval, and override.

### 4) Deployment safety (Apollo)

- Progressive rings: Sandbox -> Internal -> Mission Pilot -> Full Ops.
- Automatic canary analysis against SLO + safety KPIs.
- One-click rollback to last approved release bundle.

---

## Code Examples (Integrated)

### 1) Agent tool execution with approval gate

```python
# services/agent_orchestrator/executor.py
def execute_plan(plan, user_ctx):
    for call in plan.calls:
        if is_operationally_significant(call):
            request_id = approvals.create_request(call, actor=user_ctx.user_id)
            return {"status": "pending_approval", "request_id": request_id}

        policy.enforce(user_ctx, call)
        tools.invoke(call.name, call.args)

    return {"status": "completed"}
```

### 2) Feedback ingestion API

```python
# services/feedback/main.py
@app.post("/v1/feedback")
def submit_feedback(payload: FeedbackIn, ctx=Depends(authorize("feedback:write"))):
    event = {
        "type": "operator.feedback",
        "actor": ctx.user.id,
        "target": payload.target_id,
        "rating": payload.rating,
        "correction": payload.correction,
        "timestamp": now_iso(),
    }
    bus.publish("feedback.events", event)
    return {"ok": True}
```

### 3) Auto-generated improvement proposal

```python
# services/improvement/proposer.py
def generate_candidate_changes():
    failures = eval_store.top_failure_modes(window_days=14)
    proposals = []

    for mode in failures:
        proposals.append({
            "type": "prompt_patch",
            "target": mode.prompt_id,
            "patch": synthesize_patch(mode),
            "expected_gain": estimate_gain(mode),
            "risk": estimate_risk(mode),
        })

    return proposals
```

---

## Scenario Walkthrough (Cinematic + Technical)

1. **Live event ingestion**
   - A maritime SIGINT alert enters `intel.signal.received` with mission tag `M-SEA-042`.
2. **Machine-speed triage**
   - Triage Agent scores severity `HIGH`, confidence `0.87`, links to known smuggling network entity cluster.
3. **Enrichment + correlation**
   - Enrichment Agent resolves vessel/device ownership mismatch.
   - Correlation Agent finds 3 prior incidents sharing route + device fingerprint.
4. **Recommendation package**
   - Recommendation Agent drafts an `ActionPackage`: surveillance escalation + coalition notification draft.
5. **Approval gate**
   - Policy engine marks action as `OPS_CRITICAL`; requires dual human approval.
   - Commander approves; legal officer requests minor dissemination redaction.
6. **Execution and outcome capture**
   - Approved package executed; case updated with final outcome and mission impact.
7. **Self-improvement loop activation**
   - System records edits to AI draft, approval timing, and outcome success.
   - Eval engine detects repeated redaction corrections and proposes prompt patch.
8. **Safe upgrade path**
   - Patch runs offline eval -> shadow deployment -> A/B test.
   - Gains: +4.2% precision on dissemination compliance, no latency regression.
   - Human review board approves rollout through Apollo rings.
9. **Audited closure**
   - Full provenance trail preserved: source signal, tool calls, approvals, prompt/model/workflow versions, and final mission result.

---

## Final Implementation Notes

- Build as **policy-first, ontology-centric, evaluation-driven** architecture.
- Let agents optimize execution details, never mission intent or guardrail objectives.
- Every autonomous improvement must be explainable, testable, reversible, and human-approved before operational promotion.


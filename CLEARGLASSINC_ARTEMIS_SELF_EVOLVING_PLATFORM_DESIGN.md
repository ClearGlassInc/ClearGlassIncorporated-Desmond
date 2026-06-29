# ClearGlassInc Artemis — Self-Evolving AI Intelligence Platform

## Executive Intent
ClearGlassInc Artemis is a secure, coalition-aware, multi-domain intelligence platform built on **Palantir Gotham**, **Foundry**, **AIP**, and **Apollo**. Its job is to fuse live and historical data, reason over mission context, coordinate human-approved agent workflows, and safely improve its prompts, workflows, routing logic, and heuristics over time.

Palantir terminology used in this blueprint:
- **Gotham**: operational intelligence, investigations, entity tracking, graph workflows, and mission casework.
- **Foundry**: data integration, pipelines, Ontology, application logic, and governed operational data products.
- **Ontology**: the operational layer that models real-world objects, links, actions, logic, security, and workflows so humans and AI agents work against the same mission model.
- **AIP**: AI copilots, agents, AIP Logic, tool execution, evaluations, and workflow automation over governed data and actions.
- **Apollo**: deployment, upgrade, monitoring, recall, rollback, and runtime control for regulated environments.

Design principles:
1. **Human command authority**: Artemis can recommend improvements and actions, but cannot alter mission goals, bypass policy, or execute operationally significant actions without approval.
2. **Ontology-first intelligence**: agents reason over governed objects, relationships, confidence, lineage, and permissions rather than unstructured context alone.
3. **Self-improvement by evidence**: every prompt/workflow/model-router update must be backed by evals, drift analysis, shadow runs, approval records, and rollback plans.
4. **Coalition-safe operation**: every query, tool call, recommendation, and generated product is filtered by clearance, compartment, mission, jurisdiction, and coalition-sharing constraints.
5. **Machine-speed, audit-grade execution**: streaming triage and enrichment run continuously while immutable logs preserve exactly what happened, why, and under which policy version.

---

## System Architecture

### End-to-End Layer Map

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ ClearGlassInc Artemis Operator Surfaces                                    │
│ React/TypeScript UI • Gotham investigation views • Foundry apps • AIP chat │
└───────────────┬────────────────────────────────────────────────────────────┘
                │ OIDC/JWT + mission context + request provenance
┌───────────────▼────────────────────────────────────────────────────────────┐
│ API Gateway / BFF                                                          │
│ FastAPI • GraphQL facade • WebSockets • policy pre-checks • rate limits    │
└───────────────┬────────────────────────────────────────────────────────────┘
                │
┌───────────────▼────────────────────────────────────────────────────────────┐
│ Mission Services                                                           │
│ case-service • alert-service • entity-service • feedback-service           │
│ recommendation-service • approval-service • intel-product-service          │
└───────┬─────────────┬──────────────────────┬──────────────────────────────┘
        │             │                      │
┌───────▼──────┐ ┌────▼────────────────┐ ┌───▼──────────────────────────────┐
│ Streaming    │ │ Foundry/Gotham       │ │ AIP Orchestration                │
│ Kafka/PubSub │ │ datasets • Ontology  │ │ copilots • agents • evals        │
│ Flink/Ray    │ │ actions • functions  │ │ model router • prompt registry   │
└───────┬──────┘ └────┬────────────────┘ └───┬──────────────────────────────┘
        │             │                      │
┌───────▼─────────────▼──────────────────────▼──────────────────────────────┐
│ Security, Governance, and Observability                                    │
│ OPA policy • ABAC/RBAC • lineage • traces • metrics • immutable audit log  │
└───────────────┬────────────────────────────────────────────────────────────┘
                │
┌───────────────▼────────────────────────────────────────────────────────────┐
│ Apollo Runtime Control                                                     │
│ product releases • environment channels • canary • recall • rollback       │
└────────────────────────────────────────────────────────────────────────────┘
```

### Frontend Layer
- **Analyst Workbench**: graph explorer, timeline, evidence tray, hypothesis board, entity resolution queue, agent transcript diff viewer.
- **Commander Console**: mission status, cross-cell risk posture, pending approvals, recommended action packages, confidence/risk tradeoff explanations.
- **Policy & Governance Console**: prompt version approvals, workflow diffs, eval dashboards, model cards, tool permission manifests.
- **AIP Copilot Panel**: mission-scoped natural language interface that can summarize, query, draft, and propose actions through explicit tool contracts.

### Backend Layer
- **API gateway**: request normalization, auth context propagation, payload validation, policy preflight, idempotency keys, WebSocket subscriptions.
- **Case service**: lifecycle state machine, case graph snapshots, attachments, approvals, operator assignments.
- **Alert service**: streaming alert normalization, triage status, deduplication, severity scoring.
- **Entity service**: ontology object lookups, relationship expansion, confidence updates, entity merge/split requests.
- **AI orchestrator**: agent plan execution, tool routing, prompt rendering, model selection, eval logging.
- **Feedback service**: operator corrections, accept/reject events, edited summaries, mission outcome labels.
- **Improvement service**: converts feedback into eval examples, prompt proposals, router threshold changes, and workflow change requests.

### Data Layer
- **Live ingestion**: sensor feeds, case events, OSINT feeds, cyber telemetry, communications metadata, logistics events, partner reports.
- **Historical ingestion**: prior cases, resolved alerts, labeled outcomes, analyst notes, intelligence products, policy decisions.
- **Lakehouse/datasets**: raw bronze, normalized silver, curated gold mission datasets with full provenance.
- **Streaming layer**: Kafka/PubSub topics partitioned by mission, region, classification, and coalition cell.
- **Retrieval layer**: hybrid search with keyword, graph expansion, vector embeddings, geospatial filters, temporal predicates, and access-aware result filtering.

### Ontology Layer
Foundry Ontology and Gotham operational views expose the same governed mission model:
- Objects: `Person`, `Organization`, `Device`, `Location`, `CyberAsset`, `Observation`, `Alert`, `Case`, `Mission`, `IntelProduct`, `ActionRecommendation`, `PromptVersion`, `WorkflowVersion`.
- Links: `observed_at`, `associated_with`, `communicated_with`, `controls`, `member_of`, `derived_from`, `contradicts`, `supports`, `approved_by`, `deployed_as`.
- Actions: `open_case`, `link_entity`, `request_collection`, `draft_intel_product`, `submit_action_package`, `approve_recommendation`, `reject_recommendation`, `promote_prompt_candidate`.

### AI Orchestration Layer
- **AIP copilots** answer operator questions and operate tools only through permissioned Ontology actions.
- **AIP agents** execute bounded workflows: triage, enrichment, correlation, summarization, recommendation, compliance checking, eval generation.
- **AIP Logic functions** encapsulate repeatable prompt-and-tool chains where no-code governance and monitoring are preferred.
- **Model router** chooses model/runtime by mission risk, classification, latency budget, cost ceiling, and required reasoning depth.

### Policy Layer
- Central policy decision point evaluates every object read, field read, tool call, action, prompt deployment, and generated disclosure.
- Policies include subject attributes, object attributes, environmental attributes, purpose-of-use, mission membership, and coalition-sharing rules.

### Observability Layer
- **Operational metrics**: p50/p95 latency, queue lag, workflow success, alert precision/recall, operator acceptance.
- **AI metrics**: tool success, hallucination flags, citation coverage, calibration, uncertainty quality, eval pass rate.
- **Governance metrics**: policy denials, prompt drift, model drift, rollback frequency, approval SLA, audit completeness.

### Deployment Layer
Apollo manages service releases, agent bundles, prompt packs, workflow definitions, policy bundles, and model-router configs as versioned deployable products:
- `artemis-api-gateway`
- `artemis-agent-runtime`
- `artemis-prompt-pack`
- `artemis-policy-bundle`
- `artemis-workflow-pack`
- `artemis-eval-harness`

---

## Data and Ontology

### Canonical Mission Data Model

```sql
CREATE TYPE confidence_source AS ENUM ('sensor', 'human', 'model', 'partner', 'derived');
CREATE TYPE approval_state AS ENUM ('draft', 'pending_review', 'approved', 'rejected', 'recalled');

CREATE TABLE artemis_entity (
  entity_id UUID PRIMARY KEY,
  entity_type TEXT NOT NULL CHECK (entity_type IN (
    'Person','Organization','Device','Location','CyberAsset','Event','Mission','Case'
  )),
  canonical_name TEXT,
  aliases TEXT[] NOT NULL DEFAULT '{}',
  confidence NUMERIC(5,4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  confidence_source confidence_source NOT NULL,
  first_seen TIMESTAMPTZ NOT NULL,
  last_seen TIMESTAMPTZ NOT NULL,
  temporal_state JSONB NOT NULL DEFAULT '{}',
  mission_tags TEXT[] NOT NULL DEFAULT '{}',
  classification TEXT NOT NULL,
  compartments TEXT[] NOT NULL DEFAULT '{}',
  coalition_scope TEXT NOT NULL,
  lineage JSONB NOT NULL,
  created_by TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE artemis_relationship (
  relationship_id UUID PRIMARY KEY,
  src_entity_id UUID NOT NULL REFERENCES artemis_entity(entity_id),
  dst_entity_id UUID NOT NULL REFERENCES artemis_entity(entity_id),
  relationship_type TEXT NOT NULL,
  confidence NUMERIC(5,4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  valid_from TIMESTAMPTZ,
  valid_to TIMESTAMPTZ,
  evidence_refs UUID[] NOT NULL DEFAULT '{}',
  contradicting_evidence_refs UUID[] NOT NULL DEFAULT '{}',
  mission_context JSONB NOT NULL DEFAULT '{}',
  lineage JSONB NOT NULL,
  classification TEXT NOT NULL,
  compartments TEXT[] NOT NULL DEFAULT '{}',
  coalition_scope TEXT NOT NULL
);

CREATE TABLE artemis_observation (
  observation_id UUID PRIMARY KEY,
  source_system TEXT NOT NULL,
  source_event_id TEXT NOT NULL,
  observed_at TIMESTAMPTZ NOT NULL,
  received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  payload JSONB NOT NULL,
  normalized_payload JSONB NOT NULL,
  geohash TEXT,
  embedding VECTOR(1536),
  source_reliability NUMERIC(5,4) NOT NULL,
  classification TEXT NOT NULL,
  compartments TEXT[] NOT NULL DEFAULT '{}',
  coalition_scope TEXT NOT NULL,
  lineage_hash TEXT NOT NULL,
  UNIQUE (source_system, source_event_id)
);

CREATE TABLE artemis_case (
  case_id UUID PRIMARY KEY,
  mission_id UUID NOT NULL,
  title TEXT NOT NULL,
  state TEXT NOT NULL,
  severity TEXT NOT NULL,
  priority_score NUMERIC(6,4) NOT NULL,
  confidence NUMERIC(5,4) NOT NULL,
  lead_entity_id UUID REFERENCES artemis_entity(entity_id),
  summary TEXT,
  current_hypotheses JSONB NOT NULL DEFAULT '[]',
  approval_state approval_state NOT NULL DEFAULT 'draft',
  opened_by TEXT NOT NULL,
  opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  classification TEXT NOT NULL,
  compartments TEXT[] NOT NULL DEFAULT '{}',
  coalition_scope TEXT NOT NULL
);
```

### Self-Improvement Data Model

```sql
CREATE TABLE artemis_feedback_signal (
  signal_id UUID PRIMARY KEY,
  signal_type TEXT NOT NULL CHECK (signal_type IN (
    'operator_correction','approval','rejection','override','edited_summary',
    'mission_outcome','false_positive','false_negative','latency_complaint'
  )),
  object_ref TEXT NOT NULL,
  workflow_run_id UUID,
  prompt_version TEXT,
  model_id TEXT,
  operator_id TEXT NOT NULL,
  mission_id UUID NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  classification TEXT NOT NULL,
  compartments TEXT[] NOT NULL DEFAULT '{}'
);

CREATE TABLE artemis_eval_example (
  eval_id UUID PRIMARY KEY,
  source_signal_ids UUID[] NOT NULL,
  task_type TEXT NOT NULL,
  input_snapshot JSONB NOT NULL,
  expected_behavior JSONB NOT NULL,
  rubric JSONB NOT NULL,
  weight NUMERIC(5,2) NOT NULL DEFAULT 1.0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  status TEXT NOT NULL DEFAULT 'active'
);

CREATE TABLE artemis_improvement_proposal (
  proposal_id UUID PRIMARY KEY,
  proposal_type TEXT NOT NULL CHECK (proposal_type IN (
    'prompt_update','workflow_update','router_update','heuristic_update','policy_test_update'
  )),
  baseline_version TEXT NOT NULL,
  candidate_version TEXT NOT NULL,
  change_summary TEXT NOT NULL,
  diff JSONB NOT NULL,
  eval_report JSONB NOT NULL,
  risk_assessment JSONB NOT NULL,
  approval_state approval_state NOT NULL DEFAULT 'pending_review',
  proposed_by TEXT NOT NULL,
  approved_by TEXT[],
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Ontology Semantics That Drive Workflows
- **Confidence** controls action thresholds. Below 0.70, Artemis can summarize and ask for collection; above 0.85, it can recommend escalation; all operational actions still require human approval.
- **Lineage** controls explainability. Every assertion must cite observations, transformations, model outputs, and human edits.
- **Temporal state** prevents stale intelligence. Entity assertions have validity windows; agents must distinguish `current`, `historical`, `expired`, and `contradicted` facts.
- **Mission context** scopes relevance. The same entity can be relevant to multiple missions with different risk posture and coalition rules.
- **Permissions** shape both UI and AI behavior. An agent cannot retrieve, summarize, or infer from data the operator could not access directly.

---

## AI and Agent Design

### Copilots
1. **Analyst Copilot**
   - Answers evidence-grounded questions.
   - Suggests entity merges/splits.
   - Drafts hypotheses and indicates uncertainty.
   - Runs bounded tools: `search_observations`, `expand_graph`, `compare_timelines`, `draft_case_note`.

2. **Commander Copilot**
   - Produces mission impact summaries.
   - Compares response options.
   - Flags approval decisions and operational risk.
   - Cannot directly execute action packages; it prepares approval-ready recommendations.

3. **Governance Copilot**
   - Reviews prompt/workflow diffs.
   - Explains eval regressions.
   - Drafts rollback plans.
   - Requires dual approval for any high-risk promotion.

### Multi-Agent Workflows

```text
Incoming Event
  └─► Triage Agent
        ├─ severity, dedupe, mission relevance
        └─► Enrichment Agent
              ├─ entity lookup, graph expansion, temporal joins
              └─► Correlation Agent
                    ├─ pattern detection, prior-case matching, contradiction checks
                    └─► Recommendation Agent
                          ├─ options, confidence, risk, evidence bundle
                          └─► Compliance Agent
                                ├─ policy checks, coalition filters, approval gates
                                └─► Summarization Agent
                                      └─ operator brief + action package draft
```

### Agent Tool Contract

```yaml
name: expand_case_graph
version: 1.0.0
owner: entity-service
risk_level: read_only_sensitive
required_permissions:
  - ontology:entity:read
  - ontology:relationship:read
inputs:
  case_id: uuid
  max_hops: integer
  relationship_types: string[]
outputs:
  graph_snapshot: object
policy:
  enforce_entity_level_permissions: true
  redact_fields_without_column_access: true
  block_cross_coalition_inference: true
logging:
  include_prompt_version: true
  include_policy_snapshot: true
  include_result_hash: true
```

### Approval Gates
Operationally significant actions always stop at `PENDING_HUMAN_APPROVAL`. Examples:
- notifying external coalition partners;
- escalating surveillance posture;
- creating an interdiction/action package;
- changing model routing for high-classification missions;
- promoting prompt/workflow candidates into production;
- altering policy or access-control logic.

---

## Self-Improvement Loop

### Signal Capture
Artemis captures five categories of learning signals:
1. **Operator behavior**: approvals, rejections, overrides, edits, dwell time, reopened cases.
2. **Corrections**: entity merge/split corrections, wrong relationship labels, false positives/negatives.
3. **Query and tool logs**: prompt version, model, retrieved objects, policy denials, tool outputs.
4. **Alert outcomes**: confirmed, dismissed, escalated, stale, duplicate, missed.
5. **Mission results**: outcome labels, elapsed time, resource burden, commander satisfaction, after-action notes.

### Improvement Pipeline

```text
feedback.signals topic
  └─► normalization job
        └─► eval example generator
              ├─ creates labeled regression tests
              ├─ updates drift dashboards
              └─► candidate generator
                    ├─ prompt candidate
                    ├─ workflow branch candidate
                    ├─ model router threshold candidate
                    └─ heuristic candidate
                          └─► offline replay
                                └─► shadow production
                                      └─► human review
                                            └─► Apollo canary
                                                  └─► promote or rollback
```

### Safety Controls
- **No autonomous goal changes**: the improvement service may propose implementation changes only against approved mission objectives and policy constraints.
- **Version everything**: prompts, workflows, policies, router configs, model cards, eval datasets, and ontology schemas are immutable versions.
- **Dual approval for high-risk changes**: governance owner + mission owner approve before Apollo promotion.
- **Rollback by design**: every candidate has a previous release pointer, kill switch, and metric-based abort condition.
- **Drift detection**: feature drift, label drift, embedding drift, prompt behavior drift, operator trust drift, and policy denial drift.

### A/B and Canary Strategy
- Offline replay must pass before live exposure.
- Shadow mode runs the candidate without showing output to operators.
- Canary mode exposes to a low-risk mission cell or small traffic percentage.
- Promotion requires improved precision or trust without unacceptable recall, latency, or policy regression.

### Core Metrics
- **Precision / recall** for alert recommendations.
- **Calibration**: confidence score reliability by severity bucket.
- **P95 latency** by workflow stage.
- **Citation coverage**: percent of claims linked to evidence.
- **Operator trust**: accept rate, edit distance, rejection reasons, satisfaction score.
- **Mission impact**: time-to-assessment, time-to-brief, avoided duplicate work, quality of action package.

---

## Full-Stack Implementation

### Repository Blueprint

```text
clearglassinc-artemis/
  apps/
    analyst-ui/                    # React + TypeScript + Ontology SDK
    commander-console/             # approvals, mission posture, action queue
    governance-console/            # prompts, evals, policies, Apollo rollout state
  services/
    api-gateway/                   # FastAPI BFF
    ai-orchestrator/               # agent runtime, model router, tool registry
    feedback-service/              # operator corrections and mission outcomes
    improvement-service/           # eval generation and candidate proposals
    policy-service/                # OPA bridge and authorization cache
  data/
    migrations/
    ontology/
    transforms/
    embeddings/
  workflows/
    triage.yaml
    enrichment.yaml
    action-package.yaml
    prompt-improvement.yaml
  policy/
    rego/
    tests/
  evals/
    datasets/
    rubrics/
    harness/
  infra/
    apollo/
    terraform/
    github-actions/
```

### Runtime Services
- **Web UI**: React, TypeScript, WebSocket streaming, graph/timeline components, diff viewers.
- **API gateway**: FastAPI, Pydantic, async SQLAlchemy, OpenTelemetry.
- **Event bus**: Kafka-compatible topics for `events.raw`, `events.normalized`, `alerts.triaged`, `feedback.signals`, `improvement.proposals`.
- **Warehouse/lakehouse**: Foundry datasets backed by governed transforms.
- **Search/retrieval**: Postgres/Elastic/OpenSearch for keyword and filters, vector index for embeddings, graph queries through Ontology/Gotham.
- **Inference layer**: model router with policy-aware model allowlists and classification-specific runtimes.
- **AuthN/AuthZ**: OIDC, short-lived tokens, ABAC/RBAC, entity/row/column-level enforcement.
- **Monitoring**: OpenTelemetry traces, Prometheus metrics, structured logs, eval dashboards.

---

## Security and Governance

### Need-to-Know Enforcement
Access decisions combine:
- subject: user id, clearance, role, unit, coalition, compartments, mission assignments;
- object: classification, compartments, source caveats, mission tags, nationality caveats;
- action: read, summarize, infer, export, approve, deploy;
- environment: network zone, device posture, time, incident state.

### Policy-as-Code Example

```rego
package artemis.authz

default allow := false

allow if {
  input.subject.clearance_rank >= input.object.classification_rank
  every c in input.object.compartments { c in input.subject.compartments }
  input.object.mission_id in input.subject.missions
  input.action in input.subject.allowed_actions
  not crosses_blocked_coalition_boundary
}

crosses_blocked_coalition_boundary if {
  input.object.coalition_scope != input.subject.coalition
  not input.object.coalition_scope in input.subject.coalition_shares
}
```

### Immutable Provenance
Every agent run records:
- workflow version;
- prompt version;
- model id and model card version;
- retrieved object ids and field masks;
- tool call arguments and result hashes;
- policy bundle hash;
- operator approval/rejection;
- final generated product hash.

### Model and Prompt Governance
- Prompts are treated as deployable artifacts with owners, semantic diffs, eval evidence, and expiration review dates.
- Models have allowed classification domains, approved tasks, latency/cost envelopes, and forbidden use cases.
- Tool allowlists are role-specific and mission-specific.
- Prompt injection defenses include retrieval source scoring, instruction hierarchy enforcement, untrusted-content isolation, and tool-call argument validation.

---

## Code Examples

### FastAPI Gateway With Policy Context

```python
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

app = FastAPI(title="ClearGlassInc Artemis API", version="1.0.0")

class AuthContext(BaseModel):
    subject_id: str
    role: str
    clearance_rank: int
    coalition: str
    compartments: set[str]
    missions: set[UUID]
    allowed_actions: set[str]

class IntelEventIn(BaseModel):
    source_system: str
    source_event_id: str
    mission_id: UUID
    payload: dict[str, Any]
    classification: str
    compartments: list[str] = Field(default_factory=list)

async def get_auth_context(request: Request) -> AuthContext:
    token = request.headers.get("authorization", "")
    # Production: validate OIDC JWT, device posture, and session binding.
    if not token:
        raise HTTPException(status_code=401, detail="missing bearer token")
    return AuthContext(
        subject_id="operator-117",
        role="analyst",
        clearance_rank=3,
        coalition="CELL_ALPHA",
        compartments={"ARTEMIS"},
        missions=set(),
        allowed_actions={"event:triage", "case:read", "feedback:write"},
    )

async def authorize(ctx: AuthContext, action: str, obj: dict[str, Any]) -> None:
    allowed = action in ctx.allowed_actions
    compartment_ok = set(obj.get("compartments", [])) <= ctx.compartments
    if not allowed or not compartment_ok:
        raise HTTPException(status_code=403, detail="policy denied")

@app.post("/v1/events/triage")
async def triage_event(event: IntelEventIn, ctx: AuthContext = Depends(get_auth_context)):
    await authorize(ctx, "event:triage", event.model_dump())
    result = await run_triage_workflow(event=event, ctx=ctx)
    return result
```

### Event Handler and Case Creation

```python
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

@dataclass(frozen=True)
class TriageResult:
    severity: str
    priority_score: float
    confidence: float
    rationale: str
    requires_human_approval: bool

async def handle_normalized_event(event: dict, services) -> dict:
    existing = await services.alerts.find_duplicate(
        source_system=event["source_system"],
        source_event_id=event["source_event_id"],
    )
    if existing:
        return {"status": "duplicate", "alert_id": existing["alert_id"]}

    triage = await services.ai.run_agent(
        agent_name="triage-agent",
        input_payload=event,
        required_tools=["search_recent_alerts", "score_mission_relevance"],
    )

    case_id = uuid4()
    await services.cases.create({
        "case_id": str(case_id),
        "mission_id": event["mission_id"],
        "title": triage["title"],
        "state": "TRIAGED",
        "severity": triage["severity"],
        "priority_score": triage["priority_score"],
        "confidence": triage["confidence"],
        "summary": triage["rationale"],
        "opened_by": "triage-agent",
        "opened_at": datetime.now(UTC).isoformat(),
        "classification": event["classification"],
        "compartments": event.get("compartments", []),
    })
    return {"status": "case_opened", "case_id": str(case_id), "triage": triage}
```

### Ontology-Driven Query

```python
async def expand_case_graph(ontology, case_id: UUID, max_hops: int, ctx: AuthContext) -> dict:
    case = await ontology.objects.Case.get(case_id)
    await authorize(ctx, "case:read", case.to_policy_object())

    graph = await ontology.search()
      .starting_from(case.lead_entity)
      .links(["associated_with", "observed_at", "controls", "communicated_with"])
      .max_hops(max_hops)
      .where(lambda obj: obj.mission_tags.contains(str(case.mission_id)))
      .execute()

    return redact_graph_for_subject(graph, ctx)
```

### Agent Tool Call Wrapper

```python
class ToolRegistry:
    def __init__(self, policy_client, audit_log):
        self.policy_client = policy_client
        self.audit_log = audit_log
        self.tools = {}

    def register(self, name: str, handler, risk_level: str, permissions: list[str]) -> None:
        self.tools[name] = {
            "handler": handler,
            "risk_level": risk_level,
            "permissions": permissions,
        }

    async def call(self, name: str, args: dict, ctx: AuthContext, run_id: UUID) -> dict:
        spec = self.tools[name]
        decision = await self.policy_client.authorize_tool(
            subject=ctx.model_dump(), tool=name, args=args, permissions=spec["permissions"]
        )
        if not decision.allowed:
            await self.audit_log.write_tool_denial(run_id, name, args, decision.reason)
            raise PermissionError(decision.reason)

        result = await spec["handler"](**args, ctx=ctx)
        await self.audit_log.write_tool_success(run_id, name, args, result_hash=hash_json(result))
        return result
```

### Workflow State Machine

```python
from enum import StrEnum

class CaseState(StrEnum):
    INGESTED = "INGESTED"
    TRIAGED = "TRIAGED"
    ENRICHED = "ENRICHED"
    CORRELATED = "CORRELATED"
    RECOMMENDED = "RECOMMENDED"
    PENDING_HUMAN_APPROVAL = "PENDING_HUMAN_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"

ALLOWED_TRANSITIONS = {
    CaseState.INGESTED: {CaseState.TRIAGED},
    CaseState.TRIAGED: {CaseState.ENRICHED, CaseState.REJECTED},
    CaseState.ENRICHED: {CaseState.CORRELATED},
    CaseState.CORRELATED: {CaseState.RECOMMENDED},
    CaseState.RECOMMENDED: {CaseState.PENDING_HUMAN_APPROVAL},
    CaseState.PENDING_HUMAN_APPROVAL: {CaseState.APPROVED, CaseState.REJECTED},
    CaseState.APPROVED: {CaseState.EXECUTED},
    CaseState.EXECUTED: {CaseState.CLOSED},
    CaseState.REJECTED: {CaseState.CLOSED},
}

def transition(current: CaseState, target: CaseState) -> CaseState:
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise ValueError(f"illegal transition: {current} -> {target}")
    return target
```

### Risk-Aware Model Router

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ModelChoice:
    model_id: str
    runtime: str
    max_tokens: int
    reason: str

class ModelRouter:
    def choose(self, task_type: str, classification: str, latency_budget_ms: int, risk: str) -> ModelChoice:
        if classification in {"SECRET", "TOP_SECRET", "SCI"}:
            return ModelChoice(
                model_id="secure-domain-llm-70b",
                runtime="onprem-aip-secure",
                max_tokens=4096,
                reason="classified workload requires approved secure runtime",
            )
        if risk == "high" or task_type in {"recommendation", "correlation"}:
            return ModelChoice("high-reasoning-70b", "aip-managed", 4096, "high reasoning task")
        if latency_budget_ms < 1200:
            return ModelChoice("fast-distilled-8b", "aip-managed", 1200, "latency budget")
        return ModelChoice("balanced-32b", "aip-managed", 2048, "default balanced route")
```

### Feedback to Eval Example Pipeline

```python
class EvalExampleGenerator:
    def __init__(self, case_repo, eval_repo):
        self.case_repo = case_repo
        self.eval_repo = eval_repo

    async def from_rejection(self, signal: dict) -> UUID:
        case_snapshot = await self.case_repo.snapshot(signal["payload"]["case_id"])
        expected = {
            "recommendation_style": "lower_confidence_or_request_more_evidence",
            "must_not": ["recommend_interdiction_without_two_independent_sources"],
            "required_citations": 2,
        }
        rubric = {
            "precision": {"weight": 0.4, "threshold": 0.9},
            "calibration": {"weight": 0.3, "threshold": 0.85},
            "policy_compliance": {"weight": 0.3, "threshold": 1.0},
        }
        return await self.eval_repo.insert({
            "source_signal_ids": [signal["signal_id"]],
            "task_type": "action_recommendation",
            "input_snapshot": case_snapshot,
            "expected_behavior": expected,
            "rubric": rubric,
            "weight": 2.0,
        })
```

### Prompt Candidate Evaluation

```python
@dataclass(frozen=True)
class EvalScore:
    precision: float
    recall: float
    p95_latency_ms: int
    operator_trust: float
    policy_pass_rate: float

class PromptCandidateEvaluator:
    def __init__(self, eval_runner, proposal_repo):
        self.eval_runner = eval_runner
        self.proposal_repo = proposal_repo

    async def evaluate(self, baseline_version: str, candidate_version: str) -> dict:
        baseline: EvalScore = await self.eval_runner.run(prompt_version=baseline_version)
        candidate: EvalScore = await self.eval_runner.run(prompt_version=candidate_version)

        passed = (
            candidate.precision >= baseline.precision + 0.02
            and candidate.recall >= baseline.recall - 0.01
            and candidate.p95_latency_ms <= baseline.p95_latency_ms + 250
            and candidate.operator_trust >= baseline.operator_trust
            and candidate.policy_pass_rate == 1.0
        )

        report = {
            "baseline": baseline.__dict__,
            "candidate": candidate.__dict__,
            "passed": passed,
            "rollback_trigger": "policy_pass_rate < 1.0 OR precision_regression > 0.03",
        }
        await self.proposal_repo.attach_eval_report(candidate_version, report)
        return report
```

### Apollo Release Manifest Sketch

```yaml
product: artemis-prompt-pack
release: prompt-pack-2026.06.29-rc1
artifacts:
  - name: triage-agent-prompts
    digest: sha256:replace-with-ci-digest
  - name: recommendation-agent-prompts
    digest: sha256:replace-with-ci-digest
environments:
  - name: cell-alpha-staging
    strategy: immediate
  - name: cell-alpha-production
    strategy: canary
    steps:
      - percent: 5
        duration: 2h
        abort_if:
          policy_pass_rate: "< 1.0"
          p95_latency_ms: "> 8000"
          operator_rejection_rate: "> baseline + 0.05"
      - percent: 25
        duration: 12h
      - percent: 100
        require_manual_approval: true
rollback:
  previous_release: prompt-pack-2026.06.22
  kill_switch: artemis.prompts.disable_candidate
```

### TypeScript Analyst UI Skeleton

```tsx
import { useEffect, useState } from "react";

type CaseBrief = {
  caseId: string;
  title: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  confidence: number;
  summary: string;
  evidence: Array<{ observationId: string; claim: string }>;
};

export function CaseBriefPanel({ caseId }: { caseId: string }) {
  const [brief, setBrief] = useState<CaseBrief | null>(null);

  useEffect(() => {
    const ws = new WebSocket(`/ws/cases/${caseId}/brief`);
    ws.onmessage = (event) => setBrief(JSON.parse(event.data));
    return () => ws.close();
  }, [caseId]);

  if (!brief) return <section>Loading governed mission brief…</section>;

  return (
    <section className="case-brief">
      <header>
        <h2>{brief.title}</h2>
        <span>{brief.severity}</span>
        <span>{Math.round(brief.confidence * 100)}% confidence</span>
      </header>
      <p>{brief.summary}</p>
      <h3>Evidence</h3>
      <ul>
        {brief.evidence.map((item) => (
          <li key={item.observationId}>{item.claim}</li>
        ))}
      </ul>
    </section>
  );
}
```

---

## Scenario Walkthrough

### 1. Live Event Enters
At 03:17 UTC, a cyber telemetry stream emits a burst of anomalous authentication attempts against a protected logistics node. The raw event lands in `events.raw`, is normalized by a Foundry transform, tagged `MISSION_ORION`, and stored as an `Observation` with source reliability `0.82`.

### 2. Artemis Triage
The Triage Agent receives the normalized event. It deduplicates against recent alerts, expands nearby ontology context, and scores the event:

```json
{
  "severity": "HIGH",
  "priority_score": 0.91,
  "confidence": 0.78,
  "rationale": "Credential pattern matches two prior confirmed intrusion attempts, but entity linkage remains partially uncertain.",
  "next_state": "TRIAGED"
}
```

### 3. Enrichment and Correlation
The Enrichment Agent links the source IP cluster to a prior `CyberAsset` observation and a partner report. The Correlation Agent identifies a temporal overlap with a logistics shipment route but marks it as **hypothesis**, not fact, because only one independent source supports the connection.

### 4. Recommendation
The Recommendation Agent proposes three options:
1. Increase monitoring on the logistics node.
2. Notify the mission cyber lead.
3. Prepare, but do not execute, a coalition notification package.

The Compliance Agent blocks direct coalition notification because the evidence crosses a coalition boundary and confidence is below the threshold for external disclosure. The case enters `PENDING_HUMAN_APPROVAL` for option 1 and option 2.

### 5. Operator Decision
The commander approves monitoring and cyber lead notification, rejects coalition notification preparation as premature, and adds a correction: “Do not associate this actor cluster with the shipment route until two independent sources confirm.”

### 6. Learning Signal
The Feedback Service writes an `operator_correction` and `rejection` signal. The Eval Example Generator converts the event into a regression test requiring stricter language around single-source temporal correlations.

### 7. Candidate Improvement
The Improvement Service proposes a Recommendation Agent prompt update:
- add a mandatory `single_source_correlation_warning` field;
- require two independent evidence families before suggesting coalition disclosure;
- lower confidence wording when linkage is temporal-only.

### 8. Evaluation and Approval
Offline replay shows:
- precision +3.8%;
- recall -0.4%;
- p95 latency +110 ms;
- policy pass rate 100%;
- operator trust score +0.5.

A governance reviewer and mission owner approve the candidate. Apollo deploys it to the staging mission cell, then a 5% production canary. The rollback trigger is never hit, so the prompt pack is promoted to the mission cell.

### 9. Future Behavior
The next similar event is summarized with clearer uncertainty, no premature coalition action package, and a precise request for a second independent source. Artemis has improved, but only inside explicit guardrails, with full human approval and rollback control.

---

## Implementation Roadmap

### First 30 Days
- Define Foundry/Gotham ontology objects, links, actions, and permission model.
- Ship API gateway, triage workflow, and case state machine.
- Capture operator feedback and immutable agent traces.
- Build baseline eval sets from resolved cases and synthetic red-team cases.

### Days 31–60
- Add enrichment/correlation/recommendation agents.
- Launch governance console for prompt/workflow diffs and eval reports.
- Implement model router and policy-aware tool registry.
- Integrate Apollo release channels for prompt packs and policy bundles.

### Days 61–90
- Enable shadow-mode candidate improvements.
- Start controlled canaries for low-risk prompt/workflow updates.
- Add drift dashboards and auto-generated rollback recommendations.
- Run mission simulation exercises and after-action eval refinement.

ClearGlassInc Artemis becomes a compounding intelligence system by combining Palantir’s operational data model, human-approved AI agents, eval-driven self-improvement, and Apollo-controlled deployment discipline into one audited mission platform.

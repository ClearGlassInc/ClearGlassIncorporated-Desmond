# ClearGlassInc Artemis — Self-Evolving AI Intelligence Platform Blueprint

## System Architecture

ClearGlassInc Artemis is a secure, coalition-aware, multi-domain intelligence platform built as a layered system across Palantir Gotham, Foundry, AIP, and Apollo.

**Palantir terminology used in this blueprint:**

- **Gotham**: operational intelligence layer for investigations, entity tracking, link analysis, mission workflows, and operational case management.
- **Foundry**: data integration and operational data layer for pipelines, ontology objects, transforms, applications, and governed data products.
- **AIP**: AI orchestration layer for copilots, agents, model routing, tool execution, prompt governance, evaluations, and workflow automation.
- **Apollo**: deployment and runtime-control layer for secure releases, canaries, rollback, configuration, policy bundles, and environment-specific promotion.

### End-to-end reference topology

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                              Web / Mission UI                                │
│ Analyst Console · Commander View · Case Workbench · Eval Dashboard · Admin   │
└───────────────┬──────────────────────────────────────────────────────────────┘
                │ OIDC/SAML + signed requests + policy context
┌───────────────▼──────────────────────────────────────────────────────────────┐
│                              API Gateway                                     │
│ REST/gRPC · GraphQL façade · rate limits · request signing · audit envelope  │
└───────┬──────────────┬──────────────────────┬──────────────────────────────┘
        │              │                      │
┌───────▼──────┐ ┌─────▼──────────┐ ┌─────────▼──────────┐
│ Mission API  │ │ Ontology API    │ │ AI Orchestration    │
│ cases/tasks  │ │ object/action   │ │ AIP agents/tools    │
└───────┬──────┘ └─────┬──────────┘ └─────────┬──────────┘
        │              │                      │
┌───────▼──────────────▼──────────────────────▼──────────────────────────────┐
│                             Foundry Layer                                   │
│ Pipelines · transforms · Ontology · Functions · row/entity policy · lineage │
└───────┬──────────────────────┬──────────────────────────┬─────────────────┘
        │                      │                          │
┌───────▼────────┐  ┌──────────▼────────┐  ┌──────────────▼──────────────────┐
│ Stream ingest  │  │ Lakehouse/warehouse│  │ Retrieval/Search                 │
│ Kafka/Pulsar   │  │ governed tables    │  │ embeddings · graph · full text   │
└───────┬────────┘  └──────────┬────────┘  └──────────────┬──────────────────┘
        │                      │                          │
┌───────▼──────────────────────▼──────────────────────────▼──────────────────┐
│                            Gotham Layer                                     │
│ Investigations · entity tracking · link analysis · mission objects · alerts │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                         Cross-cutting control planes                         │
│ Policy-as-code · immutable audit · observability · evals · Apollo deployment │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Runtime planes

| Plane | Primary responsibility | Production components |
| --- | --- | --- |
| Frontend | Human mission workflow and review gates | React/Next.js mission console, command dashboard, alert queue, ontology browser, prompt/eval admin |
| Backend | Mission APIs, workflow state, action approval | FastAPI services, gRPC internal APIs, Postgres operational metadata, Redis cache |
| Data | Live and historical integration | Foundry datasets, streaming ingest, batch transforms, object lineage, versioned materialized views |
| Ontology | Shared semantic mission model | Person, Organization, Asset, Event, Alert, Case, Mission, ActionPackage objects and links |
| AI orchestration | Copilots, agents, model router, tools | AIP logic, tool registry, prompt registry, eval harness, human approval workflow |
| Policy | Need-to-know, coalition, compartment controls | OPA/Rego-style policy, Foundry/Gotham permissions, entity labels, attribute-based controls |
| Observability | Mission, model, system telemetry | OpenTelemetry traces, structured logs, eval dashboards, drift monitors, audit evidence |
| Deployment | Secure release and rollback | Apollo environments, canary promotion, policy-bundle rollout, model/prompt version gates |

## Data and Ontology

The ontology is the operational contract between humans, agents, pipelines, and policy. Every important fact is represented as an object, relationship, temporal assertion, or governed artifact with confidence and lineage.

### Core ontology objects

```yaml
Ontology:
  Person:
    keys: [person_id]
    properties:
      names: string[]
      identifiers: Identifier[]
      roles: string[]
      affiliations: org_id[]
      confidence: float
      classification: ClassificationLabel
      compartments: string[]
      valid_time: TimeRange
      source_lineage: LineageRef[]
  Organization:
    keys: [org_id]
    properties: [legal_name, aliases, jurisdictions, sectors, watchlist_status]
  Asset:
    keys: [asset_id]
    properties: [type, owner, network_ranges, geolocation, criticality, exposure_score]
  Event:
    keys: [event_id]
    properties: [event_type, observed_at, source, raw_ref, severity, confidence]
  Alert:
    keys: [alert_id]
    properties: [priority, rationale, status, triage_state, model_version, prompt_version]
  Case:
    keys: [case_id]
    properties: [mission_id, status, lead_operator, objectives, sla, outcome]
  Mission:
    keys: [mission_id]
    properties: [name, coalition_scope, objectives, rules_of_engagement, risk_level]
  ActionPackage:
    keys: [action_id]
    properties: [recommended_action, risk, approvals_required, approval_status, rollback_plan]
  FeedbackSignal:
    keys: [feedback_id]
    properties: [operator_id, object_ref, signal_type, correction, rating, outcome_ref]
  ImprovementProposal:
    keys: [proposal_id]
    properties: [target, diff, eval_result, risk, reviewer, status]
```

### Relationship model

```text
Person AFFILIATED_WITH Organization
Person OWNS Asset
Organization CONTROLS Asset
Event OBSERVED_ON Asset
Event INVOLVES Person|Organization|Asset
Alert GENERATED_FROM Event
Alert OPENED_CASE Case
Case SUPPORTS Mission
Case HAS_ACTION_PACKAGE ActionPackage
FeedbackSignal ANNOTATES Alert|Case|ActionPackage|PromptVersion
ImprovementProposal MODIFIES Prompt|Workflow|RouterPolicy|Heuristic
```

### Confidence, lineage, and time

Each assertion stores both **valid time** and **system time**.

```sql
CREATE TABLE ontology_assertion (
  assertion_id UUID PRIMARY KEY,
  subject_type TEXT NOT NULL,
  subject_id TEXT NOT NULL,
  predicate TEXT NOT NULL,
  object_type TEXT NOT NULL,
  object_id TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  valid_from TIMESTAMPTZ NOT NULL,
  valid_to TIMESTAMPTZ,
  system_from TIMESTAMPTZ NOT NULL DEFAULT now(),
  system_to TIMESTAMPTZ,
  source_dataset TEXT NOT NULL,
  source_record_id TEXT NOT NULL,
  transform_version TEXT NOT NULL,
  classification TEXT NOT NULL,
  compartments TEXT[] NOT NULL DEFAULT '{}'
);
```

This lets Artemis answer: **what did we know, when did we know it, why did we believe it, who could see it, and which model/workflow used it?**

### How the ontology drives AI behavior

Agents do not operate over raw tables by default. They operate over ontology-safe tools:

```text
Agent question → policy context → ontology query plan → permitted object graph → evidence pack → model reasoning → proposed action → approval gate
```

The agent receives compact, permission-filtered evidence packs containing object summaries, lineage pointers, uncertainty, policy labels, and approved tool affordances. This prevents prompt-only access control and keeps mission permissions enforceable outside the model.

## AI and Agent Design

### Copilots

| Copilot | User | Capabilities | Hard limits |
| --- | --- | --- | --- |
| Analyst Copilot | Investigators | entity summaries, link analysis, timeline construction, source comparison | cannot change case state without approval |
| Commander Copilot | Mission leads | decision briefings, risk tradeoffs, operational readiness summaries | cannot issue operational actions |
| Data Steward Copilot | Data owners | lineage inspection, schema drift triage, quality anomaly review | cannot broaden access policy |
| Governance Copilot | Review boards | prompt diffs, eval summaries, rollback impact | cannot self-approve changes |

### Multi-agent workflows

```text
Live event
  → TriageAgent assigns priority and uncertainty
  → EnrichmentAgent gathers related ontology entities
  → CorrelationAgent finds graph/time-pattern matches
  → RetrievalAgent assembles evidence and source snippets
  → SummarizerAgent writes an intelligence note
  → RecommendationAgent drafts action packages
  → PolicyAgent verifies authority, classification, and approval gates
  → Human operator approves/rejects/edits
  → LearningLoop converts outcome into evals and proposals
```

### Operational approval gates

Actions are categorized by risk.

```yaml
action_risk_classes:
  observe:
    examples: [summarize, search, enrich, draft]
    approval: none_if_policy_allows
  administrative:
    examples: [open_case, assign_task, request_data_refresh]
    approval: operator_confirm
  operationally_significant:
    examples: [send_external_notification, escalate_to_partner, change_watchlist]
    approval: two_person_review
  irreversible_or_external:
    examples: [public disclosure, blocking action, legal referral]
    approval: commander_plus_legal_policy
```

## Self-Improvement Loop

Artemis improves prompts, workflows, heuristics, model routing, and eval suites. It does **not** autonomously change objectives, authorities, coalition boundaries, or rules of engagement.

### Signal capture

```text
Operator correction      → corrected entity, relationship, severity, rationale
Operator rating          → answer usefulness, trust, completeness, citation quality
Query logs               → latency, retrieval set, prompt version, model version, tool path
Alert outcomes           → true positive, false positive, false negative, duplicate, stale
Mission results          → case closure, action effectiveness, time-to-resolution
System telemetry         → errors, model refusals, tool failures, drift, cost
```

### Improvement pipeline

```text
Signals → normalize → label → eval-case generation → candidate proposal → offline eval
        → risk scoring → human review → canary via Apollo → online eval → promote/rollback
```

### Versioned artifacts

```sql
CREATE TABLE ai_artifact_version (
  artifact_id UUID PRIMARY KEY,
  artifact_type TEXT NOT NULL CHECK (artifact_type IN ('prompt','workflow','router','heuristic','tool_schema','eval_set')),
  name TEXT NOT NULL,
  version TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  content JSONB NOT NULL,
  created_by TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  approval_status TEXT NOT NULL CHECK (approval_status IN ('draft','review','approved','rejected','rolled_back')),
  parent_artifact_id UUID,
  rollback_artifact_id UUID
);
```

### Safe upgrade controls

- **Offline eval gate**: candidate must beat baseline on precision, citation fidelity, policy compliance, and latency budget.
- **Regression gate**: candidate must not degrade critical mission scenarios.
- **Risk gate**: changes touching high-risk action packages require governance review.
- **Apollo canary**: expose candidate to a limited operator cohort or mission sandbox.
- **Rollback**: every prompt/workflow/router bundle has a known-good version and signed provenance.
- **Audit**: every proposal, reviewer note, eval result, and rollout decision is immutable.

## Full-Stack Implementation

### Application modules

```text
artemis/
  frontend/
    app/
      alerts/
      cases/
      commander/
      evals/
      governance/
  services/
    api_gateway/
    mission_api/
    ontology_api/
    ai_orchestrator/
    feedback_service/
    eval_service/
    policy_service/
  pipelines/
    ingest_live_events.py
    transform_to_ontology.py
    build_retrieval_index.py
    generate_eval_cases.py
  policies/
    access.rego
    action_gates.rego
    coalition.rego
  infra/
    apollo_release.yaml
    otel_collector.yaml
    dashboards/
```

### Web UI blueprint

- **Alert Queue**: prioritized list with confidence, source lineage, model rationale, SLA clock, and action buttons.
- **Case Workbench**: entity graph, temporal timeline, evidence panel, task board, agent scratchpad, and approval journal.
- **Commander View**: mission status, risk heatmap, active incidents, decision briefs, coalition visibility.
- **Eval Dashboard**: prompt/workflow version comparison, false-positive trends, latency histograms, policy violations.
- **Governance Console**: improvement proposals, diffs, reviewers, canary status, rollback controls.

### API surfaces

```http
POST /v1/events/ingest
GET  /v1/ontology/entities/{type}/{id}
POST /v1/ontology/query
POST /v1/ai/agent/run
POST /v1/actions/propose
POST /v1/actions/{id}/approve
POST /v1/feedback
GET  /v1/evals/artifacts/{artifact_id}/scorecard
POST /v1/governance/proposals/{id}/decision
```

## Security and Governance

### Need-to-know model

Access is decided with attributes from the user, object, mission, and coalition context.

```yaml
user_context:
  user_id: analyst-17
  clearance: SECRET
  compartments: [CYBER, FINCRIME]
  coalition: [US, CA, UK]
  mission_roles: [case_lead]
object_context:
  classification: SECRET
  compartments: [CYBER]
  coalition_release: [US, CA]
  mission_id: mission-cyber-042
request_context:
  purpose: active_investigation
  action: read_entity
```

### Governance rules

- Row/column/entity-level authorization is enforced before model context construction.
- Prompt and model governance is handled like code: versioned, reviewed, evaluated, signed, deployed, and rollback-ready.
- Coalition release markings are attached to ontology objects and propagated into generated products.
- Every model output that cites evidence stores source object IDs, artifact versions, and policy decision IDs.
- Zero-trust services use mTLS, workload identity, least privilege, signed configs, and short-lived tokens.
- Immutable audit logs capture human, model, and tool actions.

## Code Examples

### Python FastAPI mission endpoint

```python
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime, timezone

router = APIRouter(prefix="/v1/actions", tags=["actions"])

class UserContext(BaseModel):
    user_id: str
    clearance: str
    compartments: set[str]
    coalition: set[str]
    roles: set[str]

class ActionProposalIn(BaseModel):
    case_id: UUID
    action_type: str
    summary: str
    rationale: str
    evidence_object_ids: list[str] = Field(default_factory=list)
    risk_class: str

class ActionProposalOut(BaseModel):
    action_id: UUID
    approval_status: str
    approvals_required: int
    created_at: datetime

async def current_user() -> UserContext:
    return UserContext(
        user_id="analyst-17",
        clearance="SECRET",
        compartments={"CYBER"},
        coalition={"US", "CA"},
        roles={"case_lead"},
    )

async def policy_allows(user: UserContext, action: str, resource: dict) -> bool:
    # In production this calls OPA/Foundry policy and records a policy_decision_id.
    if resource["classification"] == "TOP_SECRET" and user.clearance != "TOP_SECRET":
        return False
    return resource["compartments"].issubset(user.compartments)

@router.post("/propose", response_model=ActionProposalOut)
async def propose_action(
    body: ActionProposalIn,
    user: Annotated[UserContext, Depends(current_user)],
) -> ActionProposalOut:
    resource = {"classification": "SECRET", "compartments": {"CYBER"}}
    if not await policy_allows(user, "propose_action", resource):
        raise HTTPException(status_code=403, detail="policy_denied")

    approvals_required = 0 if body.risk_class == "observe" else 1
    if body.risk_class in {"operationally_significant", "irreversible_or_external"}:
        approvals_required = 2

    action_id = uuid4()
    # Persist action package, evidence links, policy decision, and audit event here.
    return ActionProposalOut(
        action_id=action_id,
        approval_status="pending" if approvals_required else "approved",
        approvals_required=approvals_required,
        created_at=datetime.now(timezone.utc),
    )
```

### Python streaming triage handler

```python
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass(frozen=True)
class LiveEvent:
    event_id: str
    source: str
    event_type: str
    observed_at: datetime
    payload: dict
    classification: str
    compartments: tuple[str, ...]

class TriageEngine:
    def __init__(self, ontology, model_router, audit):
        self.ontology = ontology
        self.model_router = model_router
        self.audit = audit

    async def handle(self, raw_message: bytes) -> None:
        event = LiveEvent(**json.loads(raw_message))
        related_graph = await self.ontology.expand_event_context(
            event_id=event.event_id,
            max_hops=2,
            compartments=set(event.compartments),
        )
        score = await self.model_router.score_alert_priority(
            event=event,
            graph=related_graph,
            prompt_version="triage-v34",
            policy_context={"classification": event.classification},
        )
        await self.ontology.upsert_alert(
            event_id=event.event_id,
            priority=score.priority,
            confidence=score.confidence,
            rationale=score.rationale,
            model_version=score.model_version,
            prompt_version="triage-v34",
        )
        await self.audit.write(
            actor="aip.triage_agent",
            action="alert_scored",
            object_id=event.event_id,
            metadata={"priority": score.priority, "confidence": score.confidence},
        )
```

### Ontology-driven query

```sql
WITH permitted_assertions AS (
  SELECT *
  FROM ontology_assertion
  WHERE classification <= :user_clearance_rank
    AND compartments <@ :user_compartments
    AND (:coalition = ANY(coalition_release) OR coalition_release IS NULL)
), event_neighborhood AS (
  SELECT a.*
  FROM permitted_assertions a
  WHERE a.subject_id = :event_id OR a.object_id = :event_id
)
SELECT subject_type, subject_id, predicate, object_type, object_id,
       confidence, valid_from, valid_to, source_dataset, transform_version
FROM event_neighborhood
ORDER BY confidence DESC, valid_from DESC
LIMIT 200;
```

### Python model router

```python
from enum import Enum
from pydantic import BaseModel

class TaskKind(str, Enum):
    TRIAGE = "triage"
    SUMMARY = "summary"
    RECOMMENDATION = "recommendation"
    GOVERNANCE = "governance"

class RoutingDecision(BaseModel):
    provider: str
    model: str
    max_latency_ms: int
    prompt_version: str
    rationale: str

class ModelRouter:
    def route(self, task: TaskKind, risk: str, data_classification: str) -> RoutingDecision:
        if data_classification in {"SECRET", "TOP_SECRET"}:
            return RoutingDecision(
                provider="approved_secure_aip_runtime",
                model="mission-reasoner-secure",
                max_latency_ms=2500,
                prompt_version=f"{task.value}-secure-v1",
                rationale="classified data requires secure runtime",
            )
        if task == TaskKind.SUMMARY and risk == "low":
            return RoutingDecision(
                provider="aip_standard",
                model="fast-summarizer",
                max_latency_ms=800,
                prompt_version="summary-fast-v12",
                rationale="low-risk summary optimized for latency",
            )
        return RoutingDecision(
            provider="aip_standard",
            model="balanced-reasoner",
            max_latency_ms=1800,
            prompt_version=f"{task.value}-balanced-v7",
            rationale="default balanced route",
        )
```

### Workflow state machine

```python
from transitions import Machine

class AlertWorkflow:
    states = [
        "new", "triaged", "enriched", "case_opened",
        "action_drafted", "awaiting_approval", "approved", "rejected", "closed"
    ]

    transitions = [
        {"trigger": "triage", "source": "new", "dest": "triaged"},
        {"trigger": "enrich", "source": "triaged", "dest": "enriched"},
        {"trigger": "open_case", "source": "enriched", "dest": "case_opened"},
        {"trigger": "draft_action", "source": "case_opened", "dest": "action_drafted"},
        {"trigger": "require_approval", "source": "action_drafted", "dest": "awaiting_approval"},
        {"trigger": "approve", "source": "awaiting_approval", "dest": "approved"},
        {"trigger": "reject", "source": "awaiting_approval", "dest": "rejected"},
        {"trigger": "close", "source": ["approved", "rejected"], "dest": "closed"},
    ]

    def __init__(self, alert_id: str):
        self.alert_id = alert_id
        self.machine = Machine(model=self, states=self.states, transitions=self.transitions, initial="new")
```

### Policy-as-code example

```rego
package artemis.access

default allow := false

allow if {
  input.action == "read_entity"
  clearance_rank[input.user.clearance] >= clearance_rank[input.object.classification]
  every c in input.object.compartments { c in input.user.compartments }
  input.request.purpose in {"active_investigation", "mission_command", "governance_review"}
  coalition_allowed
}

coalition_allowed if {
  count(input.object.coalition_release) == 0
}

coalition_allowed if {
  some c
  c := input.user.coalition[_]
  c == input.object.coalition_release[_]
}

clearance_rank := {
  "UNCLASSIFIED": 0,
  "CONFIDENTIAL": 1,
  "SECRET": 2,
  "TOP_SECRET": 3
}
```

### Eval pipeline

```python
from pydantic import BaseModel

class EvalCase(BaseModel):
    case_id: str
    input_event_id: str
    expected_priority: str
    expected_entities: set[str]
    forbidden_claims: set[str]
    policy_context: dict

class EvalResult(BaseModel):
    artifact_version: str
    precision: float
    recall: float
    citation_fidelity: float
    policy_pass_rate: float
    p95_latency_ms: int
    passed: bool

async def run_eval_suite(artifact_version: str, cases: list[EvalCase], runner) -> EvalResult:
    tp = fp = fn = citation_ok = policy_ok = 0
    latencies: list[int] = []
    for case in cases:
        output = await runner.run(case, artifact_version=artifact_version)
        tp += len(output.entities & case.expected_entities)
        fp += len(output.entities - case.expected_entities)
        fn += len(case.expected_entities - output.entities)
        citation_ok += int(output.citations_are_lineage_backed)
        policy_ok += int(output.policy_violations == 0)
        latencies.append(output.latency_ms)

    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    p95 = sorted(latencies)[int(len(latencies) * 0.95) - 1]
    passed = precision >= 0.92 and recall >= 0.88 and policy_ok == len(cases) and p95 <= 2500
    return EvalResult(
        artifact_version=artifact_version,
        precision=precision,
        recall=recall,
        citation_fidelity=citation_ok / len(cases),
        policy_pass_rate=policy_ok / len(cases),
        p95_latency_ms=p95,
        passed=passed,
    )
```

### TypeScript frontend action review component

```tsx
type ActionPackage = {
  actionId: string;
  summary: string;
  riskClass: "observe" | "administrative" | "operationally_significant" | "irreversible_or_external";
  rationale: string;
  evidence: { objectId: string; title: string; confidence: number }[];
  approvalStatus: "pending" | "approved" | "rejected";
};

export function ActionReviewCard({ action }: { action: ActionPackage }) {
  const canApprove = action.approvalStatus === "pending";

  async function decide(decision: "approve" | "reject") {
    await fetch(`/v1/actions/${action.actionId}/${decision}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason: "operator_decision_from_case_workbench" }),
    });
  }

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-950 p-5 text-slate-100">
      <div className="flex items-center justify-between gap-4">
        <h3 className="text-lg font-semibold">Recommended Action</h3>
        <span className="rounded-full bg-cyan-500/10 px-3 py-1 text-xs text-cyan-200">
          {action.riskClass}
        </span>
      </div>
      <p className="mt-3 text-sm text-slate-300">{action.summary}</p>
      <p className="mt-3 text-xs text-slate-400">{action.rationale}</p>
      <ul className="mt-4 space-y-2">
        {action.evidence.map((item) => (
          <li key={item.objectId} className="text-xs text-slate-400">
            {item.title} · confidence {Math.round(item.confidence * 100)}%
          </li>
        ))}
      </ul>
      {canApprove && (
        <div className="mt-5 flex gap-3">
          <button onClick={() => decide("approve")} className="rounded-xl bg-emerald-400 px-4 py-2 text-slate-950">
            Approve
          </button>
          <button onClick={() => decide("reject")} className="rounded-xl border border-slate-700 px-4 py-2">
            Reject
          </button>
        </div>
      )}
    </section>
  );
}
```

### Apollo release bundle sketch

```yaml
apiVersion: apollo.palantir.com/v1
kind: ReleaseBundle
metadata:
  name: artemis-ai-control-plane
spec:
  artifacts:
    - name: ai-orchestrator
      image: registry.clearglass.local/artemis/ai-orchestrator:2.8.14
    - name: prompt-bundle
      uri: foundry://artifacts/prompts/artemis/triage-v35
    - name: policy-bundle
      uri: foundry://artifacts/policies/access-2026-07-05
  rollout:
    strategy: canary
    initialPercent: 5
    promoteAfter: 2h
    metrics:
      - name: policy_violation_rate
        max: 0
      - name: triage_precision_online
        min: 0.92
      - name: p95_agent_latency_ms
        max: 2500
  rollback:
    automatic: true
    toLastKnownGood: true
```

## Scenario Walkthrough

1. **Live event enters**: A partner sensor sends a high-volume authentication anomaly into the streaming ingest bus. The ingest transform normalizes it into an `Event` object with SECRET/CYBER markings, source lineage, and observed time.
2. **Platform triages**: The TriageAgent requests a permitted ontology neighborhood. It sees the affected asset is mission-critical, linked to an active case, and has recent related anomalies. It creates a high-priority `Alert` with confidence 0.87.
3. **Agents correlate**: EnrichmentAgent attaches related organizations, network assets, and prior events. CorrelationAgent identifies a temporal pattern matching a known intrusion path, but marks one relationship as low-confidence because lineage comes from a single source.
4. **Recommendation drafted**: RecommendationAgent prepares an `ActionPackage`: open a case, notify the mission lead, request partner enrichment, and stage a containment checklist. PolicyAgent classifies partner notification as operationally significant, requiring two approvals.
5. **Operator reviews**: The analyst accepts the case opening, edits the summary to remove an overconfident phrase, and rejects immediate partner escalation pending one more source.
6. **System learns**: FeedbackService captures the edit, rejection, reason, source gaps, and eventual case outcome. EvalService converts the incident into regression cases for overconfidence, evidence sufficiency, and escalation thresholds.
7. **Improvement proposed**: AIP proposes a prompt change that forces RecommendationAgent to distinguish single-source inference from multi-source confirmation. It also proposes a routing rule: high-impact coalition escalation must use the higher-accuracy reasoner.
8. **Governance approves**: Offline evals show improved citation fidelity and fewer premature escalations without recall loss. Reviewers approve a canary rollout through Apollo.
9. **Canary and rollback safety**: Apollo deploys to 5% of eligible low-risk mission workflows. Observability verifies policy violations remain zero, p95 latency stays under 2500 ms, and operator trust ratings improve. The bundle is promoted; otherwise Apollo rolls back automatically.

## How Artemis Gets Better Safely

ClearGlassInc Artemis becomes more effective by converting operator behavior and mission outcomes into governed engineering artifacts. The system can propose better prompts, workflow thresholds, retrieval strategies, model routes, and eval cases, but all changes pass through human review and auditable rollout controls.

Key metrics:

- **Precision**: percentage of recommended entities/actions that operators confirm.
- **Recall**: percentage of important entities/events discovered by agents.
- **Citation fidelity**: percentage of claims backed by permitted lineage.
- **Policy pass rate**: zero tolerance for unauthorized disclosure or action.
- **Latency**: p95 and p99 response time by mission workflow.
- **Operator trust**: explicit ratings, edit distance, rejection reason frequency.
- **Mission impact**: time to triage, time to case closure, false-positive reduction, action effectiveness.

The result is a machine-speed intelligence platform with controlled self-improvement: fast enough for live operations, governed enough for coalition environments, and transparent enough for audited mission-critical use.

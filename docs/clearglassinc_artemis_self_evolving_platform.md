# ClearGlassInc Artemis — Self-Evolving AI Intelligence Platform (Palantir Gotham + Foundry + AIP + Apollo)

This document is a production-oriented full-stack architecture and implementation blueprint for **ClearGlassInc Artemis** in secure, coalition-aware, audited, low-latency environments.

---

## System Architecture

### 1) Layered runtime architecture

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                              Web / Operator UX                              │
│  React + TypeScript + Map/Timeline + Caseboard + Copilot + Approval Queue  │
└──────────────────────────────────────────────────────────────────────────────┘
                 │ mTLS + OIDC/JWT + Attribute Context (mission/compartment)
┌──────────────────────────────────────────────────────────────────────────────┐
│                               API Gateway Layer                             │
│ FastAPI Edge, Envoy, OPA/Rego PDP, request signing, rate limits, replay ID │
└──────────────────────────────────────────────────────────────────────────────┘
                 │
┌──────────────────────────────────────────────────────────────────────────────┐
│                              Service Fabric Layer                           │
│ Ingestion | Entity Resolution | Mission State | Agent Orchestrator |       │
│ Approval | Policy Decision | Eval Harness | Improvement Engine | Audit      │
└──────────────────────────────────────────────────────────────────────────────┘
                 │
┌──────────────────────────────────────────────────────────────────────────────┐
│                            Event + Stream Processing                         │
│ Kafka/Pulsar topics, DLQ, exactly-once sinks, temporal windows, CDC feeds  │
└──────────────────────────────────────────────────────────────────────────────┘
                 │
┌──────────────────────────────────────────────────────────────────────────────┐
│                      Foundry Data + Ontology + Applications                 │
│ Batch/stream transforms, lineage, ontology objects/actions, app logic       │
└──────────────────────────────────────────────────────────────────────────────┘
                 │                              │
                 │                              └────────► Gotham operational graph,
                 │                                        case investigations,
                 │                                        entity-centric analysis
                 │
┌──────────────────────────────────────────────────────────────────────────────┐
│                        AIP Agentic + Copilot Execution Plane                │
│ Prompt registry, tool registry, model router, evals, policy-constrained AI │
└──────────────────────────────────────────────────────────────────────────────┘
                 │
┌──────────────────────────────────────────────────────────────────────────────┐
│                           Apollo Deployment Control                          │
│ Signed artifacts, canary waves, runtime policy bundles, rollback/killswitch │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2) Palantir product role map

- **Gotham**: case operations, entity graph traversal, operational watchlists, investigation UX.
- **Foundry**: data integration, ontology modeling, transformation pipelines, typed object actions.
- **AIP**: copilots, agent tools, retrieval-grounded workflows, eval and prompt governance.
- **Apollo**: deployment orchestration, hardened updates, staged rollouts, rapid rollback.

### 3) Control-plane vs data-plane split

- **Control-plane**: policy bundles, model routing policies, prompt/workflow version manifests, deployment plans.
- **Data-plane**: event ingestion, enriched artifacts, ontology mutations, recommendations, approvals, execution traces.

### 4) Golden path request lifecycle

1. Event enters ingestion API.
2. Foundry stream transform enriches and writes ontology deltas.
3. AIP orchestrator runs agent graph with policy-constrained tool calls.
4. Recommendation produced with provenance and confidence.
5. Approval service applies mission/role thresholds.
6. On approval, action execution gateway submits signed operation.
7. Outcome + feedback recorded for evals and improvement proposals.

---

## Data and Ontology

### 1) Canonical entity model (Foundry Ontology)

#### Primary object types

- `Person`, `Organization`, `Asset`, `Device`, `Location`, `Event`
- `Alert`, `Case`, `Mission`, `Tasking`, `ActionPackage`, `IntelProduct`
- `PolicyControl`, `ApprovalRecord`, `OutcomeRecord`, `FeedbackSignal`

#### Required metadata on every object

- `object_id`, `version_id`, `schema_version`
- `confidence_score` (0–1)
- `source_reliability` (ordinal or weighted score)
- `lineage` (`dataset_id`, `pipeline_run_id`, transformation hash)
- `event_time`, `system_time` (bitemporal)
- `classification`, `releasability`, `compartment_tags`, `coalition_scope`
- `permissions_fingerprint` (policy snapshot hash)

### 2) Relationship semantics

- `ASSOCIATED_WITH`, `LOCATED_AT`, `OBSERVED_AT`, `DERIVED_FROM`
- `TRIGGERED_ALERT`, `PART_OF_CASE`, `PART_OF_MISSION`
- `APPROVED_BY`, `REJECTED_BY`, `SUPERSEDES`, `CONTRADICTS`, `CORROBORATES`

### 3) Temporal + lineage strategy

Use **bitemporal records** to preserve real-world event chronology and system knowledge chronology.

```sql
CREATE TABLE ontology_event_fact (
  fact_id TEXT PRIMARY KEY,
  object_id TEXT NOT NULL,
  predicate TEXT NOT NULL,
  value_json JSONB NOT NULL,
  confidence NUMERIC NOT NULL,
  event_time TIMESTAMPTZ NOT NULL,
  system_time TIMESTAMPTZ NOT NULL,
  valid_from TIMESTAMPTZ,
  valid_to TIMESTAMPTZ,
  lineage_json JSONB NOT NULL,
  classification TEXT NOT NULL,
  coalition_scope TEXT[] NOT NULL,
  compartment_tags TEXT[] NOT NULL
);
```

### 4) Ontology actions drive both human and AI behaviors

- Humans use the same action contracts in applications (e.g., `Case.open`, `Tasking.submit`).
- Agents invoke tool wrappers around those exact actions, forcing typed and policy-checkable operations.
- This guarantees parity between manual and agentic paths with uniform auditing.

### 5) Example ontology declaration (YAML)

```yaml
objects:
  Alert:
    properties:
      alert_id: string
      severity: enum[low, medium, high, critical]
      confidence_score: float
      mission_id: string
      status: enum[new, triaged, investigating, closed]
      event_time: datetime
      classification: enum[U, C, S, TS]
    links:
      related_entities: [Person, Organization, Asset, Device, Location]
      case: Case
    actions:
      - triage
      - escalate
      - close

  ActionPackage:
    properties:
      action_package_id: string
      recommendation_text: string
      predicted_impact: float
      risk_tier: enum[low, medium, high]
      approval_state: enum[draft, pending, approved, rejected, executed]
    links:
      source_alert: Alert
      mission: Mission
      approvals: [ApprovalRecord]
    actions:
      - submit_for_approval
      - approve
      - reject
      - execute
```

---

## AI and Agent Design

### 1) Copilot fleet

- **Analyst Copilot**: evidence assembly, contradiction detection, report drafting.
- **Commander Copilot**: options analysis, risk tradeoff, mission-timeline simulation.
- **Compliance Copilot**: data-handling and releasability checks before dissemination.

### 2) Multi-agent mission graph

```text
[TriageAgent] -> [EnrichmentAgent] -> [CorrelationAgent] -> [HypothesisAgent]
      -> [RecommendationAgent] -> [PolicyGateAgent] -> [ApprovalGate]
      -> [ExecutionAgent] -> [OutcomeScoringAgent]
```

### 3) Agent design constraints

- No free-form data-plane writes; only ontology action tools.
- No cross-compartment data joins without explicit policy grant.
- No operationally significant execution without human approval.
- Every tool invocation requires mission context, classification, and purpose.

### 4) Tool contract (Python)

```python
from pydantic import BaseModel, Field
from typing import Any, Literal

class ToolCall(BaseModel):
    request_id: str
    mission_id: str
    agent_id: str
    tool_name: str
    purpose: str
    classification: Literal["U", "C", "S", "TS"]
    args: dict[str, Any] = Field(default_factory=dict)

class ToolResponse(BaseModel):
    status: Literal["ok", "denied", "needs_approval", "error"]
    payload: dict[str, Any] = Field(default_factory=dict)
    provenance_id: str
    policy_trace_id: str
```

### 5) Model router strategy

Routing keys:

- latency budget (`p95 <= X ms`)
- required reasoning depth
- tool-use reliability profile
- classification boundary and hosting policy
- mission criticality and fallback policy

```python
def choose_model(route_ctx: dict) -> str:
    if route_ctx["criticality"] == "high" and route_ctx["needs_tools"]:
        return "model_ops_hardened_v3"
    if route_ctx["latency_ms_budget"] < 900:
        return "model_fast_v2"
    return "model_balanced_v4"
```

---

## Self-Improvement Loop

### 1) Improvement signal ingestion

Signals captured continuously:

- operator approvals/rejections + rationale
- manual corrections to entities/links/reports
- recommendation acceptance and override rates
- mission outcomes (success/failure/partial)
- downstream incident metrics
- latency/cost/quality telemetry

### 2) Closed-loop optimizer pipeline

```text
Feedback Capture
   -> Label Normalization
   -> Eval Dataset Builder
   -> Candidate Generator (prompt/workflow/router)
   -> Offline Eval + Safety Eval + Policy Eval
   -> Human Review Board
   -> Apollo Canary
   -> KPI Compare
   -> Promote or Rollback
```

### 3) Change object with strict governance

```json
{
  "change_id": "chg_2026_04_23_014",
  "asset_type": "workflow_graph",
  "target_asset": "recommendation_graph_v12",
  "candidate_version": "v12.3",
  "proposed_by": "improvement_engine",
  "evidence": {
    "eval_run_id": "eval_9931",
    "precision_delta": 0.047,
    "recall_delta": 0.021,
    "latency_delta_ms": -88,
    "policy_violations": 0
  },
  "risk_score": 0.19,
  "approval_required": true,
  "approval_state": "pending",
  "rollback_target": "v12.2"
}
```

### 4) Drift detection and auto-freeze controls

- **data drift**: embedding centroid and feature distribution shifts
- **label drift**: changing base-rate of positives/outcomes
- **behavioral drift**: tool usage or recommendation pattern changes
- **policy drift**: policy bundle updates invalidating old assumptions

If any drift policy is breached:

1. freeze autonomous proposal promotion,
2. alert governance,
3. run targeted re-evals,
4. require human clearance to resume.

### 5) Safe “gets better” boundaries

Allowed self-proposals:

- prompt phrasing changes
- retrieval/rerank parameter tuning
- workflow edge re-ordering among pre-approved nodes

Not allowed autonomously:

- policy relaxation
- expanded execution authority
- cross-coalition share rule changes

---

## Full-Stack Implementation

### 1) Frontend (React + TypeScript)

Core modules:

- Live Mission Grid
- Alert Triage Board
- Graph Investigation Workspace
- Action Package Composer
- Approval Queue + Policy Trace
- Eval/Drift Operations Console

Design requirements:

- persistent classification/releasability banner
- evidence/provenance panel on every AI recommendation
- inline explanation showing prompt/model/tool versions

### 2) API gateway and backend services

**Gateway**: FastAPI + Envoy + OPA hooks, request signing, idempotency.

**Services (Python preferred)**:

- `ingestion_service`
- `entity_resolution_service`
- `ontology_write_service`
- `agent_orchestrator_service`
- `approval_service`
- `policy_service`
- `evaluation_service`
- `improvement_service`
- `audit_ledger_service`

### 3) Event and streaming topology

Topics:

- `intel.raw.events`
- `intel.enriched.events`
- `alerts.generated`
- `actions.proposed`
- `actions.pending_approval`
- `actions.executed`
- `feedback.operator`
- `mission.outcomes`
- `eval.results`
- `improvement.proposals`

### 4) Data storage pattern

- **Lakehouse** for raw + refined + feature datasets.
- **Operational store** for active cases and mission state.
- **Graph index** for neighborhood expansion.
- **Vector index** for semantic retrieval.
- **Immutable audit ledger** for evidentiary trace.

### 5) Search + retrieval

Hybrid retrieval pipeline:

1. lexical prefilter (BM25)
2. vector retrieval (semantic)
3. ontology/graph expansion
4. policy filter by clearance/coalition/compartment
5. cross-encoder rerank

### 6) Deployment and runtime operations (Apollo)

- immutable, signed release bundles
- progressive rollout by mission cohort
- per-agent kill switch
- rollback to previous manifest in under 60 seconds
- policy and model manifest pinning per environment

---

## Security and Governance

### 1) Access control model

- Role + attribute + need-to-know enforcement.
- Row/column/entity-level policy constraints.
- Coalition boundary checks and compartment isolation.

### 2) Zero-trust execution

- mTLS service-to-service identity
- short-lived workload credentials
- explicit policy decision for every tool call
- encrypted transit + storage + key rotation

### 3) Immutable provenance chain

Every recommendation/action must persist:

- source object IDs + dataset lineage
- model ID + prompt version + workflow version
- tool call graph and policy decisions
- approving operator identity + timestamp

### 4) Policy-as-code (Rego)

```rego
package clearglassinc.artemis.authz

default allow = false

allow {
  clearance_ok
  coalition_ok
  compartment_ok
}

clearance_ok {
  input.user.clearance_rank >= input.resource.classification_rank
}

coalition_ok {
  input.resource.coalition_scope[_] == input.user.coalitions[_]
}

compartment_ok {
  not blocked_compartment
}

blocked_compartment {
  some t
  input.resource.compartment_tags[t]
  not input.user.compartment_access[t]
}
```

### 5) Model and prompt governance

- approved model registry by mission domain
- prompt registry with risk tier and owners
- minimum eval thresholds per change type
- mandatory human signoff for high-risk assets

---

## Code Examples

### 1) FastAPI action proposal endpoint with policy gate

```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

app = FastAPI(title="ClearGlassInc Artemis API")

class ActionProposalIn(BaseModel):
    mission_id: str
    alert_id: str
    action_type: str
    payload: dict


def get_user_context() -> dict:
    return {
        "user_id": "op-442",
        "clearance_rank": 3,
        "coalitions": ["coalition-alpha"],
        "compartment_access": {"maritime": True, "signals": False},
    }


def policy_check(user: dict, resource: dict) -> None:
    if user["clearance_rank"] < resource["classification_rank"]:
        raise HTTPException(status_code=403, detail="clearance denied")


@app.post("/v1/actions/propose")
def propose_action(req: ActionProposalIn, user=Depends(get_user_context)):
    policy_check(user, {"classification_rank": 2})
    return {
        "action_package_id": "apkg-10021",
        "approval_state": "pending",
        "mission_id": req.mission_id,
        "action_type": req.action_type,
    }
```

### 2) Stream consumer + triage pipeline

```python
import json
from confluent_kafka import Consumer, Producer

consumer = Consumer({
    "bootstrap.servers": "kafka:9092",
    "group.id": "artemis-triage",
    "auto.offset.reset": "earliest",
})
producer = Producer({"bootstrap.servers": "kafka:9092"})
consumer.subscribe(["intel.enriched.events"])


def score_alert(event: dict) -> dict:
    score = min(0.99, 0.35 + event.get("risk_signal", 0.0))
    severity = "critical" if score > 0.85 else "high" if score > 0.65 else "medium"
    return {"confidence": score, "severity": severity}


while True:
    msg = consumer.poll(1.0)
    if msg is None or msg.error():
        continue
    event = json.loads(msg.value())
    triage = score_alert(event)
    output = {"event": event, "triage": triage}
    producer.produce("alerts.generated", json.dumps(output).encode("utf-8"))
    producer.poll(0)
```

### 3) Workflow state machine for agent orchestration

```python
from enum import Enum

class Node(str, Enum):
    TRIAGE = "triage"
    ENRICH = "enrich"
    CORRELATE = "correlate"
    RECOMMEND = "recommend"
    POLICY = "policy"
    APPROVAL = "approval"
    EXECUTE = "execute"
    DONE = "done"


def run_agent_graph(ctx: dict) -> dict:
    node = Node.TRIAGE
    while node != Node.DONE:
        if node == Node.TRIAGE:
            ctx["priority"] = "high"
            node = Node.ENRICH
        elif node == Node.ENRICH:
            ctx["entities"] = ["asset:V-104", "org:O-55"]
            node = Node.CORRELATE
        elif node == Node.CORRELATE:
            ctx["correlation_score"] = 0.82
            node = Node.RECOMMEND
        elif node == Node.RECOMMEND:
            ctx["recommended_action"] = "open_case_and_brief_commander"
            node = Node.POLICY
        elif node == Node.POLICY:
            ctx["policy_ok"] = True
            node = Node.APPROVAL
        elif node == Node.APPROVAL:
            if ctx.get("approved"):
                node = Node.EXECUTE
            else:
                ctx["status"] = "awaiting_human_approval"
                return ctx
        elif node == Node.EXECUTE:
            ctx["status"] = "executed"
            node = Node.DONE
    return ctx
```

### 4) Eval pipeline + promotion guard

```python
from dataclasses import dataclass

@dataclass
class EvalMetrics:
    version: str
    precision: float
    recall: float
    latency_ms_p95: float
    policy_violations: int


def can_promote(m: EvalMetrics) -> bool:
    return (
        m.precision >= 0.90
        and m.recall >= 0.85
        and m.latency_ms_p95 <= 1200
        and m.policy_violations == 0
    )
```

### 5) Improvement proposal generator

```python
from uuid import uuid4


def create_improvement_proposal(eval_summary: dict) -> dict:
    return {
        "change_id": f"chg-{uuid4()}",
        "asset_type": "prompt",
        "target_asset": "recommendation_prompt",
        "candidate_version": eval_summary["candidate_version"],
        "evidence": {
            "precision_delta": eval_summary["precision_delta"],
            "recall_delta": eval_summary["recall_delta"],
            "latency_delta_ms": eval_summary["latency_delta_ms"],
        },
        "approval_required": True,
        "approval_state": "pending",
    }
```

### 6) SQL for mission-level quality dashboard

```sql
WITH scored AS (
  SELECT
    mission_id,
    DATE_TRUNC('day', occurred_at) AS d,
    AVG(CASE WHEN outcome_label = 'success' THEN 1 ELSE 0 END) AS success_rate,
    AVG(CASE WHEN was_overridden THEN 1 ELSE 0 END) AS override_rate,
    AVG(latency_ms) AS avg_latency_ms,
    AVG(precision_at_k) AS precision_at_k
  FROM mission_outcome_facts
  GROUP BY mission_id, DATE_TRUNC('day', occurred_at)
)
SELECT *
FROM scored
ORDER BY d DESC, mission_id;
```

---

## Scenario Walkthrough

### Phase A — live event ingress (T+00:00)

A suspicious multi-hop identity + vessel telemetry anomaly enters `intel.raw.events`.

- Ingestion signs and stores raw payload.
- Foundry stream transforms enrich with sanctions registry and travel graph.
- Ontology writes `Event`, updates `Asset`, creates `Alert`.

### Phase B — machine triage and recommendation (T+00:12)

- `TriageAgent` scores alert `0.87`, severity `critical`.
- `CorrelationAgent` finds two supporting historical patterns.
- `RecommendationAgent` drafts an `ActionPackage` with three options.
- `PolicyGateAgent` flags one option as approval-required high risk.

### Phase C — operator decision (T+00:18)

In the approval queue, operator sees:

- confidence and uncertainty range,
- evidence provenance chain,
- model/prompt/workflow versions,
- policy trace.

Operator approves two actions, rejects one and records reason: low utility under current weather constraints.

### Phase D — execution + mission outcome (T+04:00)

Approved actions execute through signed gateway. Outcome marked `preventive_success` with no policy incidents.

### Phase E — self-improvement (T+04:10 to T+48:00)

- Improvement engine aggregates similar rejections for weather-constrained tasking.
- Generates workflow tweak proposal and prompt refinement.
- Offline evals show improved precision, unchanged recall, no policy regressions.
- Governance board approves.
- Apollo canary rolls to 10% of cohorts.
- After stable KPIs for 48 hours, promotion to 100%.
- If KPI regression appears, automatic rollback to prior manifest.

This yields continuous learning with explicit human authority, full auditability, and mission-safe optimization.

---

## Disclaimer and Disclosure Pack (for content, code, posts, pages, and operator communications)

> **Important:** The following language is implementation guidance, not legal advice. For mission-specific, jurisdiction-specific, export-control, surveillance, or coalition-sharing contexts, legal review is recommended before production use.

### 1) System-wide baseline disclaimer

- **Recommended text (long-form):**
  - "ClearGlassInc Artemis provides decision-support outputs derived from available data and configured models. Outputs may contain uncertainty, incomplete context, or model error, and must be validated by authorized personnel before operational use."
- **Short-form variation:**
  - "AI-assisted output; human validation required before action."
- **Placement:** global UI footer, every generated intelligence product header, API response metadata (`disclaimer_version`).
- **Why needed:** reduces overreliance risk and clarifies human accountability for mission decisions.

### 2) High-risk advisory disclaimers

#### Financial / legal / medical / security-adjacent analysis
- **Recommended text (long-form):**
  - "This material is for operational analysis support and does not constitute financial, legal, medical, or professional advice. Consult qualified professionals and applicable command/legal authorities before relying on this information."
- **Short-form variation:**
  - "Not financial/legal/medical advice."
- **Placement:** analysis report preamble, copilot response banner when sensitive domains detected.
- **Why needed:** prevents mischaracterization of AI output as regulated professional advice.

#### Operational recommendation disclaimer
- **Recommended text (long-form):**
  - "Recommended actions are generated from probabilistic models and policy-constrained workflows. Final execution decisions require authorized human approval under mission rules of engagement and policy."
- **Short-form variation:**
  - "Recommendations are non-binding; approval required."
- **Placement:** action package cards, approval queue, execution API docs.
- **Why needed:** clarifies non-autonomous authority boundaries.

### 3) Accuracy, assumptions, and limitation disclosures

- **Recommended text (long-form):**
  - "Assessments are based on available sources at generation time and may change as new data arrives. Confidence scores indicate estimated reliability, not certainty."
- **Short-form variation:**
  - "Confidence is probabilistic, not certainty."
- **Placement:** near confidence indicators and timeline views.
- **Why needed:** aligns operator interpretation with model/statistical uncertainty.

### 4) Confidentiality, privacy, and data-handling disclaimer

- **Recommended text (long-form):**
  - "This content may include sensitive or compartmented information. Access, sharing, and retention are restricted by need-to-know, classification, coalition, and applicable privacy/security policies."
- **Short-form variation:**
  - "Handle per classification and need-to-know rules."
- **Placement:** page headers for case views, export dialogs, downloadable intel products.
- **Why needed:** reduces accidental disclosure and reinforces handling obligations.

### 5) Copyright, ownership, and third-party material

- **Recommended text (long-form):**
  - "Source materials may include third-party data subject to licensing and attribution requirements. Verify rights and attribution obligations before redistribution or external publication."
- **Short-form variation:**
  - "Verify license/attribution before sharing."
- **Placement:** publishing workflows, report export wizard, external sharing controls.
- **Why needed:** mitigates IP infringement and improper reuse risk.

### 6) AI-generated content disclosure

- **Recommended text (long-form):**
  - "This section was generated with AI assistance and reviewed by an authorized operator."
- **Short-form variation:**
  - "AI-assisted, human-reviewed."
- **Placement:** generated summaries, briefs, external communications where policy requires transparency.
- **Why needed:** satisfies transparency expectations and downstream trust requirements.

### 7) Endorsement / affiliation / sponsorship disclaimer

- **Recommended text (long-form):**
  - "References to external organizations, platforms, datasets, or products do not imply endorsement, sponsorship, or affiliation unless explicitly stated in writing."
- **Short-form variation:**
  - "No implied endorsement or affiliation."
- **Placement:** architecture documents, presentations, public-facing pages.
- **Why needed:** avoids false implication of partnerships or approvals.

### 8) Legal review escalation flags (strong recommendation)

Trigger mandatory counsel review when any of the following are present:

- cross-border data transfers or coalition releasability edge cases,
- surveillance-sensitive workflows or biometrics/person-tracking expansions,
- automated recommendations affecting liberty, sanctions, or critical infrastructure,
- novel retention/sharing terms for personally identifiable or classified data,
- jurisdiction-specific AI disclosure mandates.

### 9) Implementation hook (Python) for disclaimer injection

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class DisclaimerBundle:
    long_text: str
    short_text: str
    placement: str
    reason: str

DISCLAIMER_REGISTRY = {
    "baseline": DisclaimerBundle(
        long_text=(
            "ClearGlassInc Artemis provides decision-support outputs derived from "
            "available data and configured models. Outputs may contain uncertainty "
            "or error and must be validated by authorized personnel before use."
        ),
        short_text="AI-assisted output; human validation required.",
        placement="global_footer,report_header,api_metadata",
        reason="Human accountability and liability risk control",
    ),
    "operational_action": DisclaimerBundle(
        long_text=(
            "Recommendations are probabilistic and non-binding. Operationally "
            "significant actions require authorized human approval."
        ),
        short_text="Non-binding recommendation; approval required.",
        placement="approval_queue,action_card,runbook",
        reason="Prevents unsafe autonomous interpretation",
    ),
}


def resolve_disclaimers(content_tags: set[str]) -> list[DisclaimerBundle]:
    selected = [DISCLAIMER_REGISTRY["baseline"]]
    if "actionable" in content_tags:
        selected.append(DISCLAIMER_REGISTRY["operational_action"])
    return selected
```

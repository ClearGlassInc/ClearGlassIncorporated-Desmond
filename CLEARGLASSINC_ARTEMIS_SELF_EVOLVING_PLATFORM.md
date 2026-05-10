# ClearGlassInc Artemis — Self-Evolving AI Intelligence Platform (Production Blueprint)

## System Architecture

### 1) End-to-End Full-Stack Topology
```text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ Web UI (React/TS + Map + Timeline + Copilot + Governance Console)                 │
│ - Analyst workstation, commander dashboard, policy review, eval observability      │
└───────────────────────────────┬─────────────────────────────────────────────────────┘
                                │ OIDC + mTLS + device posture + signed sessions
┌───────────────────────────────▼─────────────────────────────────────────────────────┐
│ API Gateway (Envoy/Kong)                                                           │
│ - AuthN/AuthZ context propagation, schema validation, WAF, rate limits, audit IDs  │
└───────────────────────────────┬─────────────────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────────────────────┐
│ Backend Services (Python/FastAPI + Temporal + gRPC internal mesh)                  │
│ - ingest-service, ontology-service, case-service, mission-service                  │
│ - ai-orchestrator, policy-decision, eval-service, feedback-service                 │
└───────────────────────────────┬─────────────────────────────────────────────────────┘
                                │ events + commands + CDC
┌───────────────────────────────▼─────────────────────────────────────────────────────┐
│ Event Backbone (Kafka/Pulsar + Schema Registry + DLQ + Redis + exactly-once keys) │
└───────────────────────────────┬─────────────────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────────────────────┐
│ Foundry Data Plane                                                                  │
│ - batch/stream transforms, ontology objects, lineage, feature views, data contracts│
│ - lakehouse tables, graph index, vector index, temporal history                     │
└───────────────────────────────┬─────────────────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────────────────────┐
│ AIP AI Plane                                                                        │
│ - copilots, tool contracts, model router, eval harness, workflow agents             │
└───────────────────────────────┬─────────────────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────────────────────┐
│ Gotham Operational Plane                                                            │
│ - investigations, case graph, watchlists, mission operations, entity tracking       │
└───────────────────────────────┬─────────────────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────────────────────┐
│ Apollo Runtime Control                                                              │
│ - secure deployment rings, config/prompt bundles, drift rollback, signed releases   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 2) Smooth-Flow Runtime Path (No Hand-Off Gaps)
1. Ingest-service receives live/historical data with schema contract validation.
2. Foundry pipelines normalize and map records to ontology entities + relationship edges.
3. ai-orchestrator triggers multi-agent chain with mission-specific policy context.
4. policy-decision service enforces action gate before any operational effect.
5. Gotham case/workflow updated only after approval gate completion.
6. feedback-service captures all outcomes and pushes training/eval artifacts.
7. eval-service proposes upgrades; Apollo promotes safely via canary rings.

---

## Data and Ontology

### Canonical Ontology (Foundry Object Types)
```yaml
entities:
  Mission: [mission_id, theater, objective, priority, classification, coalition_scope]
  Signal: [signal_id, modality, source_system, observed_at, confidence, releasability]
  Event: [event_id, type, severity, event_time, mission_id, confidence, status]
  Person: [person_id, aliases, biometrics_ref, affiliations, confidence]
  Organization: [org_id, jurisdiction, sector, aliases, confidence]
  Asset: [asset_id, platform_type, owner, geolocation, state]
  Location: [loc_id, geohash, region, maritime_zone]
  Assessment: [assessment_id, hypothesis, confidence, model_version, prompt_version]
  Recommendation: [recommendation_id, action, risk_score, urgency, approval_state]
  Outcome: [outcome_id, effectiveness_label, collateral_risk, mission_impact]
  Feedback: [feedback_id, operator_id, correction_type, notes, created_at]

relationships:
  - SIGNAL_INDICATES_EVENT (Signal -> Event)
  - EVENT_OCCURS_AT (Event -> Location)
  - EVENT_INVOLVES_PERSON (Event -> Person)
  - EVENT_ASSOCIATED_WITH_ORG (Event -> Organization)
  - EVENT_TARGETS_ASSET (Event -> Asset)
  - ASSESSMENT_OF_EVENT (Assessment -> Event)
  - RECOMMENDATION_FROM_ASSESSMENT (Recommendation -> Assessment)
  - OUTCOME_OF_RECOMMENDATION (Outcome -> Recommendation)
  - FEEDBACK_ON_RECOMMENDATION (Feedback -> Recommendation)
```

### Temporal, Confidence, Lineage, Permissions
- **Bitemporal**: `valid_time` (real-world) + `system_time` (platform record time).
- **Confidence graph**: source reliability × corroboration × model certainty.
- **Lineage**: connector ID, transform hash, model hash, prompt version, policy version.
- **Permission tags**: classification, compartment, coalition releasability, mission scope.

```sql
CREATE TABLE ontology_event_state (
  event_id TEXT,
  mission_id TEXT,
  event_type TEXT,
  confidence NUMERIC(5,4),
  valid_from TIMESTAMPTZ,
  valid_to TIMESTAMPTZ,
  system_from TIMESTAMPTZ,
  system_to TIMESTAMPTZ,
  lineage JSONB,
  acl JSONB,
  PRIMARY KEY(event_id, system_from)
);
```

---

## AI and Agent Design

### Copilot Roles
- **Analyst Copilot**: hypothesis generation, evidence chains, anomaly explanation.
- **Commander Copilot**: course-of-action matrix, risk decomposition, mission trade-offs.

### Multi-Agent Graph (AIP)
```python
AGENT_GRAPH = {
  "triage": ["enrichment"],
  "enrichment": ["correlation", "threat_scoring"],
  "correlation": ["summarization"],
  "threat_scoring": ["recommendation"],
  "summarization": ["recommendation"],
  "recommendation": ["policy_sentinel"],
  "policy_sentinel": ["human_approval_queue"]
}
```

### Tool-Using Agent Contract (Python)
```python
from pydantic import BaseModel, Field
from typing import Literal, Any

class ToolCall(BaseModel):
    mission_id: str
    actor_id: str
    tool: Literal[
        "query_ontology",
        "search_cases",
        "open_case",
        "prepare_action_package",
        "get_policy_decision"
    ]
    payload: dict[str, Any] = Field(default_factory=dict)

class ToolResult(BaseModel):
    ok: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    audit_id: str
```

---

## Self-Improvement Loop

### Closed-Loop Learning + Approval
```text
Feedback/Corrections → Eval Case Builder → Candidate Prompt/Workflow/Router Change
→ Offline Benchmark → Shadow Traffic Eval → Human Review Board
→ Apollo Canary Ring 1% → Ring 10% → Ring 50% → Full Promote
→ Continuous Drift & SLO Watch → Auto Rollback if breached
```

### State Machine
```python
from enum import Enum

class ImprovementState(str, Enum):
    DRAFT = "draft"
    EVAL_RUNNING = "eval_running"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    CANARY = "canary"
    PRODUCTION = "production"
    ROLLED_BACK = "rolled_back"
```

### Drift + Guardrails
```python
def should_rollback(baseline: dict, live: dict) -> tuple[bool, str]:
    precision_drop = baseline["precision"] - live["precision"]
    recall_drop = baseline["recall"] - live["recall"]
    psi = live["psi"]
    p95_latency = live["p95_latency_ms"]

    if precision_drop > 0.05:
        return True, "precision regression"
    if recall_drop > 0.07:
        return True, "recall regression"
    if psi > 0.20:
        return True, "distribution drift"
    if p95_latency > 1800:
        return True, "latency SLO breach"
    return False, "healthy"
```

---

## Full-Stack Implementation

### Web UI (TypeScript/React)
```ts
export type Recommendation = {
  recommendationId: string;
  action: string;
  riskScore: number;
  urgency: "LOW" | "MEDIUM" | "HIGH";
  approvalState: "PENDING" | "APPROVED" | "REJECTED";
};

export async function approveRecommendation(id: string, rationale: string) {
  const res = await fetch(`/api/v1/recommendations/${id}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rationale }),
    credentials: "include"
  });
  if (!res.ok) throw new Error("approval failed");
  return res.json();
}
```

### API + Backend (FastAPI)
```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

app = FastAPI(title="ClearGlassInc Artemis")

class ApproveRequest(BaseModel):
    rationale: str

@app.post("/v1/recommendations/{recommendation_id}/approve")
async def approve(recommendation_id: str, req: ApproveRequest, user=Depends(...)):
    # 1) check policy
    # 2) persist approval
    # 3) emit RecommendationApproved event
    return {"ok": True, "recommendation_id": recommendation_id}
```

### Event Handler + Orchestration
```python
async def handle_signal_ingested(evt: dict):
    triage = await run_agent("triage", evt)
    enrich = await run_agent("enrichment", {**evt, "triage": triage})
    corr = await run_agent("correlation", {"enrichment": enrich})
    rec = await run_agent("recommendation", {"correlation": corr})
    policy = await run_agent("policy_sentinel", {"recommendation": rec})
    if not policy["allow"]:
        await enqueue_human_review(rec, policy)
```

### Policy-as-Code Check
```python
def allow_action(subject: dict, resource: dict, action: str, ctx: dict) -> tuple[bool, str]:
    if action in {"execute_operation", "release_coalition"} and not ctx.get("dual_approval"):
        return False, "dual approval required"
    if resource["classification"] not in subject["clearances"]:
        return False, "insufficient clearance"
    if resource["compartment"] not in subject["compartments"]:
        return False, "compartment mismatch"
    if ctx.get("coalition_boundary") and not ctx.get("releasable"):
        return False, "coalition releasability denied"
    return True, "allow"
```

### Evals + A/B Testing Pipeline
```python
def evaluate_candidates(candidates: list[dict], eval_set: list[dict]) -> list[dict]:
    scored = []
    for c in candidates:
        m = run_eval_suite(candidate=c, eval_set=eval_set)
        scored.append({"candidate": c["id"], **m})
    return sorted(scored, key=lambda x: (x["mission_impact"], x["precision"], -x["latency_ms"]), reverse=True)


def ab_bucket(session_id: str) -> str:
    return "B" if hash(session_id) % 100 < 10 else "A"  # 10% B canary
```

---

## Security and Governance

- Need-to-know enforcement using RBAC + ABAC + entity-level ACL tags.
- Row/column/entity security through policy pushdown in query layer.
- Coalition-aware compartmentalization with releasability constraints.
- Zero-trust execution: signed workloads, SPIFFE identities, mTLS service mesh.
- Immutable provenance: append-only audit log for data, prompts, models, approvals.
- Model governance: model registry, allowed use-cases, approval board, rollback IDs.
- Prompt governance: prompt versioning, diff reviews, eval gates, mandatory approvers.
- Workflow governance: mission-specific state machines pinned by version.

---

## Code Examples

### Ontology-Driven Query (Python)
```python
def fetch_event_context(ontology_client, event_id: str, mission_id: str):
    return ontology_client.query(
        """
        MATCH (e:Event {event_id: $event_id, mission_id: $mission_id})
        OPTIONAL MATCH (e)-[:EVENT_INVOLVES_PERSON]->(p:Person)
        OPTIONAL MATCH (e)-[:EVENT_ASSOCIATED_WITH_ORG]->(o:Organization)
        OPTIONAL MATCH (e)-[:EVENT_TARGETS_ASSET]->(a:Asset)
        RETURN e, collect(DISTINCT p) AS persons, collect(DISTINCT o) AS orgs, collect(DISTINCT a) AS assets
        """,
        {"event_id": event_id, "mission_id": mission_id}
    )
```

### Workflow State Machine (Temporal-style)
```python
class IncidentWorkflow:
    async def run(self, signal_event: dict):
        ctx = await ingest(signal_event)
        triage = await triage_activity(ctx)
        enrich = await enrich_activity(triage)
        recommendation = await recommend_activity(enrich)
        decision = await policy_gate_activity(recommendation)
        if decision["requires_human"]:
            await wait_for_human_approval(decision["ticket_id"])
        await finalize_case(decision)
```

---

## Scenario Walkthrough

1. **Live event ingress (T+0s):** encrypted burst signal enters ingestion API; schema, signatures, and classification checks pass.
2. **Automated triage (T+1s):** triage agent marks high priority; enrichment resolves vessel and operator associations.
3. **Cross-domain correlation (T+3s):** correlation agent detects pattern match to prior decoy maneuver profile.
4. **Action recommendation (T+5s):** recommendation agent suggests targeted surveillance, not interdiction, with uncertainty rationale.
5. **Approval gate (T+6s):** policy sentinel requires dual approval for kinetic escalation; recommendation queued to commander.
6. **Human decision (T+20s):** commander approves surveillance, rejects escalation, adds correction note.
7. **Outcome capture (T+20m):** mission confirms decoy; feedback labeled as true-negative escalation avoidance.
8. **Self-improvement (Nightly):** eval builder adds this case; prompt/workflow candidate improves decoy discrimination.
9. **Safe deployment (Next ring):** Apollo canary at 10% traffic improves precision and trust score; auto-promoted after SLO pass.
10. **Continuous safety:** if precision drops >5% or PSI >0.2, system auto-rolls back and opens governance incident.

This design gives ClearGlassInc Artemis a **self-evolving but human-governed** intelligence engine: fast, auditable, coalition-safe, and continuously improving without autonomous goal drift.

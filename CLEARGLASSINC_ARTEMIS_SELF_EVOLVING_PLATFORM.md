# ClearGlassInc Artemis — Self-Evolving AI Intelligence Platform

## System Architecture

### Mission Context
ClearGlassInc Artemis is a secure, coalition-aware, multi-domain intelligence platform running on **Palantir Gotham + Foundry + AIP + Apollo**. It is designed for low-latency, audited, human-governed operations where AI can recommend and optimize, but never self-authorize operationally significant actions.

### Layered Architecture (End-to-End)
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Frontend (React + TypeScript + Map/Timeline + Copilot Workspace)          │
└──────────────┬──────────────────────────────────────────────────────────────┘
               │ mTLS + OIDC + device posture + signed sessions
┌──────────────▼──────────────────────────────────────────────────────────────┐
│ API Gateway (Envoy/Kong): authn, rate limits, schema validation, routing   │
└──────────────┬──────────────────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────────────────────┐
│ Backend Services (Python/FastAPI + Temporal)                               │
│ - case-service  - mission-service  - ontology-query-service                │
│ - ai-orchestrator - policy-decision-service - eval-service                 │
└──────────────┬──────────────────────────────────────────────────────────────┘
               │ events / commands
┌──────────────▼──────────────────────────────────────────────────────────────┐
│ Streaming & Async Layer (Kafka + Schema Registry + DLQ + Redis)            │
└──────────────┬──────────────────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────────────────────┐
│ Data & Ontology (Foundry)                                                   │
│ - pipelines, ontology objects, lineage, lakehouse, feature views           │
│ - graph index, vector index, temporal state store                          │
└──────────────┬──────────────────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────────────────────┐
│ AI Runtime (AIP): copilots, tool contracts, model router, eval harness     │
└──────────────┬──────────────────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────────────────────┐
│ Operations (Gotham): investigations, entity tracking, mission workflows     │
└──────────────┬──────────────────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────────────────────┐
│ Deployment & Control (Apollo): progressive deploy, policy bundles, rollback │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data and Ontology

### Canonical Ontology (Foundry)

```yaml
entities:
  Mission:
    keys: [mission_id]
    attrs: [name, domain, theater, priority, classification, start_ts, end_ts]
  Person:
    keys: [person_id]
    attrs: [name, aliases, nationality, confidence, first_seen, last_seen]
  Organization:
    keys: [org_id]
    attrs: [name, sector, jurisdiction, confidence]
  Asset:
    keys: [asset_id]
    attrs: [asset_type, owner_ref, location, telemetry_state]
  Signal:
    keys: [signal_id]
    attrs: [source, source_ref, observed_at, ingested_at, modality, confidence]
  Event:
    keys: [event_id]
    attrs: [event_type, severity, event_ts, geohash, confidence, mission_id]
  Assessment:
    keys: [assessment_id]
    attrs: [judgment, confidence, analyst_ref, model_ref, prompt_ref]
  Recommendation:
    keys: [recommendation_id]
    attrs: [action_type, urgency, risk, rationale, status]
  Feedback:
    keys: [feedback_id]
    attrs: [operator_ref, disposition, correction, outcome_label, created_at]

relationships:
  - SIGNAL_INDICATES_EVENT (Signal -> Event)
  - EVENT_INVOLVES_PERSON (Event -> Person)
  - EVENT_TARGETS_ASSET (Event -> Asset)
  - PERSON_AFFILIATED_WITH_ORG (Person -> Organization)
  - ASSESSMENT_REFERENCES_EVENT (Assessment -> Event)
  - RECOMMENDATION_FROM_ASSESSMENT (Recommendation -> Assessment)
  - FEEDBACK_ON_RECOMMENDATION (Feedback -> Recommendation)
```

### Temporal + Lineage + Confidence
- **Bitemporal state**: `valid_time` and `system_time` to preserve historical truth.
- **Lineage**: source connector, transform hash, model ID, prompt version, workflow version.
- **Confidence model**: Bayesian update over multi-source corroboration.

```sql
CREATE TABLE artemis_event_fact (
  event_id TEXT PRIMARY KEY,
  mission_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  severity TEXT NOT NULL,
  event_ts TIMESTAMPTZ NOT NULL,
  valid_from TIMESTAMPTZ NOT NULL,
  valid_to TIMESTAMPTZ,
  system_from TIMESTAMPTZ NOT NULL,
  system_to TIMESTAMPTZ,
  confidence NUMERIC(5,4) NOT NULL,
  evidence_refs JSONB NOT NULL,
  lineage_ref TEXT NOT NULL,
  classification TEXT NOT NULL,
  releasability JSONB NOT NULL
);
```

---

## AI and Agent Design

### Copilots
1. **Analyst Copilot**: hypothesis generation, evidence linking, uncertainty articulation.
2. **Commander Copilot**: mission risk summary, action-option matrix, dependency impacts.

### Multi-Agent Workflow (AIP)
- **Triage Agent**: classify incoming signal, assign urgency.
- **Enrichment Agent**: resolve entities, fetch linked intel.
- **Correlation Agent**: cross-mission pattern detection.
- **Summary Agent**: produce briefing artifacts.
- **Recommendation Agent**: propose operational actions.
- **Policy Sentinel Agent**: preflight checks before human queue.

### Tooling Contract (Python)
```python
from pydantic import BaseModel
from typing import Literal, Any

class ToolRequest(BaseModel):
    tool: Literal["query_ontology", "open_case", "create_action_package", "get_policy_decision"]
    payload: dict[str, Any]
    actor_id: str
    mission_id: str

class ToolResult(BaseModel):
    ok: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    audit_ref: str
```

Operationally significant actions (`open_case`, `create_action_package`, execution) always require human approval.

---

## Self-Improvement Loop

### Closed-Loop Learning Pipeline
1. Capture feedback signals:
   - explicit operator corrections
   - accept/reject decisions
   - query-to-outcome chains
   - false-positive/false-negative outcomes
2. Generate eval cases automatically.
3. Propose upgrades: prompt/workflow/router heuristics.
4. Run offline + shadow evals.
5. Require human approval in governance UI.
6. Progressive rollout via Apollo ring deployment.
7. Monitor drift and rollback automatically when thresholds breach.

### Improvement State Machine
```python
from enum import Enum

class UpgradeState(str, Enum):
    DRAFT = "draft"
    EVAL_RUNNING = "eval_running"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    CANARY = "canary"
    PRODUCTION = "production"
    ROLLED_BACK = "rolled_back"
```

### Drift Detection
```python
def drift_detect(baseline: dict, live: dict) -> bool:
    # Example: PSI + precision drop gate
    psi = live["psi"]
    precision_drop = baseline["precision"] - live["precision"]
    return psi > 0.2 or precision_drop > 0.05
```

---

## Full-Stack Implementation

### Backend Service Skeleton (FastAPI)
```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel

app = FastAPI(title="ClearGlassInc Artemis API")

class SignalIn(BaseModel):
    signal_id: str
    source: str
    payload: dict
    mission_id: str

@app.post("/v1/signals/ingest")
async def ingest_signal(signal: SignalIn):
    # 1) persist raw
    # 2) publish kafka event
    # 3) return tracking id
    return {"ok": True, "tracking_id": f"trk-{signal.signal_id}"}
```

### Event Handler + Workflow Kickoff
```python
async def on_signal_ingested(evt: dict):
    triage = await run_agent("triage_agent", evt)
    enrich = await run_agent("enrichment_agent", {**evt, "triage": triage})
    corr = await run_agent("correlation_agent", {"enrich": enrich})
    rec = await run_agent("recommendation_agent", {"corr": corr})
    await enqueue_human_approval(rec)
```

### Policy-as-Code Check
```python
def can_execute_action(actor, mission, action, attrs):
    if action in {"execute_operation", "release_to_coalition"} and not attrs.get("dual_approval"):
        return False, "dual approval required"
    if attrs.get("classification") not in actor.clearances:
        return False, "insufficient clearance"
    if mission.compartment not in actor.compartments:
        return False, "compartment mismatch"
    return True, "allow"
```

### Model Router
```python
def route_model(task_type: str, classification: str, latency_budget_ms: int) -> str:
    if classification in {"SECRET", "TOP_SECRET"}:
        return "onprem-secure-llm"
    if task_type == "summarization" and latency_budget_ms < 1500:
        return "low-latency-distilled"
    return "high-accuracy-reasoner"
```

### Eval Pipeline (Nightly)
```python
def run_nightly_evals(candidates: list[dict], eval_set: list[dict]):
    results = []
    for c in candidates:
        metrics = score_candidate(c, eval_set)
        results.append({"candidate": c["id"], **metrics})
    return sorted(results, key=lambda r: (r["mission_impact"], r["precision"]), reverse=True)
```

---

## Security and Governance

- **Need-to-know ABAC/RBAC** with row/column/entity-level controls.
- **Coalition boundaries** with releasability tags and cross-domain guards.
- **Zero-trust runtime**: workload identity, signed artifacts, mTLS everywhere.
- **Immutable provenance**: append-only audit ledger for data/model/prompt decisions.
- **Model governance**: model cards, approval matrices, allowed task scopes.
- **Prompt governance**: versioned prompts, diff reviews, rollback handles.
- **Workflow governance**: state-machine version pinning by mission profile.

---

## Scenario Walkthrough (Cinematic + Operational)

1. **00:00:03 UTC**: A maritime SIGINT feed emits anomalous encrypted burst traffic near a protected corridor.
2. **00:00:04**: Ingestion pipeline normalizes payload, tags classification, writes lineage.
3. **00:00:05**: Triage Agent scores event severity as *High*, confidence 0.76.
4. **00:00:06**: Enrichment Agent resolves vessel ID ambiguity; Correlation Agent links similar pattern from 19 days prior.
5. **00:00:08**: Recommendation Agent drafts action package: "initiate focused surveillance + notify sector commander" with risk rationale.
6. **00:00:09**: Policy Sentinel blocks auto-execution due to dual-approval requirement; action enters commander queue.
7. **00:00:20**: Commander approves surveillance, rejects broad interdiction; adds correction note: "pattern resembles decoy behavior".
8. **00:05:00**: Outcome confirms decoy. Feedback pipeline labels previous broader recommendation as over-aggressive.
9. **02:00:00**: Nightly eval generator creates new test cases from this mission chain.
10. **Next deployment ring**: Prompt variant B improves precision on decoy-vs-threat classification by +6.2%; approved and promoted via Apollo canary.
11. **Continuous**: If live precision regresses >5% or drift PSI >0.2, Apollo rolls back automatically and opens a governance incident.

Result: ClearGlassInc Artemis becomes more accurate over time, but only through explicit review, traceable evidence, and controlled promotion.

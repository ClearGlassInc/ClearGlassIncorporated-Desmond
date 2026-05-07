# ClearGlassInc Artemis — Self-Evolving Intelligence Platform Blueprint

## Strategic Overview
ClearGlassInc Artemis needs a **mission-grade intelligence system** that increases decision speed while preserving operator trust, auditability, and coalition safety.

Business outcomes:
- **Speed:** reduce time-to-assessment from minutes to seconds with automated triage.
- **Reliability:** deterministic workflow orchestration + policy gates for high-stakes actions.
- **Security:** zero-trust, entity-level controls, immutable provenance.
- **Cost:** model routing + eval-driven optimization to keep high-end models for high-impact tasks only.
- **Compounding advantage:** a controlled self-improvement loop that continuously upgrades prompts/workflows.

---

## System Architecture

### 1) Layered Architecture (Palantir-native)

1. **Frontend Layer**
   - Analyst/Commander web app (React + TypeScript) embedded within Foundry/AIP application surfaces.
   - Live map, graph, timeline, case board, action queue, model explanation panel.

2. **API & Experience Gateway**
   - Python FastAPI gateway for UI, copilot sessions, workflow actions.
   - Request normalization, auth context propagation, tenancy/coalition tagging.

3. **Operational Services Layer (Python)**
   - `case-service`, `entity-service`, `alert-service`, `mission-service`, `feedback-service`.
   - Read/write through Foundry datasets, ontology APIs, and action abstractions.

4. **Data & Ontology Layer (Foundry + Gotham)**
   - Foundry for ingestion, transforms, ontology, application logic.
   - Gotham for operational entity tracking, investigations, temporal context, and operational workflows.

5. **AI Orchestration Layer (AIP)**
   - Copilots, tool-using agents, multi-agent plans, eval harnesses.
   - Model router, prompt registry, policy-aware tool permissions.

6. **Policy & Governance Layer**
   - Policy-as-code (OPA/Rego style) + Foundry/Gotham controls.
   - Need-to-know checks at entity, relation, field, and operation levels.

7. **Observability & Evaluation Layer**
   - Telemetry pipeline: logs, traces, metrics, eval scores, mission outcomes.
   - Drift detectors + auto-generated improvement proposals.

8. **Deployment/Runtime Layer (Apollo)**
   - Progressive rollout, canary, rollback, runtime kill-switches.
   - Signed artifacts, environment promotion, coalition-specific deployment channels.

### 2) Reference Repo Topology

```text
clearglassinc-artemis/
  apps/
    analyst-ui/                  # React app
    commander-ui/
  services/
    api-gateway/                 # FastAPI
    case-service/
    alert-service/
    feedback-service/
    ai-orchestrator/             # agent runtime adapters
  data/
    schemas/
    ontology/
    sql/
  workflows/
    triage/
    enrichment/
    action-package/
  policy/
    rego/
    test-cases/
  evals/
    datasets/
    harness/
    reports/
  infra/
    github/
      workflows/
    terraform/
    apollo-manifests/
  docs/
```

---

## Data and Ontology

### Core Ontology Objects
- **Entity**: `Person`, `Organization`, `Device`, `Location`, `Event`, `Asset`, `Case`, `Mission`.
- **Relationship**: typed directed edge with confidence + temporal validity.
- **Observation**: atomic fact from source with provenance.
- **Assessment**: machine/human judgment with rationale.
- **ActionRecommendation**: candidate response requiring approval state.

### Canonical Data Model

```sql
CREATE TABLE ontology_entity (
  entity_id UUID PRIMARY KEY,
  entity_type TEXT NOT NULL,
  canonical_name TEXT,
  confidence NUMERIC(5,4) NOT NULL,
  first_seen TIMESTAMPTZ NOT NULL,
  last_seen TIMESTAMPTZ NOT NULL,
  mission_tags TEXT[] DEFAULT '{}',
  coalition_scope TEXT NOT NULL,
  classification TEXT NOT NULL,
  lineage JSONB NOT NULL,
  created_by TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE ontology_relationship (
  rel_id UUID PRIMARY KEY,
  src_entity_id UUID NOT NULL,
  dst_entity_id UUID NOT NULL,
  rel_type TEXT NOT NULL,
  confidence NUMERIC(5,4) NOT NULL,
  valid_from TIMESTAMPTZ,
  valid_to TIMESTAMPTZ,
  evidence_refs TEXT[] NOT NULL,
  mission_context JSONB NOT NULL,
  lineage JSONB NOT NULL
);

CREATE TABLE feedback_signal (
  signal_id UUID PRIMARY KEY,
  signal_type TEXT NOT NULL, -- correction, approval, rejection, override
  object_ref TEXT NOT NULL,
  operator_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Ontology → AI Behavior Binding
- Agent tools declare required ontology scopes.
- Prompt context is generated from ontology slices constrained by mission and permission.
- Confidence/lineage determine model response style (assertive vs tentative + evidence-first).

---

## AI and Agent Design

### Copilot Personas
1. **Analyst Copilot**: evidence synthesis, hypothesis generation, entity disambiguation.
2. **Commander Copilot**: mission risk summary, decision options, action package drafting.

### Multi-Agent Pipeline
1. **Triage Agent**: classify incoming event + priority.
2. **Enrichment Agent**: pull contextual entities/relations.
3. **Correlation Agent**: detect cross-source patterns.
4. **Recommendation Agent**: propose ranked actions.
5. **Compliance Agent**: validate recommendation vs policy.
6. **Summarization Agent**: produce operator-facing brief.

### Operational Approval Gates
- Any “operationally significant” action moves to `PENDING_HUMAN_APPROVAL`.
- Human can approve/reject/request-alt-plan.
- Rejections become explicit training/eval signals.

---

## Self-Improvement Loop

### Signal Capture
- Inputs: prompt traces, tool calls, latency, operator edits, approvals/rejections, mission outcomes.
- Stored as immutable event stream + normalized feature store.

### Improvement Pipeline
1. Generate candidate improvements:
   - prompt variants
   - workflow branching changes
   - model routing thresholds
2. Offline replay on historical eval sets.
3. Shadow deployment in production.
4. Canary activation (5% → 25% → 100%).
5. Auto-rollback on guardrail breach.

### Guardrails
- No autonomous policy bypass.
- No self-modification of high-risk action logic without dual approval.
- All changes versioned, signed, and linked to eval evidence.

### Drift Detection
- Data drift: embedding/feature distribution shifts.
- Concept drift: precision/recall decay on labeled outcomes.
- Behavioral drift: deviation in operator trust score.

---

## Full-Stack Implementation (GitHub-Native)

### GitHub Actions Governance Pack

```yaml
name: ci-platform
on:
  pull_request:
  push:
    branches: [main]

jobs:
  quality-gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r requirements-dev.txt
      - run: ruff check .
      - run: mypy services
      - run: pytest -q

  policy-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: opa test policy/rego -v

  supply-chain:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: anchore/sbom-action@v0
      - uses: github/codeql-action/init@v3
        with: { languages: python, javascript }
      - uses: github/codeql-action/analyze@v3
```

### Branch Protection (Recommended)
- Require PR, CODEOWNERS review, signed commits.
- Require all checks above.
- Block force push.
- Dismiss stale reviews.

### Release Workflow (Apollo-Coupled)
- Artifact signing + provenance attestation.
- Deploy to staging coalition cell.
- Automated mission simulation tests.
- Manual approval gate for production promotion.

---

## Security and Governance

### Zero-Trust Controls
- Workload identity (OIDC) for all services.
- Mutual TLS east-west traffic.
- Secrets from secure vault only (no static repo secrets).

### Fine-Grained Access
- ABAC/RBAC hybrid:
  - subject attrs: clearance, role, coalition
  - object attrs: classification, mission tag, compartment
- Policy decision point called on each query/tool action.

### Immutable Provenance
- Append-only event log (hash chained).
- Every agent decision stores: prompt version, model version, tool outputs, policy snapshot.

### Model & Prompt Governance
- Prompt registry with semantic diff + required approvers.
- Model card enforcement: approved use-cases + forbidden contexts.
- Runtime allowlist for tools per agent persona.

---

## Code Examples

### 1) FastAPI Gateway + Policy Enforcement (Python)

```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from services.policy import authorize
from services.agents import run_triage_workflow

app = FastAPI(title="ClearGlassInc Artemis Gateway")

class EventIn(BaseModel):
    event_id: str
    source: str
    payload: dict
    mission_id: str

@app.post("/v1/events/triage")
async def triage_event(event: EventIn, user=Depends(authorize("event:triage"))):
    decision = await run_triage_workflow(event.model_dump(), user_context=user)
    if decision["requires_human_approval"]:
        return {"status": "PENDING_HUMAN_APPROVAL", "proposal": decision}
    return {"status": "AUTO_EXECUTED", "result": decision}
```

### 2) Event Handler + Feedback Capture

```python
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class FeedbackSignal:
    signal_type: str
    object_ref: str
    operator_id: str
    mission_id: str
    payload: dict

class FeedbackService:
    def __init__(self, repo, bus):
        self.repo = repo
        self.bus = bus

    async def record(self, signal: FeedbackSignal):
        row = {
            "signal_type": signal.signal_type,
            "object_ref": signal.object_ref,
            "operator_id": signal.operator_id,
            "mission_id": signal.mission_id,
            "payload": signal.payload,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await self.repo.insert_feedback(row)
        await self.bus.publish("feedback.signals", row)
```

### 3) Model Router (Risk/Latency/Cost Aware)

```python
def route_model(task_type: str, classification: str, latency_budget_ms: int):
    if classification in {"TOP_SECRET", "SCI"}:
        return "onprem-secure-llm-v2"
    if task_type == "summarization" and latency_budget_ms < 1200:
        return "fast-distilled-8b"
    if task_type in {"reasoning", "recommendation"}:
        return "high-reasoning-70b"
    return "balanced-32b"
```

### 4) Self-Improvement Evaluator

```python
class PromptCandidateEvaluator:
    def __init__(self, eval_runner, registry, thresholds):
        self.eval_runner = eval_runner
        self.registry = registry
        self.thresholds = thresholds

    async def evaluate_and_propose(self, candidate_version: str, baseline_version: str):
        baseline = await self.eval_runner.run(prompt_version=baseline_version)
        candidate = await self.eval_runner.run(prompt_version=candidate_version)

        delta_precision = candidate.precision - baseline.precision
        delta_latency = candidate.p95_latency_ms - baseline.p95_latency_ms
        trust_delta = candidate.operator_trust - baseline.operator_trust

        if (
            delta_precision >= self.thresholds.min_precision_gain
            and delta_latency <= self.thresholds.max_latency_regression
            and trust_delta >= 0
        ):
            return {"approved_for_canary": True, "evidence": candidate.to_dict()}
        return {"approved_for_canary": False, "reason": "failed guardrails"}
```

### 5) Workflow State Machine

```python
from enum import Enum

class CaseState(str, Enum):
    INGESTED = "INGESTED"
    TRIAGED = "TRIAGED"
    ENRICHED = "ENRICHED"
    RECOMMENDED = "RECOMMENDED"
    PENDING_HUMAN_APPROVAL = "PENDING_HUMAN_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"

ALLOWED = {
    CaseState.INGESTED: {CaseState.TRIAGED},
    CaseState.TRIAGED: {CaseState.ENRICHED, CaseState.REJECTED},
    CaseState.ENRICHED: {CaseState.RECOMMENDED},
    CaseState.RECOMMENDED: {CaseState.PENDING_HUMAN_APPROVAL},
    CaseState.PENDING_HUMAN_APPROVAL: {CaseState.APPROVED, CaseState.REJECTED},
    CaseState.APPROVED: {CaseState.EXECUTED},
}
```

---

## Performance and Scaling Plan

- **P95 latency targets**:
  - event triage: < 2s
  - enriched recommendation: < 8s
  - case summary refresh: < 1.5s
- **Scalability**:
  - Kafka/PubSub partitioning by mission/region.
  - Vector index sharding by coalition + classification domain.
  - Async workflow workers with autoscaling on queue lag.
- **Reliability**:
  - Circuit breakers on external sources.
  - Idempotent event processors.
  - Apollo rollback recipes per service/model/prompt release.

---

## Immediate Execution Steps (Prioritized)

1. Stand up ontology baseline + policy model in Foundry/Gotham.
2. Ship API gateway + triage workflow with strict human approval gate.
3. Implement feedback schema and immutable telemetry stream.
4. Build eval harness and prompt registry with approval workflow.
5. Integrate Apollo progressive delivery + rollback automation.
6. Enforce GitHub branch protections, CodeQL, SBOM, OPA policy CI.
7. Run 30-day controlled pilot on 2 mission cells; tune routing and prompts.

---

## Scenario Walkthrough (End-to-End Self-Improvement)

1. **Live event enters** from ISR feed: anomalous device cluster near protected asset.
2. **Triage agent** scores severity High (0.87), opens Case `C-78421`.
3. **Enrichment/correlation agents** link to prior pattern + known logistics entity.
4. **Recommendation agent** proposes: “elevate surveillance + notify commander + prep interdiction package.”
5. **Compliance agent** flags action package requires commander approval due to coalition boundary impact.
6. **Commander approves surveillance, rejects interdiction.**
7. System logs rejection reason: insufficient confidence on entity linkage.
8. Feedback pipeline creates eval example where overconfident recommendation is penalized.
9. New prompt candidate adds stricter evidence threshold language and mandatory uncertainty rubric.
10. Candidate passes offline eval (+4.2 precision, -0.1 recall, +0.6 trust) and canary.
11. Apollo promotes prompt v43 → v44 for this mission cell only.
12. Future similar cases show fewer false-positive interdiction suggestions, higher operator acceptance.

This is how ClearGlassInc Artemis compounds operational advantage while retaining human command authority.

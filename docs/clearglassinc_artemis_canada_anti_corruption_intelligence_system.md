# ClearGlassInc Artemis — Canada Anti-Corruption Intelligence System

## System Architecture

ClearGlassInc Artemis is deployed as a secure, audited, self-improving intelligence platform using:

- **Palantir Gotham** for investigations, link analysis, case timelines, watchlists, and entity tracking.
- **Palantir Foundry** for data integration, ontology modeling, transforms, quality checks, and operational applications.
- **Palantir AIP** for copilots, agent workflows, LLM extraction/routing, evaluations, and assistive automation.
- **Palantir Apollo** for policy-controlled deployment, progressive releases, rollback, runtime controls, and environment governance.

### Layered full-stack blueprint

```text
[Web UI + Analyst Workbench + Commander Dashboard]
              |
        [API Gateway]
              |
[Workflow Service] [Case Service] [Evidence Service] [Routing Service]
              |
         [Event Bus / Stream]
              |
[Intake Parser] [Auto-Scan Crawler] [Entity Resolution] [Risk Scoring]
              |
       [Foundry Data Products + Ontology]
              |
[Vector Store + Search Index + Lakehouse + Immutable Audit Log]
              |
      [AIP Agent Runtime + Model Router + Evals]
              |
         [Apollo Deployment Control]
```

### Core modules required by mission

1. **Intake parser**
   - Inputs: text, email, PDF, screenshots, URLs, CSV, pasted narratives.
   - OCR + extraction + normalization into ontology objects.
   - Chain-of-custody metadata attached at ingest.

2. **Risk scoring engine**
   - Hybrid rules + statistical anomaly model + graph intelligence.
   - Red flags: bid-rigging, invoice inflation, shell vendors, COI patterns, unusual gifts, BO overlap, repeated single-vendor wins.

3. **Auto-scan layer**
   - Scheduled and event-driven crawlers for procurement records, registries, court filings, sanctions and Canada open datasets.
   - Delta detection, baseline drift, anomaly queues.

4. **Workflow layer**
   - Severity assignment, analyst queues, evidence lock, report drafting, approval gates, authority routing.
   - Routes by jurisdiction/issue type to:
     - Federal Contracting Fraud Tip Line (federal procurement).
     - CAFC (general fraud/cyber/ID theft).
     - RCMP (federal corruption/foreign bribery/major corruption scope).
     - Local police (municipal/provincial/local business corruption).

---

## Data and Ontology

### Ontology (Foundry object model)

#### Entity classes

- `Person`
- `Organization`
- `GovernmentAgency`
- `Contract`
- `Invoice`
- `Tender`
- `GiftHospitalityEvent`
- `TipReport`
- `Case`
- `EvidenceArtifact`
- `Jurisdiction`
- `SanctionRecord`
- `CourtFiling`
- `BeneficialOwnershipRecord`

#### Relationship types

- `AWARDED_TO(Contract -> Organization)`
- `SUBMITTED_BY(Tender -> Organization)`
- `ASSOCIATED_WITH(Person -> Organization)`
- `BENEFICIAL_OWNER_OF(Person -> Organization)`
- `RELATED_TO_CASE(Entity -> Case)`
- `SUPPORTS(EvidenceArtifact -> AllegationIndicator)`
- `WITHIN_JURISDICTION(Case -> Jurisdiction)`
- `REFERRED_TO(Case -> AuthorityEndpoint)`

#### Temporal + confidence + lineage fields

```sql
-- Example Foundry/warehouse table pattern
CREATE TABLE ontology_events (
  event_id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  event_time TIMESTAMP NOT NULL,
  valid_from TIMESTAMP,
  valid_to TIMESTAMP,
  confidence_score DOUBLE PRECISION CHECK (confidence_score BETWEEN 0 AND 1),
  source_url TEXT,
  source_hash TEXT,
  ingestion_run_id TEXT,
  lineage_json JSONB,
  classification TEXT,
  coalition_domain TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Permission-aware ontology behavior

- Every object tagged with:
  - `classification` (e.g., Protected A/B)
  - `compartment` (operation/program)
  - `coalition_domain` (CAN, FiveEyes subset, etc.)
  - `need_to_know_tags`
- Policy engine enforces row/column/entity visibility before AI inference or UI rendering.
- Agents only retrieve entities user is authorized to view.

---

## AI and Agent Design

### Copilots

1. **Analyst Copilot**
   - Summarizes tips, proposes indicators, requests missing evidence, drafts neutral reports.
2. **Commander Copilot**
   - Portfolio view: risk concentration, active case status, SLA breaches, response recommendations.

### Multi-agent workflow

- `intake_agent`: parse + normalize + quality check.
- `enrichment_agent`: attach public-source context and entity graph neighbors.
- `risk_agent`: compute score and explain top factors.
- `routing_agent`: determine jurisdiction and authority endpoint.
- `report_agent`: draft structured report package.
- `review_gate_agent`: enforce mandatory human approval before external referral.

### Authority routing rules (policy-first)

```python
from enum import Enum

class Destination(str, Enum):
    FEDERAL_CONTRACT_TIP = "federal_contracting_fraud_tip_line"
    CAFC = "canadian_anti_fraud_centre"
    RCMP = "rcmp"
    LOCAL_POLICE = "local_police"
    HOLD_REVIEW = "hold_for_human_review"


def route_case(jurisdiction: str, issue_types: set[str], is_federal_contract: bool) -> Destination:
    if is_federal_contract and "procurement_fraud" in issue_types:
        return Destination.FEDERAL_CONTRACT_TIP
    if issue_types & {"fraud", "cybercrime", "identity_theft"}:
        return Destination.CAFC
    if issue_types & {"federal_corruption", "foreign_bribery", "major_public_corruption"}:
        return Destination.RCMP
    if jurisdiction in {"municipal", "provincial", "local"}:
        return Destination.LOCAL_POLICE
    return Destination.HOLD_REVIEW
```

---

## Self-Improvement Loop

### Closed-loop learning pipeline

1. Collect signals:
   - analyst corrections
   - false-positive/false-negative outcomes
   - submission acceptance/rejection
   - downstream case outcomes
   - latency + queue burden
2. Convert into eval records.
3. Run offline/online evaluations.
4. Propose improvements (prompts/rules/model routing/workflow transitions).
5. Human governance board approves/rejects.
6. Apollo progressive deploy.
7. Shadow mode + canary + rollback guardrails.

### Safe evolution controls

- No autonomous policy or objective changes.
- All high-impact changes require signed human approval.
- Prompt/model/workflow versions immutable + traceable.
- Drift alarms trigger rollback to last known good package.

```python
@dataclass
class ProposedUpgrade:
    upgrade_id: str
    target: str  # prompt|router|rule|workflow
    baseline_version: str
    candidate_version: str
    expected_gain: float
    risk_level: str
    requires_human_approval: bool = True


def approve_and_deploy(upgrade: ProposedUpgrade, approver: str):
    assert upgrade.requires_human_approval
    record_approval(upgrade.upgrade_id, approver)
    deploy_canary(upgrade.candidate_version)
    if not passes_canary_slo(upgrade.candidate_version):
        rollback(upgrade.baseline_version)
        mark_failed(upgrade.upgrade_id)
    else:
        promote(upgrade.candidate_version)
```

---

## Full-Stack Implementation

### Frontend (TypeScript/React)

- Dashboard tabs:
  - Intake queue
  - Risk heatmap
  - Entity graph
  - Case timeline
  - Referral routing panel
  - Eval and drift panel

```ts
// src/api/cases.ts
export async function submitTip(payload: TipSubmission) {
  return fetch('/api/v1/tips', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }).then(r => r.json());
}
```

### API gateway + backend (Node.js + Python services)

- **Node.js gateway**: authn/authz, request validation, rate limiting, case APIs.
- **Python intel services**: extraction, scoring, graph analytics, eval pipelines.

```ts
// gateway/src/routes/tips.ts
router.post('/api/v1/tips', requireAuth, async (req, res) => {
  enforcePolicy(req.user, 'tip:create');
  const tip = await intakeClient.createTip(req.body, req.user);
  await eventBus.publish('tip.received', { tipId: tip.id, actor: req.user.id });
  res.status(202).json({ id: tip.id, status: 'queued' });
});
```

```python
# services/intel/intake_worker.py
def handle_tip_received(event: dict):
    tip = load_tip(event["tipId"])
    artifacts = extract_artifacts(tip)
    entities = llm_extract_entities(artifacts)
    normalized = normalize_entities(entities)
    save_entities(normalized)
    emit("tip.parsed", {"tipId": tip.id, "entityCount": len(normalized)})
```

### Event + data stack

- Kafka/NATS for stream events.
- Foundry pipelines for curated data products.
- Postgres + object storage + vector index + search (OpenSearch).

```python
# services/scoring/risk_engine.py
RED_FLAG_WEIGHTS = {
    "repeated_vendor_wins": 18,
    "beneficial_owner_overlap": 20,
    "invoice_inflation_pattern": 15,
    "conflict_of_interest": 22,
    "shell_vendor_signal": 17,
    "gift_irregularity": 8,
}


def score_case(flags: dict[str, float], anomaly_score: float) -> int:
    weighted = sum(RED_FLAG_WEIGHTS[k] * v for k, v in flags.items() if k in RED_FLAG_WEIGHTS)
    total = min(100, int(weighted + anomaly_score * 25))
    return total
```

### Workflow state machine

```python
from transitions import Machine

states = [
    "INGESTED", "PARSED", "ENRICHED", "SCORED", "REVIEW", "APPROVED", "REFERRED", "CLOSED"
]

class CaseFlow:
    def __init__(self):
        self.machine = Machine(model=self, states=states, initial="INGESTED")
        self.machine.add_transition("parse", "INGESTED", "PARSED")
        self.machine.add_transition("enrich", "PARSED", "ENRICHED")
        self.machine.add_transition("score", "ENRICHED", "SCORED")
        self.machine.add_transition("send_review", "SCORED", "REVIEW")
        self.machine.add_transition("approve", "REVIEW", "APPROVED")
        self.machine.add_transition("refer", "APPROVED", "REFERRED")
        self.machine.add_transition("close", "REFERRED", "CLOSED")
```

---

## Security and Governance

### Zero-trust + policy-as-code

- OIDC + hardware-backed MFA + short-lived workload identities.
- ABAC/RBAC hybrid for user + data + mission attributes.
- Row/column/entity enforcement in query proxy and service mesh.
- End-to-end encryption, key rotation, tamper-evident logs.

```rego
package artemis.authz

default allow = false

allow {
  input.user.clearance_level >= input.resource.required_clearance
  input.user.coalition_domain == input.resource.coalition_domain
  input.action == "read"
}
```

### Governance controls

- Prompt registry with version tags and risk labels.
- Model registry with approved-use matrix.
- Evals required before promotion.
- Immutable audit timeline across user actions, agent actions, and policy decisions.

---

## Code Examples

### Structured output contract for reasoning layer

```json
{
  "summary": "string",
  "jurisdiction": "federal|provincial|municipal|private|foreign|unknown",
  "allegations_or_indicators": [
    {"type": "indicator", "label": "repeated_vendor_wins", "confidence": 0.81}
  ],
  "evidence_quality": "weak|moderate|strong",
  "entities": [{"id": "org:123", "name": "Example Vendor Ltd"}],
  "risk_score": 0,
  "recommended_next_action": "monitor|request_more_evidence|route_to_authority",
  "draft_report_text": "string",
  "missing_evidence": ["beneficial ownership filing", "invoice originals"]
}
```

### Prompt template (AIP)

```text
System: You are CanadaCorruptScan for ClearGlassInc Artemis.
Rules:
- Distinguish allegation vs indicator vs confirmed fact.
- Never assert guilt.
- Preserve URL, timestamps, and evidence hash.
- Return valid JSON only.
```

### Eval pipeline skeleton

```python
def run_eval_suite(dataset_id: str, candidate_prompt: str, candidate_model: str):
    cases = load_eval_cases(dataset_id)
    results = [score_case_output(infer(c, candidate_prompt, candidate_model), c.expected) for c in cases]
    metrics = aggregate(results)
    save_eval_result(dataset_id, candidate_prompt, candidate_model, metrics)
    return metrics
```

---

## Scenario Walkthrough (End-to-End)

1. A whistleblower email with PDF invoices and screenshot evidence enters intake.
2. OCR + extractor identifies contract numbers, vendor, payment values, and timeline.
3. Enrichment agent finds same vendor repeatedly winning similar tenders and recent address/ownership changes.
4. Risk engine outputs score `87` with top factors: repeated wins + BO overlap + invoice inflation indicators.
5. Routing engine classifies case as federal procurement fraud and recommends Federal Contracting Fraud Tip Line.
6. Analyst reviews AI draft report, edits one claim from “likely” to “possible,” and approves submission package.
7. Workflow logs full provenance and referral action; case becomes `REFERRED`.
8. Outcome later marked as “accepted for investigation.” This feedback is stored as positive label.
9. Self-improvement job includes this case in weekly evals; candidate prompt shows improved precision by 4.2% in procurement cases.
10. Governance board approves upgrade; Apollo canary deploys to 10%, passes latency/quality thresholds, then promotes globally.

---

## MVP Delivery Plan

### Phase 1 (4–6 weeks): Federal procurement focus
- Intake parser + procurement rule pack + referral routing to federal contracting tip flow.
- Human-reviewed reporting only.

### Phase 2 (6–10 weeks): Broader fraud channels
- Add CAFC fraud/cyber/identity workflows and RCMP/local police routing refinement.
- Add entity graph expansion + court/sanctions integrations.

### Phase 3 (10–16 weeks): Full self-improving runtime
- Prompt/workflow/router optimization loop with strict approvals.
- Drift detection + automated rollback controls + mission impact dashboards.

This design keeps **detection separate from accusation**, ensuring ClearGlassInc Artemis remains evidence-driven, legally safe, and operationally effective.

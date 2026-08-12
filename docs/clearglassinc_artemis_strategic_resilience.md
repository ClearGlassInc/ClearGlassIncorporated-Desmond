# ClearGlassInc Artemis — Strategic Resilience & Growth Intelligence

> **Status:** implementation blueprint plus a local deterministic reference core. Palantir products, feeds, procurements, customers, and deployments described here are target-state integrations—not evidence that they are provisioned or endorsed.

## System Architecture

ClearGlassInc Artemis turns lawful public Arctic and NATO milestones into evidence-backed, diversified commercial experiments. The hard invariant is **public evidence → normalized signal → analyst assessment → draft recommendation → human approval → reversible validation**. It never performs collection against restricted systems or converts a headline directly into revenue.

```text
Public allowlisted sources / tender exports / operator uploads
  → ingestion quarantine → parser + malware/content checks → source registry
  → Foundry pipelines (quality, dedupe, temporal normalization, lineage)
  → Foundry Ontology (Signal, Source, Organization, BudgetPath, Opportunity)
  → AIP bounded agents → policy decision point → approval queue
  → Gotham investigation/case views (when provisioned)
  → React/Next.js executive console + evidence and scenario workbench
  → immutable audit sink, OpenTelemetry, eval store
  → Apollo rings: dev → evaluation → canary → production → rollback
```

| Layer | Production component | Boundary |
|---|---|---|
| Web | Next.js/TypeScript signal inbox, evidence viewer, bear-case lab, approval queue | No authorization decisions in the browser |
| API | FastAPI BFF; `/signals`, `/assessments`, `/approvals`, `/evals` | OIDC, schema validation, rate/size limits, purpose binding |
| Data | Foundry datasets/lakehouse; Kafka-compatible stream ingress | Raw data quarantined; immutable source snapshots |
| Ontology | Foundry Ontology objects, links and Actions | Actions validate state and policy server-side |
| Operations | Gotham cases, investigations and entity tracking | Public commercial/policy intelligence only |
| AI | AIP Logic/workflows, tool registry, evaluation suites, model router | Model output is untrusted; no self-granted tools or authority |
| Delivery | Apollo environments, signed releases, health gates and rollback | Human promotion and protected production environment |

Latency objectives are p95 < 60 seconds from accepted feed event to normalized signal, p95 < 5 seconds for stored assessment queries, and RPO 15 minutes/RTO 4 hours for the decision store. These are design objectives until measured in a deployed environment.

## Data and Ontology

`Source` proves provenance; `Signal` represents one public observation; `OpportunityAssessment` contains explicitly separated epistemic categories; `BearCase` quantifies nine concentration risks. The Python reference contract is canonical for local validation. 【../artemis/strategic_resilience.py】

```text
Source ─supports→ Signal ─indicates→ CapabilityRequirement
  │                 ├─involves→ Organization ─located_in→ Geography
  │                 ├─may_use→ BudgetPath
  │                 └─produces→ OpportunityAssessment ─tested_by→ Experiment
  └─repeated_by→ Source
OpportunityAssessment ─depends_on→ Vendor|Cloud|Hardware|Regulation|FundingSource
Recommendation ─requires→ Approval ─authorizes→ ValidationExperiment
Feedback ─evaluates→ Recommendation|PromptVersion|WorkflowVersion|ModelRoute
```

Every object carries `valid_time`, `observed_time`, source IDs, transformation lineage, confidence, tenant, coalition release scope, compartment, retention label, and policy tags. Access is intersected—not unioned—across organization, mission, purpose, compartment, geography, and source licence. Temporal graph queries must specify an `as_of` time to avoid treating stale relationships as current.

Signal lifecycle has distinct commercial weights: `MENTIONED` and `ANNOUNCED` support research only; `FUNDED` establishes a budget indication; `PROCURED` establishes a buying mechanism; `PILOTED`, `DEPLOYED`, and `SCALED` establish delivery evidence. Even a funded signal permits forecast validation only when customer type and budget path are present.

## AI and Agent Design

| Bounded agent | Read tools | Draft tools | Forbidden without human gate |
|---|---|---|---|
| Source sentinel | allowlist, source registry, duplicate graph | quarantine/rejection reason | Bypass source validation |
| Arctic analyst | Ontology/search/temporal graph | signal and competing hypotheses | Infer military intent from civilian science |
| NATO policy analyst | official publication and tender indexes | lifecycle classification | Claim endorsement or contract intent |
| Opportunity architect | capability catalog, customer map | experiment and reusable-IP proposal | Forecast from policy alone |
| Bear-case challenger | dependency graph, sanctions/export-control public data | rupture scenario and mitigations | Legal determination |
| Revenue validator | CRM aggregate, public budget path | interview/pilot plan | Contact, price, contract, or spend |
| Improvement agent | redacted feedback and eval results | versioned prompt/router/workflow patch | Activate, expand tools, loosen policy |

Multi-agent execution is a typed state machine: `RECEIVED → QUARANTINED → VERIFIED → ASSESSED → DRAFT → IN_REVIEW → APPROVED → VALIDATING → CLOSED`. AIP may call only registered read tools and draft Actions. Foundry Actions for external outreach, case sharing, procurement response, pricing, or production changes require short-lived, package-bound approval created by a designated reviewer. Rejection creates a new audit event; history is never rewritten.

## Self-Improvement Loop

1. Capture corrections, cited-claim edits, accepted/rejected recommendations, alert dispositions, validation results, latency, and optional trust ratings.
2. Redact sensitive text, enforce consent/retention, and compile immutable train/eval snapshots split by time and source family.
3. Generate a candidate prompt, routing rule, heuristic, or workflow diff. Goal, permissions, approval thresholds, and source boundaries are immutable.
4. Run unit/policy tests plus precision, recall, calibration error, citation coverage, unsupported-claim rate, p95 latency, cost, source diversity, and concentration-risk evals.
5. Require non-inferiority on safety and citation metrics, statistical confidence on quality gains, security review, and named human approval.
6. Apollo deploys a small canary with a pinned model, prompt, policy, dataset and code digest. Automatic rollback fires on policy violation, provenance loss, error-budget breach, or confidence degradation.
7. Promote only after the observation window; append approval, metrics and release identity to the audit plane.

A/B assignment is deterministic by hashed case ID, never operator identity. Feedback is not silently used as training data. Drift monitors source freshness, country/customer mix, class prevalence, confidence calibration, model disagreement, retrieval misses, override rate, and coalition-policy denials.

## Full-Stack Implementation

```text
apps/resilience-web/                 # Signal inbox, graph, scenario and approval UI
services/resilience-api/             # FastAPI commands and read models
artemis/strategic_resilience.py      # Deterministic contract/scoring/state/audit core
foundry/pipelines/public_sources/    # Quarantine, normalize, deduplicate
foundry/ontology/resilience/         # Object/link/Action definitions
aip/workflows/resilience/            # Versioned agent graphs and eval suites
policy/resilience/                   # Rego/data-access/action policies
apollo/resilience/                   # Environments, rings, health and rollback
```

Representative API commands use an idempotency key and optimistic version:

```json
POST /v1/signals
{"source": {"url": "https://…", "supporting_passage": "…"}, "signal_type": "Tender", "lifecycle_stage": "PROCURED"}

POST /v1/opportunities/{id}/transitions
{"target": "IN_REVIEW", "expected_version": 3, "reason": "Evidence package complete"}
```

The handler authenticates workload and user, asks the policy decision point before retrieval, validates the Python contract, writes the command and outbox event in one transaction, and returns a correlation ID. Workers claim outbox rows idempotently. Retries are bounded with jitter; poison messages enter a dead-letter queue with an operator-visible alert.

```python
def prepare_assessment(command, principal, store, policy):
    policy.require(principal, "opportunity:draft", resource=command.signal_id)
    signal = store.get_signal(command.signal_id, as_of=command.as_of)
    assessment = ResilienceEngine().assess(signal, command.bear_case, **command.analysis)
    with store.transaction() as tx:
        tx.insert_assessment(assessment, expected_signal_version=command.signal_version)
        tx.append_outbox("assessment.created", assessment.opportunity_id)
    return assessment  # always DRAFT; the model cannot approve its output
```

The web console always shows Fact / Interpretation / Inference / Assumption / Unknown / Recommendation / Trigger / Validation as separate panels. Keyboard navigation, visible focus, WCAG AA contrast, reduced motion, source timestamps, stale-data banners, and a no-JavaScript evidence view are release gates.

## Security and Governance

- OIDC workload/user identity, mTLS service identity, short-lived audience-bound credentials, default-deny egress, and secrets from a runtime vault.
- Row, column, property and entity controls in Foundry/Gotham plus server-side policy checks adjacent to every Action. Browser filtering is never a security boundary.
- Coalition release requires originator-control, licence and releasability evaluation. Cross-boundary export creates a separately approved, redacted derivative with lineage.
- Public URLs are allowlisted, DNS/IP checked against SSRF, fetched through an egress proxy with timeouts and size limits, content-scanned, and stored as untrusted evidence.
- Append-only hash-chained decisions feed a separately administered immutable store. Logs include actor, purpose, source, model/prompt/policy versions, tool calls, approval and result—never secret values.
- Signed/SBOM-attested artifacts, pinned dependencies, isolated builds, protected Apollo environments, canaries, kill switch and last-known-good rollback.
- No classified data, covert collection, personal targeting, restricted military information, autonomous operational action, fabricated endorsement, or unsourced claim.

## Scenario Walkthrough

At 08:14 UTC, an allowlisted Arctic infrastructure authority publishes a remote-port monitoring tender. Ingestion stores the exact passage and retrieval time, detects the official primary source, and creates a `Tender/PROCURED` signal. The Arctic analyst links it to civilian port operators and monitoring capabilities; the NATO-policy agent labels national-security relevance separately rather than inferring military intent.

The opportunity architect drafts a vendor-neutral monitoring pilot. The bear-case challenger assigns each of nine dependencies a 0–5 exposure, then shows that a single satellite provider and public buyer make the first design too concentrated. The agent proposes a terrestrial fallback, portable telemetry interface, two clouds plus an edge-only mode, and civilian utility/energy reuse. These are analyst inferences and assumptions—not verified demand.

The revenue validator requests proof of eligibility, buyer interviews, delivery mechanism, and an identified budget line. An executive sees every evidence passage and rejects the first package because maintenance support was absent. The rejection is appended, not overwritten. The agent revises the experiment; an authorized reviewer approves only a bounded discovery sprint, not a bid or purchase.

After validation, operators mark which pain hypotheses were confirmed. The improvement agent turns the missed-maintenance correction into an eval case and proposes a prompt change. Offline evaluation improves requirement recall without reducing citation precision; a reviewer approves a 5% Apollo canary. Drift and policy dashboards remain within gates for the observation window, so the release is promoted. If provenance coverage or override rate degrades, Apollo rolls back to the pinned prior package. The system learned a reusable reasoning check, but never changed its mission, permissions, or approval boundary.

## Rollout and Recovery

Milestone 1 runs the Python reference core and synthetic/public fixtures locally. Milestone 2 connects one read-only official source and Foundry development ontology. Milestone 3 enables draft-only AIP analysis. Milestone 4 adds reviewer approvals and a non-production Apollo canary. Production requires documented Palantir provisioning, data/source licences, threat and privacy review, operational owner, SLO evidence, backup restoration test, and rollback drill. Recovery disables collectors and agent tools, preserves the audit plane, restores the last-known-good signed package, replays the idempotent outbox, and revalidates ontology counts and hashes before reopening.

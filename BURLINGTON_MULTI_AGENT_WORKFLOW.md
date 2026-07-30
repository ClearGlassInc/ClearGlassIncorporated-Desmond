# ClearGlassInc Artemis — Burlington Multi-Agent Workflow

> **Control posture:** agents propose; policy and named humans authorize; dedicated executors act. No agent can expand tools, scope, credentials, mission or deployment targets. Production, personal-data and public-channel capabilities remain disabled until explicit approvals and environment evidence exist.

## Interfaces

Every message uses `{schema_version, event_id, correlation_id, mission_id, actor, purpose, occurred_at, source_refs, classification, consent_markings, payload, payload_digest}`. Consumers validate size/type, authorize purpose and entity scope, enforce idempotency, write a decision event and quarantine malformed data. Outputs are immutable versions; agents never share writable files.

| Agent | Inputs | Outputs | Cadence / SLO | Acceptance and authority |
|---|---|---|---|---|
| ReconEngine | authorized GBP, GA4, GSC, social, CRM, provider exports | baseline versions, anomalies, competitor observations, grid runs | daily incremental; weekly full | ≥95% expected days or waiver; read-only |
| StrategyArchitect | locked recon, objectives, experiments | scored lever proposal and rationale | monthly or drift trigger | reproducible formula; draft only |
| ContentGenerator | verified opportunities, rights-cleared evidence, approved voice | article/social/video drafts | 2–4 blogs and 15–25 social drafts/month | originality, evidence, accessibility; no publish |
| LocalSEOAuditor | repo/live read-only scan, canonical NAP | issues and safe patch proposals | weekly / critical alert | schema/NAP/CWV checks; PR only |
| ReviewAndCitationManager | eligible job flag, consent/suppression state, directory register | neutral request/correction drafts, alerts | event-driven / weekly audit | no sentiment gating; send/edit requires approval |
| CommunityPartnershipScout | verified public sources and fit criteria | weekly ranked shortlist and individual drafts | weekly | evidence URL fresh; no contact action |
| GrowthReporter | immutable aggregates from all agents | weekly summary/monthly report | weekly/monthly | no raw PII; definitions and release annotations |
| Evaluator | candidate/control traces and holdout cases | signed scorecard and rollback recommendation | every candidate | cannot approve or modify candidate |
| OpsOrchestrator | approved mission DAG, leases, budgets, policies | task states, audit events, escalations | continuous | bounded retries; no business decision authority |

## State machine and write isolation

`PROPOSED → VALIDATED → AWAITING_APPROVAL → APPROVED → EXECUTING → SUCCEEDED|FAILED|ROLLED_BACK`; `REJECTED`, `EXPIRED` and `QUARANTINED` are terminal. Only the approval service transitions to `APPROVED`; only the destination-specific executor transitions to `EXECUTING`; neither accepts a changed digest.

The orchestrator leases `{resource_type, resource_id, version}` before a write. A compare-and-swap on the expected version prevents overlapping destructive edits. Draft agents use separate branches/objects. Lease expiry never implies approval, and retryable execution uses the same idempotency key.

## Approval matrix

| Change | Required approval | Executor checks |
|---|---|---|
| Read aggregate / draft | mission owner preauthorization | purpose, compartment, budget |
| Website content publish | editor + site owner | artifact digest, evidence, accessibility, expiry |
| Site-wide schema/core structure | SEO + site + governance owner | staging results, backup, rollback, protected environment |
| GBP field/post | GBP owner; governance for identity/category | profile snapshot, exact field diff, guideline check |
| Review/outreach send | privacy/legal + channel owner | legal basis, suppression, frequency, identity, exact copy |
| Personal-data connector | privacy, security, data owner | minimization, DPIA where applicable, retention, kill switch |
| Prompt/workflow/model route | model-risk owner; security if tool surface changes | offline eval, signed bundle, canary, last known good |

No role approves its own proposal. Emergency disablement can reduce capability without campaign approval; re-enablement needs the normal gate.

## Scheduling and failure behavior

Daily ingestion uses bounded concurrency and per-source quotas. Weekly full refresh waits for source watermarks, then freezes a snapshot before downstream analysis. Monthly strategy reads only that snapshot. Network reads use capped retry with jitter; mutations do not retry unless the destination supports verified idempotency. Authorization, consent, lineage or audit failure is fail-closed. Partial results are labelled and cannot silently replace a complete baseline.

## Continuous verification

- Validate all JSON contracts and recompute lever scores on every change.
- Scan for secrets, unsupported claims, mutable evidence and raw personal data.
- Run eval holdouts on every prompt/workflow/model candidate; policy failures block.
- Compare grid settings digests before trend calculation.
- Reconcile approval and execution ledgers daily; alert on orphan or replayed actions.
- Exercise connector shutdown and last-known-good rollback quarterly in non-production, then in production only under approved procedure.

## Audit event minimum

Record UTC time, correlation/mission IDs, actor/workload identity, action, input/output digests, source references, policy/version decision, prompt/workflow/model versions, tool calls, approval actor/reason/expiry, destination, result, latency/cost, previous-event hash and rollback link. Sensitive values stay in protected source systems; the audit uses references and minimized metadata.

## Operator runbook

1. Confirm mission scope, owners, budgets, sources and stop conditions.
2. Start read-only ReconEngine; resolve quarantine and lock the snapshot.
3. Run strategy/content/audit agents against the snapshot in separate namespaces.
4. Evaluator checks every candidate; orchestrator routes exact packages to named approvers.
5. Approved executor revalidates immediately before acting. Monitor guardrails and audit completeness.
6. On breach, disable the adapter, preserve evidence, restore last known good, notify the owner and open post-incident evaluation.

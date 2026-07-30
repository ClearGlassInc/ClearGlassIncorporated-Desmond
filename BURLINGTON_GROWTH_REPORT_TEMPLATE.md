# ClearGlassInc Artemis — Burlington Growth Report Template

> **Reporting rule:** replace bracketed fields only with traceable observations. `N/A — not connected`, `not collected`, and `insufficient matched sample` are valid; do not convert missing data to zero. This template is not evidence of performance, active integrations, or Palantir provisioning.

## Report control

| Field | Value |
|---|---|
| Period / cadence | `[YYYY-MM-DD..YYYY-MM-DD]` / `[weekly|monthly]` |
| Generated / approved at | `[RFC3339]` / `[RFC3339 or pending]` |
| Mission / report version | `burlington-local-exposure` / `[version]` |
| Data cut-off / timezone | `[RFC3339]` / `America/Toronto` |
| Baseline snapshot digest | `[sha256]` |
| Current snapshot digest | `[sha256]` |
| Metric-definition version | `[digest/version]` |
| Sources and freshness | `[source: observed_at, status]` |
| Author / approver | `[workload or human ID]` / `[human ID or pending]` |
| Classification / releasability | `[marking]` / `[audience]` |
| Known gaps/method changes | `[explicit list]` |

## Executive evidence summary

**Status:** `[on track | watch | off track | not measurable]`

* Verified outcome: `[claim with metric, denominator, comparison, and evidence ID]`.
* Material change: `[what changed, when, approved action/package/release ID]`.
* Blocker/risk: `[precise limitation, impact, owner, due date]`.
* Decision required: `[decision, approver, deadline, safe default]`.
* Next best experiment: `[hypothesis and smallest falsifiable test]`.

## Objectives scorecard

| Objective | Definition | Baseline | Current | Delta | 90-day threshold | Confidence/status | Evidence |
|---|---|---:|---:|---:|---:|---|---|
| Geo-grid visibility | Share of matched cells at rank `≤ [green threshold]`, per priority keyword | `[n/N, %]` | `[n/N, %]` | `[pp/%]` | `+30–50% relative green-cell share` | `[CI/method/status]` | `[run IDs]` |
| Local organic sessions | Consented GA4 organic sessions with approved Burlington/Halton/Hamilton geo definition | `[N]` | `[N]` | `[%]` | `+40% in 90 days` | `[status]` | `[snapshot]` |
| Qualified local leads | Leads meeting versioned qualification and local-context rules, deduped, attributable | `[N/month]` | `[N/month]` | `[N/%]` | `≥10/month` | `[status]` | `[aggregate]` |
| Brand surface area | Branded query index plus verified unique local mentions (reported separately) | `[index; N]` | `[index; N]` | `[%/N]` | `[approved threshold]` | `[status]` | `[evidence IDs]` |

Do not sum unlike brand signals. Geography is an analytics estimate, not a precise-person claim. Suppress small cohorts under the approved privacy threshold.

## Channel detail

### Google Business Profile

| Metric | Current | Prior matched period | Change | Completeness/evidence |
|---|---:|---:|---:|---|
| Impressions / profile views | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| Calls / direction requests / website clicks | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| Top queries | `[query: value; …]` | `[ ]` | `[ ]` | `[minimum-volume/privacy notes]` |
| Posts/photos/reviews observed | `[ ]` | `[ ]` | `[ ]` | `[observation only]` |

### Web and conversion

| Metric | Current | Prior | Change | Evidence/notes |
|---|---:|---:|---:|---|
| Local organic sessions / engaged sessions | `[ ]` | `[ ]` | `[ ]` | `[GA4 definition]` |
| Top local landing pages | `[path: sessions/conversions]` | `[ ]` | `[ ]` | `[ ]` |
| Local CTA / lead submits | `[ ]` | `[ ]` | `[ ]` | `[event contract version]` |
| Qualified attributable leads | `[ ]` | `[ ]` | `[ ]` | `[dedupe/qualification/source]` |
| Conversion rate | `[qualified leads / eligible sessions]` | `[ ]` | `[pp]` | `[denominator]` |

### Social and local surface area

| Channel | Followers change | Engagement rate and formula | Local signal | Top asset/evidence |
|---|---:|---:|---|---|
| Instagram | `[ ]` | `[interactions / eligible reach]` | `[coarse aggregate]` | `[asset ID]` |
| TikTok | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| LinkedIn | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| Local mentions/partners | `N/A` | `verified unique mentions: [N]` | `[Burlington/Oakville/etc.]` | `[URLs/archive digests]` |

## Geo-grid evidence

| Keyword | Matched cells | Green prior | Green current | Delta (pp) | Median rank delta | Red clusters | Run IDs |
|---|---:|---:|---:|---:|---:|---|---|
| `[keyword]` | `[N]` | `[n/N, %]` | `[n/N, %]` | `[ ]` | `[ ]` | `[neighbourhood/coarsened cell]` | `[ ]` |

**Method:** vendor/API `[name/version]`; fixed grid digest `[ ]`; green threshold `[ ]`; device/locale `[ ]`; collection windows `[ ]`; missing/failed cells `[N by reason]`; source/method changes `[ ]`. Compare only matched cells unless a documented sensitivity analysis says otherwise.

Example visualization using actual populated values only:

```text
Keyword             Prior     Current   Change
[keyword A]         [██░░░]   [███░░]   [+__ pp]
[keyword B]         [N/A]     [N/A]     [insufficient data]
```

## Experiments and actions

| Experiment/action ID | Hypothesis or approved effect | Segment / dates | Baseline & stop rules | Result | Decision | Approval / rollback |
|---|---|---|---|---|---|---|
| `[ID]` | `[falsifiable statement]` | `[ ]` | `[metric, minimum N/time, harm/cost stop]` | `[estimate + uncertainty]` | `[continue/stop/iterate/inconclusive]` | `[package/release IDs]` |

### What worked / did not / remains unknown

* **Worked:** `[evidence-backed result; avoid causal language unless design supports it]`.
* **Did not:** `[negative or neutral result and cost]`.
* **Unknown:** `[missing data/confounder/sample issue and plan]`.

## Agent, quality, and governance health

| Signal | Value | Threshold | Status / response |
|---|---:|---:|---|
| Source freshness / schema reject rate | `[ ]` | `[versioned]` | `[ ]` |
| Citation coverage / unsupported-claim rate | `[ ]` | `[ ]` | `[ ]` |
| Draft acceptance / operator override rate | `[ ]` | `[ ]` | `[ ]` |
| Precision / recall on frozen eval | `[ ]` | `[ ]` | `[ ]` |
| p95 latency / cost per accepted draft | `[ ]` | `[ ]` | `[ ]` |
| Policy violations / boundary leaks | `[0 required]` | `0` | `[stop immediately if nonzero]` |
| Pending/expired approvals / reconciliation | `[ ]` | `[ ]` | `[owner/action]` |
| Drift status / champion version | `[ ]` | `[ ]` | `[candidate/rollback disposition]` |

## Compliance, privacy, and risk register

| Risk/invariant | Evidence | Severity | Owner | Mitigation / safe state | Due/status |
|---|---|---|---|---|---|
| `[CASL consent/suppression, review gating, provider terms, privacy, schema/SEO, brand, access, drift]` | `[ ]` | `[ ]` | `[ ]` | `[disable/draft-only/rollback]` | `[ ]` |

Confirm: no fake or selectively solicited reviews; no invented claims/locations/endorsements; no mass outreach/link schemes; no production/personal-data/public campaign change without the required approval. Record only the result of checks actually performed.

## Next-period plan and decisions

| Priority | Lever / task | Measurable acceptance | Owner | Dependency | Approval gate | Verification / rollback |
|---:|---|---|---|---|---|---|
| `1` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` |

### Required human decisions

1. `[Decision, accountable approver, evidence packet, deadline, default if no decision]`.

### Data and resource blockers

1. `[Missing connector/export/access/definition; never imply it exists]`.

## Audit appendix

* Input/output digests: `[ ]`
* Query/data product/ontology versions: `[ ]`
* Prompt/model/workflow/tool/policy versions: `[ ]`
* Agent run IDs and action packages: `[ ]`
* Approval/rejection IDs and reason codes: `[ ]`
* Release/canary/rollback identifiers: `[ ]`
* Report generation logs and formula checks: `[ ]`
* Retention/classification/releasability review: `[ ]`

## Sign-off

| Role | Identity | Decision | Timestamp | Scope/notes |
|---|---|---|---|---|
| Growth owner | `[ ]` | `[approve/reject/pending]` | `[ ]` | `[ ]` |
| Data owner | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| Privacy/security (when applicable) | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| Deployment/rollback owner (when applicable) | `[ ]` | `[ ]` | `[ ]` | `[ ]` |

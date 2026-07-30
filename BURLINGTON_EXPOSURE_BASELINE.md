# ClearGlassInc Artemis — Burlington Exposure Baseline

> **Evidence state:** baseline contract created; no authorized GBP, analytics, CRM, social, competitor, or rank-provider export was supplied. Every unavailable measurement is `null`, never zero. This document is not evidence of current rankings, traffic, partnerships, Palantir provisioning, or production deployment.

## Decision summary

The first operational decision is **measurement authorization**, not optimization. Lock a 90-day baseline, the business identity/NAP source of truth, the service-area facts, 3–7 keywords, a fixed geo-grid, conversion definitions, consent basis, and accountable owners. Until that gate passes, `priority_levers.json` is provisional and public/mutating automation remains disabled.

## Baseline inventory

| Domain | Artifact | Current state | Exit criterion |
|---|---|---|---|
| Mission | `MISSION_OBJECTIVES.json` | Targets defined | Owners approve definitions and baseline date |
| GBP/web/social/leads | `baseline_metrics.json` | Awaiting authorized exports | Required values populated, lineage recorded, anomalies reviewed |
| Competitors | `competitor_intel.json` | Empty by design | 3–5 evidenced competitors per keyword |
| Opportunities | `local_opportunity_map.json` | Research shortlist | URLs, eligibility, dates and fit reverified |
| Geo-grid | `geo_grid_baseline.json` | Awaiting provider | Comparable successful run with fixed settings |

## Collection runbook

1. A data owner approves the purpose, minimum fields, retention, geography, credentials, and operators. Keep credentials in a runtime secret manager.
2. Export the trailing 90 complete days from GBP performance, GA4, Search Console, CRM and channel-native analytics. Preserve raw exports in access-controlled storage; commit only aggregates.
3. Record source, property/account identifier alias, query parameters, timezone, extraction timestamp, row count and checksum in the audit plane.
4. Normalize into `baseline_metrics.json`; use `null` for unavailable/thresholded values. Flag source discrepancies above 10%, missing days, tracking changes and consent-mode changes.
5. Run the rank provider from a fixed Burlington grid with the same keyword, locale, device, radius, spacing and provider settings. Failed queries are failures, not poor ranks.
6. Discover competitors from that exact run. Record observation time and evidence; do not infer GBP fields or scrape Google contrary to its terms.
7. Freeze the baseline digest. Any corrected baseline creates a new version and records why; it never overwrites the prior audit object.

## Initial diagnostic hypotheses—not findings

- A single, genuinely useful `/burlington` page may concentrate local service evidence better than generic site copy; verified coverage and unique proof are prerequisites.
- Accurate GBP categories, services, hours, photos and links may close completeness gaps; the profile owner must approve evidence-backed edits.
- Consistent, sentiment-neutral review requests may improve trust, but require CASL/privacy review, suppression, consent evidence and no incentives or review gating.
- Neighbourhood-level content should be driven by measured red zones and real expertise, not mass-generated doorway pages.

## Data-quality gates

A baseline is releasable only if dates and timezone are fixed, definitions match `MISSION_OBJECTIVES.json`, at least 95% of expected source-days are present or waived, CRM tests/spam are excluded, geography is aggregate, UTM/source coverage is measured, rank-grid success rate is at least 95%, and a second operator reproduces summary totals. Store no raw IP address, message body, phone number or email address in repository artifacts.

## Immediate next actions

| Order | Owner | Action | Verification |
|---:|---|---|---|
| 1 | Executive sponsor | Name data, GBP, marketing, privacy and site owners | Signed responsibility record |
| 2 | Data/privacy owner | Approve source access, minimization and retention | Data-access decision logged |
| 3 | Analyst | Populate baseline using authorized exports | `python tools/burlington_exposure.py validate` |
| 4 | SEO owner | Approve fixed grid and keyword set | Baseline digest recorded |
| 5 | Strategy owner | Rescore levers from observed gaps | Score calculation reproduced |

Rollback is deletion/revocation of connector credentials, disabling scheduled ingestion, and restoration of the last approved immutable baseline version. Raw-source deletion follows the approved retention policy rather than a Git operation.

# ClearGlassInc Artemis — Burlington Exposure Baseline

> **Baseline status: incomplete / external data not collected.** Generated 2026-07-30. This document does not claim current rankings, traffic, profile activity, competitor performance, social performance, leads, partnerships, or event availability. A JSON `null` means unknown, never zero.

## Executive finding

The repository establishes a canonical domain (`www.clearglassinc.com`) and its checked-in homepage includes Burlington locality and `Organization`, `ProfessionalService`, and `WebSite` structured data. These are **repository observations only**, not proof that the live page is indexed, that Google accepts its markup, that the stated service area is operationally verified, or that a Google Business Profile exists.

No authenticated GBP, GA4, Search Console, CRM, social, citation, competitor, or geo-grid exports were available. Consequently, a quantitative 90-day baseline cannot yet be calculated. The first operational milestone is connector authorization and a reproducible snapshot—not optimization claims.

## Evidence inventory

| Area | State | Evidence available | Blocking requirement |
|---|---|---|---|
| Canonical web domain | Repository-observed | `CNAME:1` | Resolve live URL and record HTTP/indexing checks |
| Homepage local/entity markup | Repository-observed | `index.html:246` | Verify business facts, validate rendered JSON-LD, inspect Search Console |
| GBP performance | Not collected | None | Authorized API access or dated export |
| Web/search performance | Not collected | None | GA4 and Search Console read-only access or dated exports |
| Lead outcomes | Not collected | None | Consent-aware CRM aggregate and local-lead definition |
| Social performance | Not collected | None | Read-only platform analytics or dated exports |
| Competitors | Not collected | None | Terms-compliant, time-and-location-stamped observation |
| Geo-grid | Not collected | None | Approved provider, grid, keyword set, budget, and collection method |

## Machine-readable artifacts

- `baseline_metrics.json` is the normalized 90-day measurement contract. All unavailable measures are `null` and all unavailable lists are empty.
- `competitor_intel.json` defines keyword coverage and the evidence contract for future competitor records; it identifies no competitors without observations.
- `local_opportunity_map.json` separates user-supplied candidates from verified opportunities and records the validation required before use.
- `geo_grid_baseline.json` defines rank semantics and a pending grid contract; it contains no fabricated cells.

## Initial diagnostic (bounded to repository evidence)

### Confirmed

1. The checked-in `CNAME` names `www.clearglassinc.com`.
2. The checked-in homepage describes AI automation, cybersecurity, software architecture, OSINT, and enterprise workflow services.
3. The checked-in homepage JSON-LD states Burlington, Ontario and includes organization/service entities.

### Unknown and not safe to infer

- GBP ownership, verification, category, services, hours, photos, posts, Q&A, reviews, actions, queries, or guideline compliance.
- Organic visibility, local sessions, conversions, branded demand, or source attribution.
- The top three to five local competitors for any keyword.
- Current event dates, directory eligibility, publication contacts, partnership availability, or backlink opportunity.
- Map/local-pack rank at any coordinate.
- Whether Oakville, Hamilton, Milton, or Dundas are verified operational service areas.

## Reproducible collection plan

1. **Approve scope:** owner signs off on 3–7 exact keywords, verified service areas, local-lead definition, grid resolution, green threshold, provider, cost ceiling, retention, and responsible operators.
2. **Create read-only connectors:** use least-privilege identities for GBP, GA4, Search Console, CRM aggregates, and platform analytics. Keep credentials in runtime secrets and personal data out of artifacts.
3. **Freeze the baseline window:** capture a single 90-day interval with explicit UTC start/end, source export IDs, collection timestamps, account/property identifiers (non-secret), and checksums.
4. **Validate:** reject duplicate rows, impossible negative counts, mismatched time zones, unrecognized dimensions, missing attribution fields, and partial connector responses. Record unknowns as `null`.
5. **Collect geo-grid evidence:** use a terms-compliant provider at approved, stable points. Record provider, device/language settings, observation time, maximum checked rank, and raw-run digest. Do not scrape or manipulate Google.
6. **Verify candidates:** identify competitors from repeated observations, then record profile/site/social/citation fields only with dated evidence. Validate opportunity records from official sources before outreach.
7. **Lock and compare:** checksum the accepted snapshot, retain it read-only, and compare day 30/60/90 runs using the identical definitions. Any methodology change creates a new series.

## Acceptance gates for baseline completion

- All required sources have either a successful timestamped snapshot or an explicit approved exclusion.
- The 90-day window and time zone are consistent across sources or differences are documented.
- Every aggregate has lineage; no secret or unnecessary personal data appears in artifacts.
- Competitor facts include observation time and evidence references.
- Every rank cell contains keyword, point, position/not-found status, collection settings, and source-run reference.
- Reconciliation checks pass and a named owner approves the immutable baseline digest.

## Immediate next actions

| Priority | Action | Owner needed | Exit evidence |
|---:|---|---|---|
| 1 | Verify canonical NAP, services, public address/service-area model, and secondary-market coverage | Business owner | Signed source-of-truth record |
| 2 | Authorize read-only GBP, GA4, Search Console, CRM, and social exports | Data owners | Successful connector timestamps/export digests |
| 3 | Approve keyword/grid measurement contract and compliant provider | Local SEO + privacy/governance | Signed measurement specification |
| 4 | Execute baseline collection and schema validation | ReconEngine operator | Complete JSON, validation log, snapshot digest |
| 5 | Review competitor and opportunity evidence before any public action | Marketing owner | Approved evidence-backed shortlist |

## Risk and authorization boundary

Collection is read-only. No agent may edit GBP, publish a page or social post, contact a customer or partner, request a review, purchase a citation, or deploy schema from this baseline. Those actions require an exact draft/action package, evidence and policy checks, named human approval, auditable execution, and a rollback or disposition plan. Review gating, fabricated reviews, deceptive location pages, unverified claims, mass outreach, and link schemes are prohibited.

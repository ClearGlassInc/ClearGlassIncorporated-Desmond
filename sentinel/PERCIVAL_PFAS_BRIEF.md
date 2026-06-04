# PERCIVAL · PFAS — Compliance & Decision Intelligence (Ontario)

> Defensive PFAS intelligence agent inside the **PERCIVAL** control plane.
> Source-of-truth charter for the Phase-One product narrowly described in the
> operator brief. Executable companion: `sentinel/sentinel/pfas.py` +
> `sentinel/tests/test_pfas.py`.

## Mission
Build and operate a serious PFAS business in Burlington focused on **PFAS
screening, compliance analytics, source tracing, and treatment operations
support** for municipalities, property owners, industrial sites, and consultants.

## Commercial anchor
Health Canada's interim drinking-water objective tightened to **30 ng/L for
the sum of 25 PFAS**. The 25-analyte list is implemented in `pfas.HC_25_PFAS`
and the threshold in `pfas.HC_25_PFAS_NGL`.

## Best business model
A **PFAS intelligence + compliance platform** with service wrappers — software
first, services second:
- ingest lab results → normalize analytes → classify against guideline
  thresholds → map likely source categories → generate client-ready reports
- premium human-reviewed consulting and sampling coordination as wrappers

## What we sell (Phase One)
1. PFAS screening coordination
2. Compliance reporting (HC interim objective + Ontario MECP)
3. Source-risk mapping
4. Treatment decision support (GAC / IEX / RO comparison briefs)

Packaged as monthly monitoring, incident response, and capital-planning support.

## Why Burlington
The Burlington/Ontario corridor sits near industrial, transportation, and
municipal infrastructure where water risk, source tracing, and documentation
matter. The local angle is to be the operating system that helps regulated
organizations manage PFAS risk continuously.

## Automation-first system (Phase-One workflow — what `pfas.py` implements)
```
upload report → detect PFAS → score risk → generate compliance package
              → recommend next action
```
- **Inputs:** `Sample` with `AnalyteResult[]` (ng/L, LOQ-aware), `ScreeningRequest`
  with mandatory `client_id / site_owner_ref / jurisdiction / purpose /
  requester_role` (fail-closed if any missing).
- **Scoring:**
  - `LOW` — sum-of-25 (upper bound) < 0.5 × HC objective (15 ng/L)
  - `ELEVATED` — 15 ≤ sum < 30 ng/L → monthly monitoring + pre-design study
  - `EXCEEDANCE` — sum ≥ 30 ng/L → compliance ticket, source characterization,
    treatment evaluation, 7-day resample
- **LOQ handling:** operator-conservative — values <LOQ count toward the
  *upper-bound* sum (not the lower); both bounds reported.
- **Source hints:** matrix + analyte mix → bucketed categories (AFFF, coatings,
  landfill, wastewater…) — informational, never accusatory.
- **Treatment options:** GAC, ion exchange, RO, interim source isolation.
- **Output:** `CompliancePackage` with `audit_ref`, `next_actions`,
  `resample_after_days`, references.

## Revenue architecture
- Subscription software (monitoring + reporting)
- Paid expert review for high-risk cases
- Project-based source tracing + remediation planning
- Referral / implementation revenue from treatment vendors

## What we do NOT overbuild
No national database, no in-house lab. The product is the narrow workflow above
and the compliance package it produces.

## Positioning
A **PFAS compliance and decision intelligence platform** for Ontario — faster
reporting, better risk visibility, less manual work, clearer next steps for
water, property, and infrastructure stakeholders.

## What PERCIVAL PFAS does **not** do
- Does not identify private individuals or link PFAS findings to people
- Does not run offensive or covert collection
- Does not bypass the SENTINEL fail-closed gate or charter

## References
- Health Canada — *Objective for Canadian drinking water: per- and polyfluoroalkyl
  substances (PFAS)* — interim objective 30 ng/L (sum of 25 PFAS).
- Ontario MECP — *Drinking Water Quality Standards* (PFAS where applicable).

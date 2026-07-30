# ClearGlassInc Artemis — Burlington Growth Report — YYYY-MM

> **Reporting state:** template. Replace examples/placeholders only with reproducible observations. `N/A` means unavailable; zero is a measured zero. Do not include raw personal data.

## Executive decision brief

- **Window / comparison:** `[start–end, America/Toronto]` vs `[locked baseline window]`
- **Data snapshot / code / policy:** `[digests and versions]`
- **Overall state:** `[on track | at risk | blocked | insufficient evidence]`
- **Decision required:** `[owner, decision, due date]`
- **Stop conditions:** `[none or exact condition and action]`

## Objective scorecard

| Objective | Baseline | Current | Target | Confidence / quality | Status |
|---|---:|---:|---:|---|---|
| Green-cell rate for ≥3 priority keywords | `[x%]` | `[x%]` | `+30%; stretch +50%` | `[provider success, fixed grid]` | `[ ]` |
| Consented local organic sessions | `[x]` | `[x]` | `+40%` | `[thresholding/coverage]` | `[ ]` |
| Qualified local leads/month | `[x]` | `[x]` | `≥10` | `[≥90% attribution]` | `[ ]` |
| Verified earned local mentions | `[x]` | `[x]` | `≥2/90d` | `[evidence URLs]` | `[ ]` |

## Weekly channel evidence

### Google Business Profile

| Metric | Prior | Current | Change | Annotation |
|---|---:|---:|---:|---|
| Impressions/profile views | `[ ]` | `[ ]` | `[ ]` | `[release/source note]` |
| Calls/directions/site clicks | `[ ]` | `[ ]` | `[ ]` | `[ ]` |
| Top query mix | `[ ]` | `[ ]` | `[ ]` | `[no individual query claims if thresholded]` |

### Web and leads

Report local organic sessions, landing pages, CTA events, qualified forms/calls, qualification rate, attribution coverage and consent/tracking changes. Separate observed association from causal claim.

### Social and brand surface

Report local audience/engagement where channel data supports it, saves/shares, assisted conversions, verified mentions and branded-query trend. Do not infer audience location from individual profiles.

## Geo-grid

```text
Keyword                       Green / measured     Rate      Δ vs locked baseline
[software architect...]       [00 / 00]             [--%]     [-- pp]
```

Include provider/run IDs, timestamp, locale/device, grid/settings digest, successful/failed cells and map legend. A simple accessible table is mandatory even when a visual heatmap is included. Failed cells are errors, not red ranks.

## Experiments

| ID | Hypothesis | Control/candidate | Primary metric | Window/sample | Guardrails | Result / decision |
|---|---|---|---|---|---|---|
| `[ ]` | `[ ]` | `[version digests]` | `[ ]` | `[ ]` | `[ ]` | `[continue/stop/promote/rollback]` |

For each result attach the preregistered plan, data snapshot, analysis method and limitations. Do not call directional movement a win before the success threshold and minimum window.

## What worked / did not / remains unknown

- **Supported:** `[claim + evidence reference]`
- **Not supported:** `[experiment + evidence]`
- **Unknown:** `[missing signal and collection decision]`

## Changes and audit

| Time | Change | Risk | Approval digest | Release | Before/after evidence | Rollback |
|---|---|---:|---|---|---|---|
| `[UTC]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `[last-known-good]` |

## Risks, blockers and next actions

| Priority | Risk/blocker | Owner | Due | Mitigation / stop rule |
|---:|---|---|---|---|
| 1 | `[ ]` | `[ ]` | `[ ]` | `[ ]` |

## Verification attestation

- [ ] Source windows, timezone, row counts and checksums recorded.
- [ ] Objective definitions match `MISSION_OBJECTIVES.json`.
- [ ] Grid/provider settings match the locked baseline.
- [ ] Null/thresholded/error values are not represented as zero.
- [ ] No raw PII, fabricated claim, review, partnership or affiliation appears.
- [ ] Reviewer reproduced totals and linked approvals/releases/rollbacks.

# ClearGlassInc Artemis — Burlington Local SEO Plan

**Status:** evidence-gated 90-day operating plan; not proof of deployment or performance.
**Primary market:** Burlington, Ontario. **Secondary test markets:** Oakville, Hamilton, Milton, and Dundas.

## 1. Outcome, invariants, and measurement

The objective is to improve qualified local discovery, not manufacture proximity or reputation. KPI contracts and thresholds live in `MISSION_OBJECTIVES.json`. Before work begins, the GrowthReporter must freeze a dated 90-day baseline and a comparison protocol. “Green” means rank 1–3 only; blocked, missing, or provider-error cells are `unavailable`, never failures or successes.

**Non-negotiable invariants**

- Use only the real business name, address/service area, hours, categories, services, qualifications, clients, testimonials, and images verified by the business owner.
- Never create virtual locations, doorway pages, fake engagement, review gating, sentiment-based solicitation, or reciprocal/paid links disguised as editorial links.
- Automation produces **drafts**. A named human approves every GBP mutation, public post, outreach send, schema/site deployment, review campaign, and personal-data integration.
- Record `actor`, UTC timestamp, source evidence, before/after representation, rationale, approval ID, result, and rollback for each material action.

## 2. Foundation (days 1–14)

### Evidence and GBP

1. Analytics/privacy owner validates consent, retention, city-level reporting thresholds, conversion definitions, referral exclusions, and UTM capture.
2. ReconEngine records a fixed geo-grid: points, coordinates/labels, keyword, language, device, provider, radius, collection time, and error state. Use an approved rank provider; do not scrape Google or simulate user traffic.
3. Business owner exports GBP and verifies canonical NAP, genuine service area, opening hours, appointment URL, primary/secondary categories, service descriptions, and landing URL.
4. StrategyArchitect creates a field-level GBP change set. Publish only after owner approval; preserve a rollback snapshot. Establish a sustainable draft cadence of up to two useful GBP posts weekly, reduced if quality or evidence is unavailable.
5. Add real, rights-cleared photos only. Q&A answers must address genuine questions; never seed fabricated consumer questions or keyword-stuffed answers.

### Website hub

Create `/burlington` first, only if the business genuinely serves Burlington. It must contain unique service scope, verified local proof, delivery model, relevant FAQ, contact path, and a truthful statement about office versus service area. It must not imply a storefront or local clients that do not exist.

Release gate: unique-content review; canonical URL; localized title/H1 without stuffing; crawl/index directives; accessible landmarks/headings/forms; valid `Organization` and the correct business subtype (use `LocalBusiness` only if applicable); consistent NAP; privacy-safe map; internal links; sitemap; 404/canonical checks; Core Web Vitals budget; CTA events; and rollback commit. Secondary pages are authorized only when query/lead evidence supports distinct content.

### Reviews and citations

- Send the same neutral request path to all eligible, genuinely completed engagements—never only promoters. Do not reward positive sentiment. Legal/privacy must approve CASL basis, channel, identity, unsubscribe/suppression, retention, vendor processing, frequency, and evidence.
- Establish one canonical NAP record. Audit GBP, Bing Places, Apple Business Connect, relevant chamber/association profiles, and high-quality industry profiles. Correct inaccuracies account-by-account; avoid bulk directory blasts.

## 3. Momentum (days 15–45)

| Workstream | Action | Owner | Verification |
|---|---|---|---|
| Content | Publish two evidence-backed local articles mapped to distinct intents | Editor | Index status, engagement, CTA conversions after 30 days |
| Social | Run the approved calendar at 3–5 quality posts/week, Instagram first | ContentGenerator + human publisher | UTM sessions, saves, shares, qualified replies; not vanity reach alone |
| GBP | Draft useful updates from approved articles/case evidence | GBP owner | Post URL, date, actions; policy check |
| Partnerships | Research five organizations and make value-first, one-to-one approaches | Scout + partnership owner | Recipient basis, approval, response, outcome |
| Grid | Repeat identical grid at day 30 | ReconEngine | Comparable-cell coverage and cell transition matrix |

At day 30, continue a tactic only if its evidence is interpretable. Diagnose red zones; do not fabricate neighbourhood pages. Prefer a useful Burlington-wide asset, a real local event contribution, or stronger service proof.

## 4. Scale and refine (days 46–90)

- Expand a secondary-city page only where Search Console/analytics, qualified demand, and unique proof support it. Each page receives an independent editorial and schema gate.
- Repeat geo-grid runs on the same protocol at days 60 and 90. Report absolute green-cell rate, relative change, median rank, valid-cell coverage, and confidence caveats by term.
- Promote only formats with meaningful local actions. Stop or revise content after two evaluation windows with no qualified signal, unless it serves a documented user need.
- Seek one or two **earned** local contributions (workshop, expert commentary, jointly useful guide). Disclose sponsorships and never require followed links.

## 5. Content architecture and internal links

Pillars: (1) practical AI automation for Halton organizations, (2) secure software architecture and cybersecurity, (3) responsible AI/governance, (4) locally useful workshops and case evidence. Each article links naturally to one service page and the Burlington hub when relevant. The hub links to verified services, contact/privacy pages, and genuinely related articles. Repository-generated internal-link blocks must be changed only through `tools/internal_links.py`.

## 6. Experiments and decision rules

| Experiment | Hypothesis | Primary metric | Guardrail | Decision |
|---|---|---|---|---|
| Burlington hub | A proof-rich hub earns qualified local discovery | Local organic conversions | No false location; CWV/accessibility stable | Keep if indexed and contributes a qualified action within 60 days; otherwise revise intent/proof |
| Two content topics | Practical local answers attract relevant visitors | Engaged local organic sessions and leads | Source/claim review | Scale winning intent only after a comparable 30-day window |
| Neutral review request | A compliant request improves response coverage | Request-to-review rate | Complaint, unsubscribe, platform warning | Pause immediately on consent/control failure |
| Partner workshop | Useful education generates earned mentions/leads | Verified mention and qualified referrals | No quid-pro-quo link | Repeat only with partner and audience evidence |

## 7. Reporting, approvals, and rollback

Weekly: data freshness/quality, GBP actions, local organic sessions/conversions, content outcomes, review workflow controls, grid only when scheduled, experiments, incidents, and approvals. Monthly: target trajectory, comparable cohorts, winning/losing hypotheses, resource decisions, and residual risks. No causal claim without a controlled or clearly qualified analysis.

Rollback means reverting the repository commit or restoring captured GBP/profile fields; pausing messaging and applying suppression; removing erroneous schema; and annotating measurement breaks. GBP warning, privacy/consent fault, material NAP error, deceptive claim, or unexplained data discontinuity triggers an immediate pause and owner review.

## 8. Immediate next actions

1. Assign business, analytics/privacy, GBP, editorial, and production owners.
2. Validate recon JSON and replace every `not_connected`/unknown value with sourced data or an explicit unavailable reason.
3. Approve canonical NAP and core keyword set (limit initial tracking to four; add terms only by change request).
4. Rescore `priority_levers.json`; approve the first reversible experiment.

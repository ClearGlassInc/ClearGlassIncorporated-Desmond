# ClearGlass SEO Assessment — 2026-08-21

## Executive diagnosis

ClearGlass's SEO constraint is primarily a **translation and information-architecture problem**, not simply a keyword problem. Distinctive product vocabulary should remain as brand language while every commercial page states, in plain language, what ClearGlass does, who it serves, and the operational problem addressed.

Recommended positioning:

> ClearGlass Inc. designs governed AI automation, cybersecurity, and intelligence systems for organizations that need faster execution with human approval, evidence, and operational control.

This repository does not claim NSA certification, DARPA certification, government accreditation, or equivalence. High-assurance/defense-in-depth refers to engineering discipline.

## Evidence boundary

The connected Search Console integration currently returns **Access denied** for both the URL-prefix property and `sc-domain:clearglassinc.com`. Therefore query, page, click, impression, CTR, average-position, and indexing metrics are **UNVERIFIED** until property access is restored and data is retrieved.

Public-site observations must remain distinct from Search Console measurements. No traffic or ranking value is inferred from access denial.

## Canonical commercial architecture

- `/services/ai-automation-services.html` — governed AI automation
- `/services/cybersecurity-consulting.html` — cybersecurity risk visibility, automation, and control
- `/services/osint-automation.html` — evidence-based public-source intelligence workflows
- `/services/ai-governance.html` — AI governance and agent controls
- `/methodology/seo-evidence.html` — evidence and claim methodology

## Search ownership

| Intent | Canonical destination |
|---|---|
| ClearGlass Inc | `/` |
| AI automation | `/services/ai-automation-services.html` |
| Cybersecurity | `/services/cybersecurity-consulting.html` |
| OSINT automation | `/services/osint-automation.html` |
| AI governance | `/services/ai-governance.html` |
| Methodology | `/methodology/seo-evidence.html` |

Do not create thin pages for every brand-query variation. Consolidate important intent around strong canonical destinations.

## Technical controls implemented

- Dedicated canonical service routes.
- Unique titles and descriptions.
- Canonical URLs on every new commercial page.
- Organization, Service, and BreadcrumbList structured data where applicable.
- Evidence-status disclosure on commercial pages.
- Dedicated `sitemap-services.xml`.
- `robots.txt` reference to the dedicated service sitemap.
- Deterministic repository validator at `scripts/validate_seo_governance.py`.
- CI validation at `.github/workflows/seo-governance.yml` with immutable action pinning.
- Machine-readable policy at `config/seo/seo-governance.json`.

## Claim controls

The SEO policy classifies evidence as `VERIFIED_FACT`, `OBSERVATION`, `DERIVED_METRIC`, `INFERENCE`, `UNVERIFIED`, or `UNKNOWN`.

The publication gate blocks unsupported certification language such as NSA-certified, DARPA-certified, or government-certified. Customer outcomes, production deployments, security certifications, and third-party validation require separate evidence.

## Next measurement actions

1. Restore Search Console property owner/full access.
2. Pull the last 16 months of query/page data.
3. Segment branded, non-branded, product, service, local, and informational queries.
4. Identify high-impression/low-CTR opportunities.
5. Identify positions 4–20 for optimization.
6. Detect keyword cannibalization and competing canonical pages.
7. Validate sitemap submission and inspect high-value URLs.
8. Connect SEO events to assessment/briefing pipeline outcomes.

## Commercial measurement events

`cta_click`, `assessment_start`, `assessment_submit`, `briefing_request_start`, `briefing_request_submit`, `contact_form_start`, `contact_form_submit`, `asset_download`, `calendar_booking`, `security_inquiry`, `platform_briefing_request`.

## 90-day priority sequence

### Critical

- Restore Search Console access.
- Verify sitemap, robots, canonicals, redirects, response codes, and indexability.
- Document whether each named platform is live, beta, demonstration, research, or roadmap.
- Publish the four canonical commercial service pages.
- Publish the evidence/methodology page.

### High

- Add verified Organization/Person/Service/Product/Breadcrumb schema where factually supported.
- Build internal links from the homepage to service and platform hubs.
- Add conversion tracking.
- Publish a flagship AI-governance guide.

### Medium

- Add comparison pages for validated buyer intent.
- Publish original research and assessment tools.
- Build legitimate media, conference, podcast, and expert-commentary relationships.
- Add Ontario/Toronto/Burlington pages only where ClearGlass actively serves those markets.

## Non-negotiable quality rule

SEO optimization must never manufacture evidence. Search demand can determine information architecture; it cannot determine whether a security, compliance, performance, customer, certification, or government-affiliation claim is true.

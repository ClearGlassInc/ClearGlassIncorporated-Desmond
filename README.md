# ClearGlassInc Artemis — GitHub Ecosystem Operations Hub

This repository is the public web and documentation edge for **ClearGlassInc Artemis**. It now includes a reliability-focused operations baseline so content, legal pages, automation, and deployment behave as one production system.

## Repository System Map

- `/index.html`, `/artemis.html`, `/guardian.html`, `/investors/index.html`
  - Public-facing product and investor pages.
- `/legal/*.html`
  - Legal documents, policy pages, and legal index.
- `/assets/`, `/logo.png`, `/schema.json`, `/sitemap.xml`, `/robots.txt`
  - Shared static assets and SEO/discovery metadata.
- `/bots/marketing_bot.py` + `/marketing/output/*`
  - Automated content generation and publication output.
- `/.github/workflows/*.yml`
  - CI validation, content automation, and deployment workflows.
- `/scripts/site_reliability_audit.py`
  - Python reliability audit for links, workflow hygiene, and baseline content checks.
- `/docs/artemis-intelligence-platform-blueprint.md`
  - Full-stack architecture and implementation blueprint for the self-improving intelligence platform.

## Reliability and Deployment Flows

1. **Code + Content Change** → push/PR.
2. **Site Reliability Audit** validates links, workflow sanity, and required docs.
3. **Pages Deployment Workflow** builds artifact from repository root and deploys through GitHub Pages environment.
4. **Marketing Bot Workflow** updates generated content on schedule/dispatch.

## Standard Operating Checks

Run locally:

```bash
python scripts/site_reliability_audit.py
```

## Manual Admin Checks (outside repo)

- GitHub Pages source should be set to **GitHub Actions**.
- If custom domain is used, ensure DNS + CNAME alignment and HTTPS enforced.
- Verify environment protection rules for `github-pages` deployment environment.


# ClearGlassInc

ClearGlassInc is building digital infrastructure for product licensing, AI-assisted operations, and crypto-aligned business systems.

## Live Demo
[Visit the ClearGlassInc site](https://clearglassinc.github.io)

## What This Project Does
- Organizes ClearGlassInc digital assets
- Publishes public-facing business and product pages
- Supports licensing, brand presence, and future monetization systems

## Current Focus
- GitHub Pages deployment
- Artemis self-evolution system
- Business automation infrastructure
- Public visibility and traffic growth

## Quick Links
- [Website](https://clearglassinc.github.io)
- [Issues](https://github.com/ClearGlassInc/ClearGlassInc.github.io/issues)
- [Pull Requests](https://github.com/ClearGlassInc/ClearGlassInc.github.io/pulls)
- [Roadmap](https://clearglassinc.github.io/roadmap.html)
- [Contact](https://clearglassinc.github.io/contact.html)

## Star the Repository

If this project aligns with your interest in AI operations, licensing, or crypto infrastructure, star the repo and follow development.

![GitHub last commit](https://img.shields.io/github/last-commit/ClearGlassInc/ClearGlassInc.github.io)
![GitHub repo size](https://img.shields.io/github/repo-size/ClearGlassInc/ClearGlassInc.github.io)
![GitHub issues](https://img.shields.io/github/issues/ClearGlassInc/ClearGlassInc.github.io)

# ClearGlassInc Artemis

Public website, governance documentation, and supporting automation for ClearGlassInc Artemis — enterprise cybersecurity, secure software architecture, and intelligence operations.

The site is published via GitHub Pages from the `main` branch.

## Repository structure

| Path | Purpose |
| --- | --- |
| `index.html`, `*.html` | Top-level pages of the public site (`/`, product pages, legal hub). |
| `assets/` | Site images and static media. |
| `legal/` | Legal pages and policy templates (privacy, terms, NDAs, IP assignment). |
| `investors/` | Investor-facing pages and briefing material. |
| `docs/` | Long-form blueprints, platform designs, and corporate documentation. See `docs/README.md`. |
| `bots/` | Python automation modules used by scheduled workflows. |
| `scripts/` | Operational scripts (site integrity, reliability audits, intel automation). |
| `tests/` | `pytest` suite covering `bots/` and `scripts/`. |
| `prompts/` | System and agent prompts referenced by the bots. |
| `infra/` | Terraform configuration for supporting infrastructure. |
| `runner/` | Self-hosted GitHub Actions runner setup notes. |
| `.github/workflows/` | CI: Pages build, CodeQL, site integrity/reliability, Python tests, scheduled bots. |
| `SECURITY.md` | Vulnerability reporting and disclosure policy. |
| `sitemap.xml`, `robots.txt`, `schema.json` | SEO and discovery metadata. |
| `.nojekyll` | Disables Jekyll processing on GitHub Pages; the site is served as static HTML. |

## Local development

The site is plain static HTML. No build step is required to preview it.

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

A Jekyll build is exercised in CI (`.github/workflows/jekyll-docker.yml`) as a structural check; it is not used to produce the deployed artifact.

## Python tooling

The bots and scripts target Python 3.11. Tests run on every push and pull request that touches Python sources.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # if present
pip install pytest
python -m pytest tests/ -v
```

## Continuous integration

Workflows in `.github/workflows/` cover:

- `pages-deploy.yml` — publish the site to GitHub Pages.
- `jekyll-docker.yml` — Jekyll build smoke test on HTML changes.
- `python-tests.yml` — `pytest` against `bots/` and `scripts/`.
- `codeql.yml` — CodeQL static analysis.
- `site-integrity.yml`, `site-reliability.yml`, `server-test.yml` — site health checks.
- `clearglassinc-coo-bot.yml`, `github-ceo-bot.yml`, `marketing-bot.yml`, `operations-finance-bot.yml` — scheduled automation.
- `self-hosted-deploy.yml` — self-hosted runner deployment path.

## Documentation

The canonical index of long-form documentation lives in `docs/README.md`. Notable entry points:

- Corporate and governance: `docs/clearglassinc_artemis_enterprise_corporate_layer.md`
- Platform architecture: `docs/clearglassinc_artemis_palantir_aip_blueprint.md`
- Self-evolving platform spec: `docs/clearglassinc_artemis_self_evolving_platform.md`
- Executive profile: `docs/desmond_otieno_odhiambo_executive_profile.md`

Top-level `*.md` blueprints (e.g. `ARTEMIS_INTELLIGENCE_PLATFORM_BLUEPRINT.md`, `CLEARGLASSINC_ARTEMIS_PRODUCTION_ARCHITECTURE.md`) are historical snapshots kept for reference.

## Security

Report vulnerabilities privately to **security@clearglassinc.com**. Scope, response SLAs, and safe-harbor terms are defined in `SECURITY.md`.

## Leadership

Founded by **Desmond Otieno Odhiambo**. See `docs/desmond_otieno_odhiambo_executive_profile.md`.

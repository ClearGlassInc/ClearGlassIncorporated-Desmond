# ClearGlassInc.

> Precision infrastructure for digital sovereignty, intelligent systems, and decentralized execution.

ClearGlassInc is a research and development initiative focused on advanced software systems, automation, cryptocurrency infrastructure, AI integration, and scalable digital products engineered for long-term leverage and financial independence.

---

## Vision

ClearGlassInc exists to build systems that increase autonomy, intelligence, operational efficiency, and ownership.

The objective is not temporary trends.

The objective is infrastructure.

We engineer frameworks that merge:

- Artificial Intelligence
- Automation
- Blockchain Systems
- Digital Asset Infrastructure
- High-performance Software
- Strategic Information Systems
- Licensing Models
- Scalable Revenue Architecture

---

## Core Philosophy

- Forward is the only direction.
- Precision over noise.
- Systems over chaos.
- Ownership over dependency.
- Execution over theory.

ClearGlassInc operates with a long-term mindset focused on resilient architecture and strategic technological positioning.

---

# Primary Areas

## AI Systems

Development of intelligent automation systems using:

- LLM integrations
- Autonomous workflows
- Multi-agent orchestration
- Predictive analysis
- Data intelligence pipelines

---

## Cryptocurrency Infrastructure

Research and deployment involving:

- Trading systems
- Blockchain integrations
- Smart contracts
- Wallet infrastructure
- On-chain analytics
- Tokenized ecosystems
- Decentralized finance frameworks

---

## Software Engineering

Production-grade development focused on:

- Backend systems
- API architecture
- Cloud deployment
- Secure infrastructure
- Performance optimization
- Scalable distributed systems

---

## Automation

Automation frameworks designed to reduce friction and maximize leverage.

Includes:

- Business automation
- AI-assisted execution
- Infrastructure scripting
- Workflow orchestration
- Monitoring systems
- Autonomous operational tooling

---

# Technology Stack

## Languages

- Python
- JavaScript
- TypeScript
- Solidity
- Go
- Bash

## Infrastructure

- Docker
- Linux
- GitHub Actions
- Kubernetes
- Cloudflare
- PostgreSQL
- Redis

## AI / ML

- OpenAI APIs
- Local LLM deployment
- Vector databases
- Embedding pipelines
- Retrieval systems

## Blockchain

- Ethereum
- Solana
- LayerZero
- Smart contracts
- Web3 integrations

---

# Repository Structure

```bash
.
├── ai/
├── automation/
├── blockchain/
├── infrastructure/
├── scripts/
├── research/
├── products/
├── docs/
└── README.md
```

---

# ClearGlass Inc — Website & Engineering Monorepo

Public website, governance documentation, and supporting automation for **ClearGlass Inc** — enterprise cybersecurity, secure software architecture, AI automation, and intelligence operations. Founded by **Desmond Otieno Odhiambo** (Founder & Chairman, Software Architect).

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

Report vulnerabilities privately to **clearglass369@gmail.com**. Scope, response SLAs, and safe-harbor terms are defined in `SECURITY.md`.

## Leadership

Founder & Chairman **Desmond Otieno Odhiambo**. See `docs/Desmond_Otieno_Odhiambo_executive_profile.md`.

## Architecture Blueprints

- [ClearGlassInc Artemis full-stack intelligence blueprint](CLEARGLASSINC_ARTEMIS_FULL_STACK_INTELLIGENCE_BLUEPRINT.md)

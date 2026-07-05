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

This repository is a website and engineering monorepo. The active top-level entry points are:

| Path | Purpose | Primary checks |
| --- | --- | --- |
| `index.html`, `*.html`, `assets/` | Static GitHub Pages website and product pages. | `python scripts/site_reliability_audit.py` |
| `data/platform/architecture.json`, `platform-architecture.html`, `PLATFORM_ARCHITECTURE.md` | Canonical ClearGlass Intelligence Platform taxonomy (executive layer, agent framework, hierarchy, product family, naming standard) and its data-driven page. | `python -m scripts.platform_registry --validate`; `python -m pytest tests/test_platform_registry.py` |
| `artemis/` | Installable Artemis Python package and environmental risk module. | `python -m pytest artemis/tests` |
| `deployment/artemis/` | Containerized Artemis FastAPI model-service deployment. | `uvicorn deployment.artemis.app.main:app` / Docker build |
| `bots/`, `scripts/`, `tests/` | Operational automation bots, repository audits, release/content tooling. | `python -m pytest tests` |
| `sentinel/` | Sentinel defensive intelligence package and tests. | `python -m pytest sentinel/tests` |
| `clearglass-commerce/` | Commerce control plane plus Storefront/Admin Next.js apps. | `pytest control-plane/tests`; `npm ci && npm run build` in each frontend |
| `apps/autostore/` | Autostore control plane, cockpit UI, and Docker Compose deployment. | `docker compose`; `npm ci && npm run build` in `cockpit` |
| `services/clearglass_agent_service/` | Render-deployed lawful risk-intelligence API service. | Docker build / `/health` |
| `.github/workflows/` | CI/CD workflows for tests, audits, Pages, commerce, policy, security, and scheduled bots. | GitHub Actions |
| `docs/`, top-level `*.md` | Long-form architecture, governance, and product documentation. | Markdown review |

## Local static-site run

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

## Python tooling

The Python packages and bots target Python 3.11+ unless a package-specific README says otherwise. The root pytest configuration now includes the major Python test roots.

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install -e .[test]
python -m pip install -r requirements.txt
python -m pytest -q
```

## Frontend tooling

Each Next.js app is intentionally self-contained. Install dependencies in the app directory before building.

```bash
cd clearglass-commerce/storefront && npm ci && npm run build
cd ../admin && npm ci && npm run build
cd ../../apps/autostore/cockpit && npm ci && npm run build
```

## Continuous integration

Workflows in `.github/workflows/` cover the active CI/CD paths, including:

- `ci.yml` — Python tests, Ruff lint, site reliability audit, workflow doctor, and OSINT deck validation.
- `pages.yml` — GitHub Pages deployment for the static site.
- `commerce-frontend-ci.yml` and `commerce-deploy.yml` — commerce frontend validation and deployment.
- `auto-store.yml` — Autostore validation/deployment path.
- `security.yml`, `api-security-audit.yml`, `policy-gate.yml`, `release-supply-chain.yml`, and `ip-protection-scan.yml` — security, policy, and supply-chain checks.
- Scheduled automation workflows such as `bot-orchestrator.yml`, `content-pipeline.yml`, `control-surface-feeds.yml`, `defender-watch.yml`, and `health-monitor.yml`.

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

## ClearGlass Growth Entity

Run the local manual-review growth command system with PowerShell 7:

```powershell
pwsh -ExecutionPolicy Bypass -File .\ClearGlass-GrowthEntity.ps1 -Mode Sample -OpenFolder
pwsh -ExecutionPolicy Bypass -File .\ClearGlass-GrowthEntity.ps1 -Mode Full -OpenFolder
```

The script creates `ClearGlassGrowthEntity/` with configuration, content scoring exports,
daily posting briefs, finance action files, and logs. It is intentionally a planning and
compliance-review system only; do not store passwords, tokens, cookies, or API secrets in it,
and do not use it for fake engagement, mass DMs, scraping, or platform-bypass behavior.

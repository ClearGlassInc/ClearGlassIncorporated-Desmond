# ClearGlassInc Artemis

<div align="center">

![ClearGlassInc Artemis](assets/images/clearglass-logo.png)

## Governed intelligence infrastructure for decisions that cannot afford guesswork

**Fuse operational data, deploy policy-constrained AI agents, and preserve human authority at every consequential action.**

[**Explore the live platform →**](https://www.clearglassinc.com/) · [**Review the Artemis architecture →**](docs/clearglassinc_artemis_self_evolving_platform.md) · [**Start a discussion →**](https://github.com/ClearGlassInc/ClearGlassInc.github.io/discussions)

[![Website](https://img.shields.io/badge/Website-Live-00e5ff?style=for-the-badge)](https://www.clearglassinc.com/)
[![License](https://img.shields.io/badge/License-See%20LICENSE-8b5cf6?style=for-the-badge)](LICENSE)
[![Security](https://img.shields.io/badge/Security-Policy-39ff88?style=for-the-badge)](SECURITY.md)
[![Contributions](https://img.shields.io/badge/Contributions-Welcome-f8fafc?style=for-the-badge)](CONTRIBUTING.md)

</div>

---

ClearGlassInc Artemis is an engineering monorepo and live product surface for secure automation, defensive intelligence, governed commerce, and high-assurance agent systems. It turns fragmented data and workflows into auditable decision support—without allowing model output to manufacture authority.

> [!IMPORTANT]
> **See the system, then inspect the evidence.** Visit the [live ClearGlassInc experience](https://www.clearglassinc.com/), explore the implementation map below, and star the repository if governed agentic systems belong in your technical radar.

## Why this matters

Most AI demonstrations optimize for fluent output. Mission-critical systems must optimize for **traceable evidence, bounded authority, reversible deployment, and measurable operator trust**. Artemis treats AI output as untrusted until deterministic policy checks and, where required, explicit human approval make the next transition valid.

### What makes Artemis different

| Ordinary AI project | ClearGlassInc Artemis |
| --- | --- |
| Chat interface as the product | Ontology, policy, agents, approval, audit, and deployment as one system |
| Model confidence as authority | Evidence lineage and deterministic authorization outside the model |
| Autonomous action by default | Read-only analysis → draft → human approval → governed execution |
| Architecture claims without boundaries | Implemented components are separated from clearly labeled target-state blueprints |
| One-shot launch | Operational docs, tests, security gates, and an evolving product surface |

## Platform highlights

- **Governed agent workflows** — typed tools, risk-scored transitions, approval queues, and append-only material-action records.
- **Full-stack intelligence design** — operator interfaces, Python services, ontology contracts, retrieval, event processing, and model routing.
- **Palantir-aligned blueprint** — precise roles for Gotham, Foundry, AIP, and Apollo without implying unverified provisioning.
- **Secure-by-construction controls** — need-to-know access, zero-trust boundaries, provenance, rollback, and policy-as-code.
- **Production delivery surfaces** — GitHub Pages, containerized services, CI gates, health checks, and independently deployable applications.

## Start here

| Your goal | Best entry point |
| --- | --- |
| Experience the brand and products | [Visit clearglassinc.com](https://www.clearglassinc.com/) |
| Understand the end-to-end platform | [Read the self-evolving Artemis blueprint](docs/clearglassinc_artemis_self_evolving_platform.md) |
| Inspect Gotham / Foundry / AIP / Apollo alignment | [Read the Palantir AIP blueprint](docs/clearglassinc_artemis_palantir_aip_blueprint.md) |
| Evaluate defensive agent governance | [Explore Sentinel](sentinel/README.md) |
| Review governed commerce automation | [Explore ClearGlass Commerce](clearglass-commerce/README.md) |
| Help shape the roadmap | [Open a feature request](https://github.com/ClearGlassInc/ClearGlassInc.github.io/issues/new?template=feature_request.md) |

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
- Secure deployment agent prompt: `CLEARGLASS_SECURE_DEPLOYMENT_AGENT_PROMPT.md`
- Executive profile: `docs/desmond_otieno_odhiambo_executive_profile.md`

Top-level `*.md` blueprints (e.g. `ARTEMIS_INTELLIGENCE_PLATFORM_BLUEPRINT.md`, `CLEARGLASSINC_ARTEMIS_PRODUCTION_ARCHITECTURE.md`) are historical snapshots kept for reference.

## Security

Report vulnerabilities privately to **clearglass369@gmail.com**. Scope, response SLAs, and safe-harbor terms are defined in `SECURITY.md`.

## Leadership

Founder & Chairman **Desmond Otieno Odhiambo**. See `docs/Desmond_Otieno_Odhiambo_executive_profile.md`.

## Architecture Blueprints

- [ClearGlassInc Artemis full-stack intelligence blueprint](CLEARGLASSINC_ARTEMIS_FULL_STACK_INTELLIGENCE_BLUEPRINT.md)
- [ClearGlassInc Artemis local SEO and multi-channel growth intelligence plan](CLEARGLASSINC_ARTEMIS_LOCAL_SEO_GROWTH_PLAN.md)

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

## Threads Growth Command Center V3

Run the Python-first, compliant Threads growth command center locally:

```bash
python -m bots.threads_growth_command_center --mode all --brand-name ClearGlassInc --root-path ./ThreadsGrowthCommandCenter_V3
python -m bots.threads_growth_command_center --mode add-kpi --root-path ./ThreadsGrowthCommandCenter_V3 --followers 100 --posts 3 --replies 40 --likes 80 --reposts 10 --impressions 1000 --profile-visits 25 --notes "Manual daily closeout"
```

The system creates a 30-day content calendar, daily manual execution brief,
copy-editing draft files, KPI tracker, engagement tracker, backups, and a
self-contained HTML dashboard. It is intentionally a planning, drafting, and
measurement system only: zero botting, zero scraping, no automated follows,
likes, comments, reposts, DMs, or storage of platform cookies/session tokens.

---

## Use cases

- **Operational intelligence:** triage signals, correlate evidence, and prepare reviewable decision packages.
- **High-assurance automation:** separate analysis, drafting, authorization, execution, and audit.
- **Defensive monitoring:** operate bounded, fail-closed agents over approved data and tools.
- **Governed commerce:** automate low-risk work while preserving approval for financial and material actions.
- **Architecture research:** evaluate ontology, agent, policy, deployment, and self-improvement patterns without confusing target state with deployed fact.

## Evidence, not invented social proof

Evaluate ClearGlassInc Artemis through its public code, tests, threat models, release history, and live product surfaces. Testimonials, customer logos, performance claims, and adoption metrics should appear here only when they are attributable, permissioned, and verifiable.

> [!NOTE]
> Palantir-aligned documents describe an integration architecture. They do not, by themselves, prove that Gotham, Foundry, AIP, Apollo, coalition infrastructure, or production environments are provisioned.

## Roadmap

- Harden reproducible evaluation fixtures for governed agent transitions.
- Expand ontology-driven examples with explicit confidence, temporal state, and lineage.
- Improve operator-facing provenance and approval explanations.
- Publish measurable performance and reliability evidence when reproducible data exists.
- Continue accessibility, Pages reliability, security, and supply-chain improvements through existing review gates.

Roadmap items are proposals, not promises or evidence of deployment. Track concrete work through [issues](https://github.com/ClearGlassInc/ClearGlassInc.github.io/issues) and [releases](https://github.com/ClearGlassInc/ClearGlassInc.github.io/releases).

## Frequently asked questions

### Is Artemis fully autonomous?

No. Artemis is designed to automate bounded analysis and drafts while keeping deterministic policy and human authorization at consequential boundaries.

### Is every architecture blueprint already deployed?

No. Target-state documents are specifications. Source code, runtime checks, deployment records, and explicit status labels define what is implemented.

### Is ClearGlassInc affiliated with Palantir?

This repository does not claim an affiliation. Gotham, Foundry, AIP, and Apollo name the intended responsibilities in a Palantir-aligned integration design.

### How can I contribute?

Read [CONTRIBUTING.md](CONTRIBUTING.md), follow the [Code of Conduct](CODE_OF_CONDUCT.md), and select a narrowly scoped issue. Include the checks you actually ran and preserve all governance boundaries.

### How do I report a security issue?

Follow [SECURITY.md](SECURITY.md) and use the private reporting route. Do not disclose vulnerability details in a public issue or Discussion.

## Help advance governed agent engineering

- **Star** the repository if you want to find the architecture again.
- **Watch releases** if you want meaningful milestone notifications.
- **Fork and remix** a trust-boundary diagram for your domain, then share the evidence and assumptions in Discussions.
- **Challenge an invariant** with a reproducible failure case or focused issue.
- **Share responsibly:** send another engineer the [governance architecture](docs/clearglassinc_artemis_self_evolving_platform.md), not an unsupported slogan.

The complete, ethics-first launch sequence, channel copy, experiments, metrics, and automation boundaries live in the [GitHub Growth and Launch Playbook](docs/GITHUB_GROWTH_LAUNCH_PLAYBOOK.md).

## License and contact

See [LICENSE](LICENSE) for repository terms and check subtree-specific documentation before reuse. For product discovery, visit [www.clearglassinc.com](https://www.clearglassinc.com/). Use GitHub Discussions for public technical questions and [SECURITY.md](SECURITY.md) for vulnerabilities.

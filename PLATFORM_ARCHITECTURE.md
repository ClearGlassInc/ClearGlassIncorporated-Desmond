# ClearGlass Intelligence Platform — Architecture & Naming Standard

> **Status:** This document is the canonical brand + system architecture for
> ClearGlass Inc. Names below fall into two honest buckets — **operational**
> (bound to a system that already ships in this repo) and **reserved**
> (namespace reserved in the taxonomy, not yet provisioned). Reserved names are
> *plans*, not claims, exactly like the PERCIVAL v9 target-state docs in
> `sentinel/`. The machine-readable source of truth is
> [`data/platform/architecture.json`](data/platform/architecture.json); the
> validator (`scripts/platform_registry.py`) fails CI if an operational name
> ever loses its backing artifact.

The point of a platform architecture — instead of a flat list of "bot names" —
is a single taxonomy that stays internally consistent as the ecosystem grows
from a handful of agents to hundreds. Every product line, platform tier, and
agent gets a place, a prefix, and a status.

```
python -m scripts.platform_registry            # human-readable report
python -m scripts.platform_registry --validate  # exit 1 on any inconsistency
python -m scripts.platform_registry --json      # summary counts as JSON
```

---

## World-class naming standard

A consistent taxonomy makes the platform feel like one operating system rather
than a bag of tools.

| Tier | Prefix | Example | Pattern |
|------|--------|---------|---------|
| Platform | `ClearGlass` | ClearGlass Nexus | `ClearGlass <Codename>` |
| AI Engine | `Cortex` | Cortex-1 | `Cortex-<n>` |
| Agent | `CGA` | CGA-Sentinel-01 | `CGA-<Codename>-<nn>` |
| Workflow | `Flow` | Flow-Incident-001 | `Flow-<Topic>-<nnn>` |
| Knowledge | `Chronicle` | Chronicle-Alpha | `Chronicle-<Series>` |
| Security | `Sentinel` | Sentinel-Edge | `Sentinel-<Node>` |
| Analytics | `Vector` | Vector-X | `Vector-<Node>` |
| Automation | `Forge` | Forge-Auto | `Forge-<Node>` |
| Infrastructure | `Bastion` | Bastion-Cloud | `Bastion-<Node>` |
| Executive | `Oracle` | Oracle-Prime | `Oracle-<Node>` |

---

## Executive layer

The top-level platform tiers. Each is a `ClearGlass <Codename>` brand.

| Codename | Role | Status | Backing artifact |
|----------|------|--------|------------------|
| ClearGlass Nexus | Central intelligence & orchestration platform | operational | `clearglass-nexus.html` |
| ClearGlass Command | Executive operations center | operational | `command-console.html` |
| ClearGlass Cortex | AI reasoning engine | operational | `agents/clearglass_agent_os/` |
| ClearGlass Core | Platform runtime | operational | `platform.js` |
| ClearGlass Fabric | Distributed services layer | reserved | — |

---

## Autonomous agent framework

Nine capability domains. Operational codenames already map to shipping surfaces;
reserved codenames hold their place in the namespace.

- **Executive AI** — Executive · Director · **Governor** · Steward · Prime
- **Intelligence** — Oracle · Spectra · Prism · **Vector** · Meridian · Horizon · Atlas · Helix · **Pulse** · Axiom
- **Cybersecurity** — Bastion · Citadel · Fortress · Rampart · ShieldCore · LockPoint · **GuardianX** · IronGate · **SentinelOne** · BlackMirror
- **Threat Intelligence** — Recon · Hunter · Watchtower · DeepTrace · Signal · Echo · ShadowNet · RedScope · BlueWatch · ThreatGrid
- **OSINT** — Pathfinder · Observer · Discovery · Cartographer · Surveyor · **Scout** · AtlasOS · **IntelMap** · OpenIntel · TraceNet
- **Digital Forensics** — Evidence · **Ledger** · Chronicle · Timeline · Recover · Integrity · Veritas · Provenance · Archive · Chain
- **AI Automation** — Catalyst · **Forge** · Reactor · VectorFlow · Assembly · Pipeline · Conductor · Maestro · Architect · Builder
- **Business Intelligence** — Polaris · Compass · Lighthouse · **Navigator** · **Beacon** · MarketPulse · **RevenueIQ** · GrowthCore · Opportunity · Forecast
- **Development** — **Foundry** · Workshop · ForgeWorks · DevCore · CodePilot · StackEngine · Compiler · Runtime · BuilderAI · LaunchPad

*(Bold = operational. See the registry for the exact artifact each binds to.)*

---

## Enterprise multi-agent hierarchy

```
ClearGlass Nexus
│
├── Cortex (Reasoning)
├── Sentinel (Cyber Defense)
├── Recon (OSINT)
├── Forge (Automation)
├── Oracle (Strategic AI)
├── Ledger (Compliance)
├── Beacon (Monitoring)
├── Navigator (Business)
├── Foundry (Development)
├── Pulse (Telemetry)
├── Chronicle (Knowledge)
├── Catalyst (Workflow)
├── Vector (Analytics)
├── Bastion (Infrastructure)
└── Horizon (Forecasting)
```

The hierarchy is a domain map: each node names a capability the platform serves.
A node's status reflects whether that capability ships today, independent of
whether its specific agent codename is provisioned yet.

---

## Premium product family

Recognizable product lines instead of standalone names.

| Product | Domain | Status |
|---------|--------|--------|
| ClearGlass Sentinel | Cybersecurity | operational |
| ClearGlass Oracle | AI Decision Intelligence | reserved |
| ClearGlass Forge | Automation Platform | operational |
| ClearGlass Vector | Data Analytics | operational |
| ClearGlass Chronicle | Knowledge Management | reserved |
| ClearGlass Recon | OSINT Suite | operational |
| ClearGlass Ledger | Compliance & Audit | operational |
| ClearGlass Beacon | Monitoring & Alerting | operational |
| ClearGlass Pulse | Infrastructure Observability | operational |
| ClearGlass Navigator | Executive Dashboard | operational |
| ClearGlass Foundry | Developer Platform | operational |
| ClearGlass Horizon | Predictive Intelligence | reserved |

---

## How to extend this safely

1. Add the name to `data/platform/architecture.json` under the right section.
2. If it ships, set `status: "operational"` **and** point `artifact` at the
   real file. Otherwise `status: "reserved"` with `artifact: null`.
3. Run `python -m scripts.platform_registry --validate` — it must pass. The
   test suite (`tests/test_platform_registry.py`) enforces the same invariant,
   so an operational name with a missing artifact fails CI by design.
4. Keep the naming standard: a name's prefix/pattern should match its tier.

This is the same read-only-truth discipline the rest of the monorepo runs on —
the registry never claims a capability the repo can't back up.

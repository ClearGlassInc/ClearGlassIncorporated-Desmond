# ClearGlass Minerals Intelligence Platform Architecture

Status: implementation architecture for the GitHub Pages production MVP and the service-grade expansion path.

## 1. Repository decision

The current ClearGlass production site is a static GitHub Pages application with existing Critical Minerals Intelligence assets under `minerals.html`, `minerals.js`, `minerals.css`, and `data/minerals/**`. The platform therefore reuses that convention instead of forcing a repository-wide framework migration.

The production MVP is implemented as an additive static intelligence application that consumes the existing provenance-aware minerals manifest and normalized feed snapshots. No existing page, route, product, workflow, or data source is removed.

A future service deployment can lift the same domain model into Next.js 15+, PostgreSQL/PostGIS, Redis, worker queues, authenticated APIs, and streaming updates without changing the public data contracts used by the MVP.

## 2. Product identity

Product name: ClearGlass Minerals Intelligence Platform

Primary route: `/minerals-platform.html`

Existing route retained: `/minerals.html` (Critical Minerals Intelligence reference and compliance decision-support surface)

Product role: operational command center for mineral markets, supply-chain exposure, project intelligence, trade, risk, alerts, data-source health, and source-transparent analyst workflows.

## 3. Non-negotiable data rules

1. Never fabricate live data.
2. Every observed value must retain source, freshness, retrieval time, status, and confidence metadata.
3. `LIVE`, `DELAYED`, `STATIC REFERENCE`, `STALE`, `OFFLINE`, `ESTIMATED`, `ANALYST`, and `DEMO` must remain distinguishable.
4. Synthetic seed records are permitted only in an explicit Demo Mode and must carry `demo: true`.
5. Missing records render as unavailable or unknown, not zero.
6. Derived indicators expose methodology and inputs.
7. AI-assisted summaries are advisory and may only cite records present in the platform state.
8. Private supplier or customer records are never published to GitHub Pages.

## 4. MVP architecture

### Presentation

- `minerals-platform.html` — desktop-first command shell and semantic content
- `minerals-platform.css` — dark graphite/glass analytical design system
- `minerals-platform.js` — application state, provenance, filters, deterministic analytics, local watchlists, alerts, and demo-mode controls
- shared `/nav.js`, `/logo-badge.js`, `/stealth-glass.js` — existing ClearGlass site shell

### Data contracts

Existing authoritative/public-data contracts remain the source of truth:

- `/data/minerals/manifest.json`
- `/data/minerals/metadata/minerals.json`
- `/data/minerals/metadata/sources.json`
- `/data/minerals/metadata/methodology.json`
- `/data/minerals/latest/*.json`

New platform-only contracts:

- `/data/minerals/platform/config.json` — route, layer, module, and capability registry
- `/data/minerals/platform/demo.json` — explicitly synthetic demonstration entities, trade links, and events

### Client state

The static MVP maintains ephemeral application state in memory and uses `localStorage` only for user-controlled non-sensitive preferences such as watchlists, saved filters, and demo-mode state. No authentication claims or confidential records are stored client-side.

## 5. Functional MVP modules

- Command Center
- Global Map
- Mineral Markets
- Mines and Projects
- Supply Chains
- Trade Intelligence
- Risk Radar
- Exploration Monitor
- Companies
- Alerts
- Reports
- Data Sources
- Administration/readiness

The static MVP exposes all modules as working command views. Modules that lack connected production data show operational empty states with source health and integration requirements rather than placeholder metrics.

## 6. Map strategy

The GitHub Pages MVP uses a dependency-light SVG geographic command layer so the page remains deployable without runtime API keys. It supports:

- clustered or grouped project/facility points
- supply-chain relationship arcs
- layer toggles
- mineral filters
- risk filters
- source/provenance inspection
- explicit Demo Mode

The service-grade deployment should replace this renderer with MapLibre GL and deck.gl backed by PostGIS vector/GeoJSON endpoints.

## 7. Risk model

Risk scoring is transparent and configurable. The platform supports component inputs for geopolitical, regulatory, sanctions, conflict, concentration, infrastructure, logistics, climate, water, environmental, labor, community, disclosed cybersecurity, financial, production, permit, and data-confidence risk.

The static MVP computes only from records actually loaded into state. A score is not emitted when required inputs are absent. Demo-mode scores are visibly labeled synthetic.

## 8. Analyst assistant boundary

The MVP includes a deterministic analyst query surface rather than an unconstrained model call. It can answer source-grounded questions from loaded records, explain feed state, summarize selected risk factors, compare available mineral metadata, and surface missing evidence.

Future AI integration must use retrieval from platform records, return source identifiers with every answer, refuse unsupported assertions, and record generation metadata for analyst review.

## 9. Service-grade target architecture

When the product is moved from static MVP to authenticated SaaS/enterprise deployment:

- Next.js 15+ App Router and TypeScript strict mode
- React Server Components for read-heavy views
- Tailwind CSS and accessible component primitives
- MapLibre GL/deck.gl
- ECharts/Recharts/D3
- PostgreSQL + PostGIS
- Prisma or Drizzle
- Redis for cache, source TTLs, rate limits, queues, and temporary state
- BullMQ or Temporal workers
- Zod validation
- versioned OpenAPI
- SSE/WebSocket updates where a provider supports streaming
- OAuth/OIDC, SAML compatibility, MFA, organization scoping, RBAC
- Playwright, Vitest, accessibility and visual-regression gates
- Docker Compose for local services

## 10. Service database domains

The target relational model contains UUID-primary-key tables for minerals, mineral forms, countries, jurisdictions, mines, deposits, projects, facilities, companies, ownership relationships, production, reserves/resources, price series, trade records, logistics nodes, shipping routes, risk assessments, risk factors, alerts, watchlists, events, documents, data sources, ingestion runs, provenance, analyst annotations, saved views, reports, users, organizations, roles, and audit logs.

Spatial entities use PostGIS geometry/geography columns and appropriate GiST/SP-GiST indexes. Soft deletion is used for mutable business entities where historical traceability matters.

## 11. API plan

Future `/api/v1` resources:

- `/search`
- `/map/features`
- `/minerals`
- `/projects`
- `/markets`
- `/trade`
- `/risk`
- `/alerts`
- `/watchlists`
- `/reports`
- `/sources`
- `/ingestion`
- `/exports`

All endpoints require validation, authorization, pagination, filtering, sorting, consistent error envelopes, cache-control policy, and provenance references.

## 12. Ingestion framework

Source adapters carry:

- source ID
- provider and dataset
- license/use restrictions
- geographic coverage
- cadence
- expected freshness
- last successful sync
- raw-to-normalized transformation log
- field-level provenance
- retry/backoff policy
- deduplication rules
- low-confidence review routing

Connectors must respect provider terms, API limits, robots directives where applicable, attribution, copyright, and export controls.

## 13. Security controls

Static MVP:

- no secrets or private datasets
- no credential-bearing client requests
- CSP/security-header compatibility with current site deployment
- input sanitization for rendered text
- no `innerHTML` from remote records
- export limited to currently loaded public/demo records
- explicit source-status labeling

Service deployment:

- server-side secret management
- TLS in transit and encrypted storage
- MFA and SSO
- organization-aware RBAC
- audit logging for logins, exports, edits, alerts, configuration, and AI reports
- rate limits and abuse controls
- secure uploads and malware scanning hooks
- CSRF protection where state-changing cookie-authenticated requests exist
- row-level access policy where multi-tenant

## 14. Phased implementation

### Phase A — production MVP

- product registration
- global navigation registration
- command center shell
- source-health orchestration
- mineral taxonomy explorer
- map command view
- risk/trade/supply-chain workspaces
- watchlist and alerts
- deterministic analyst assistant
- explicit demo mode
- sitemap/internal-link wiring
- regression test

### Phase B — licensed/public connectors

- normalized production/reserves extraction
- trade connector
- policy/regulatory connector
- public-company filing adapter
- trusted news/RSS adapters
- project/facility registry

### Phase C — authenticated service

- Next.js application
- PostGIS data model
- Redis/worker orchestration
- API and OpenAPI
- RBAC/SSO/MFA
- audit ledger
- organization watchlists and alert delivery

### Phase D — advanced intelligence

- licensed market pricing
- geospatial overlays
- verified logistics relationships
- scenario engine
- anomaly detection
- source-grounded AI briefings

## 15. Deployment contract

The MVP must continue to pass the repository's existing Pages build and integrity gates. New files are public static artifacts only. Production data remains governed by the existing minerals manifest and pipeline; the platform never upgrades a feed's status merely because the UI is available.

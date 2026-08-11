# ClearGlass Minerals Intelligence Platform — Service Grade

Authenticated enterprise service for critical-minerals intelligence. This application complements the public GitHub Pages command surface at `/minerals-platform.html`; it does not replace or weaken that public-data-safe MVP.

## Operating principles

- Never fabricate live prices, production, reserves, trade flows, projects, ownership, or risk.
- Preserve source, collection time, transformation time, confidence, license, freshness, and analyst-review state.
- Keep observed, delayed, estimated, analyst-entered, demo, and unknown records distinguishable.
- Missing evidence remains unknown; it is never coerced to zero or a neutral risk score.
- AI-assisted outputs are drafts/evidence views and require human review before publication.
- Organization data is scoped by RBAC and is never published into GitHub Pages artifacts.

## Stack

- Next.js 15+ App Router, React, strict TypeScript
- Tailwind CSS analytical UI
- MapLibre GL for geospatial display
- ECharts for market visualization
- PostgreSQL 16 + PostGIS
- Prisma ORM
- Redis + BullMQ
- Zod validation
- OpenAPI 3.1
- Vitest unit tests
- Playwright desktop/mobile, accessibility, and visual-regression setup
- Docker Compose for local PostGIS/Redis

## Service modules

Command Center, Global Map, Mineral Markets, Mines & Projects, Supply Chains, Trade Intelligence, Risk Radar, Exploration Monitor, Companies, Alerts, Reports, Data Sources, Administration, persistent saved views, and a source-grounded analyst endpoint.

## Quick start

```bash
cd apps/minerals-platform
cp .env.example .env
docker compose up -d
npm install
npm run db:generate
npm run db:migrate:dev -- --name init
npm run db:seed
npm run dev
```

Open `http://localhost:3000`.

Development auth uses a fixed local administrator identity seeded by `prisma/seed.ts`. Production must set `AUTH_MODE` to a non-development value and place the app behind a trusted OIDC/SAML-capable identity gateway that strips user-supplied `x-cg-*` identity headers before injecting verified claims.

## Commands

```bash
npm run dev              # development server
npm run build            # Prisma generate + production Next build
npm run start            # production server
npm run lint             # Next/ESLint gate
npm run typecheck        # strict TypeScript
npm test                 # Vitest
npm run test:e2e         # Playwright desktop/mobile/a11y
npm run db:generate      # Prisma client
npm run db:migrate       # deploy committed migrations
npm run db:migrate:dev   # create/apply development migration
npm run db:seed          # taxonomy + countries + source registry
npm run worker           # BullMQ ingestion worker
npm run openapi:check    # required API-path contract check
```

## API

OpenAPI source: `openapi.yaml`.

Core resources:

- `GET /api/v1/health`
- `GET /api/v1/search?q=...`
- `GET /api/v1/minerals`
- `GET /api/v1/projects`
- `GET /api/v1/map/features`
- `GET /api/v1/markets`
- `GET /api/v1/trade`
- `GET|POST /api/v1/risk`
- `GET|POST /api/v1/alerts`
- `GET|PATCH /api/v1/alerts/:id`
- `POST /api/v1/alerts/:id/deliver`
- `GET|POST /api/v1/watchlists`
- `PATCH /api/v1/watchlists/:id`
- `GET|POST /api/v1/reports`
- `PATCH /api/v1/reports/:id`
- `GET /api/v1/sources`
- `GET|POST /api/v1/ingestion`
- `GET /api/v1/exports`
- `GET|POST /api/v1/saved-views`
- `POST /api/v1/analyst`
- `GET /api/v1/stream` (SSE source-health updates)

Responses use a consistent `{ ok, data }` or `{ ok, error }` envelope except file exports and SSE.

## Data model

`prisma/schema.prisma` defines UUID/timestamped domains for:

- Minerals and mineral forms
- Countries and jurisdictions
- Mines, deposits, projects, facilities
- Companies and ownership relationships
- Production, reserves/resources, price series, trade records
- Logistics nodes and shipping routes
- Risk assessments and component factors
- Alerts, watchlists, watchlist items, events
- Source documents, data sources, ingestion runs, provenance records
- Analyst annotations, saved views, reports
- Users, organizations, role memberships, audit logs

Spatial entities include PostGIS `geography(Point,4326)` or `geography(LineString,4326)` contracts. Latitude/longitude mirrors are retained for portable API reads and simple indexing; service migrations should maintain both representations consistently.

## Risk methodology

`lib/risk.ts` implements `weighted-mean-v1`:

- Component scores: 0–100 or unknown.
- Component weights: 0–1.
- If less than 50% of configured weight has evidence, overall risk is `UNKNOWN`.
- Available weights are normalized; missing factors are never assigned a default score.
- Severity: LOW `<34`, MODERATE `34–66.99`, HIGH `67–84.99`, CRITICAL `>=85`.
- Senior Analyst role is required for analyst overrides.
- Overrides are persisted with a reason and audit event.

HHI concentration is calculated from normalized shares; empty evidence returns no concentration signal rather than a fabricated market structure.

## Ingestion

`lib/sources.ts` defines the adapter contract. Every adapter returns:

- source ID
- status
- collection time
- transformation time
- confidence
- license
- attribution
- normalized record envelope
- errors

`workers/ingestion.ts` persists snapshot lineage, content hashes, per-record provenance, source freshness, record counts, and transformation logs. Jobs use BullMQ exponential retries and are subject to source TTL rules at enqueue time.

The initial adapters consume the existing ClearGlass public minerals snapshots. Provider-specific adapters can be added without modifying the API contract.

## Alert delivery

Supported channels:

- In-platform alert workflow
- Email via `SMTP_URL`
- Generic webhook via `ALERT_WEBHOOK_URL`
- Slack incoming webhook
- Microsoft Teams incoming webhook/adaptive-card endpoint

Delivery is explicit and audited. Secrets remain server-side.

## Analyst assistant

`POST /api/v1/analyst` performs evidence retrieval across minerals, projects, mines, events, and source health. It returns structured evidence, uncertainty, and source identifiers. It does not invent a narrative when evidence is absent.

An external model may be configured later through `AI_PROVIDER`, `AI_API_KEY`, and `AI_MODEL`, but model invocation must remain retrieval-grounded. The current implementation deliberately does not send records to an external model automatically.

## Authentication and authorization

Roles:

- Viewer
- Analyst
- Senior Analyst
- Data Steward
- Administrator
- API Client

The current production boundary is SSO-ready: a trusted ingress completes OAuth/OIDC or SAML authentication, performs MFA according to organization policy, strips inbound identity headers, and injects verified user/org/role claims. The application enforces authorization on every API route.

Do not expose the service directly to the public internet with production `AUTH_MODE` unless that trusted identity boundary is in place.

## Security controls

- strict input validation with Zod
- server-only secrets
- CSP and security headers
- organization-scoped records
- RBAC on reads and mutations
- audit log on risk, alerts, reports, ingestion, exports, saved views, analyst queries
- HMAC-linked audit records
- source TTL/rate awareness
- safe export limits
- AI report review gate
- no private data in GitHub Pages
- explicit demo/live separation

See `SECURITY.md` for deployment requirements.

## Backups and recovery

Minimum production policy:

1. Managed PostgreSQL with automated daily backups and point-in-time recovery.
2. PostGIS extension version pinned and tested before upgrades.
3. Redis treated as reconstructable queue/cache state; use persistence only when operational requirements justify it.
4. Store source documents and provenance snapshots in durable object storage when retention requirements exceed database capacity.
5. Quarterly restore test to a non-production environment.
6. Record RPO/RTO and recovery evidence in the operator log.

## Data retention

Defaults are configuration policy, not hard-coded deletion:

- audit logs: 7 years unless counsel or contract requires otherwise
- source/provenance: retain according to provider license and evidence needs
- analyst annotations/reports: organization policy
- temporary uploads: delete after processing unless explicitly retained
- queue job metadata: bounded by BullMQ retention configuration
- user deletion: soft-delete where evidence/audit obligations require traceability

## Performance budgets

Target service budgets:

- API p95 read latency under 500 ms for indexed queries at normal load
- initial dashboard LCP under 2.5 s on production infrastructure
- map payload default under 1,000 features; hard API cap 5,000
- export hard cap 5,000 rows per request until asynchronous exports are introduced
- source-refresh fan-out limited by worker concurrency and provider quotas

## Deployment

The authenticated service requires a runtime platform capable of Node.js, PostgreSQL/PostGIS, Redis, background workers, TLS, server-side secrets, and trusted SSO ingress. GitHub Pages remains the public static product surface and must not be used to host the authenticated service backend.

Recommended deployment sequence:

1. Provision managed PostgreSQL/PostGIS and Redis.
2. Configure secret manager values from `.env.example`.
3. Deploy migrations with `npm run db:migrate`.
4. Seed taxonomy/source registry where appropriate.
5. Deploy the Next.js web service.
6. Deploy the ingestion worker as a separate process using the same release.
7. Configure trusted OIDC/SAML ingress and MFA.
8. Run health, API, Playwright, and source-ingestion smoke tests.
9. Enable alert connectors only after test-message verification.
10. Set backup, monitoring, and incident-response alerts.

## Data limitations and licensing

The repository does not include paid market feeds, private supplier data, satellite entitlements, or provider credentials. A configured adapter does not imply licensing rights. Each provider's terms, attribution requirements, redistribution rules, retention limits, and API rate limits remain controlling.

Public snapshot ingestion inherits the metadata and uncertainty of the underlying source. Missing records remain missing.

## Next priorities

- provider-specific normalized production/reserve/trade loaders
- PostGIS spatial indexes in the generated baseline migration
- asynchronous large exports
- configurable risk-weight administration UI
- verified mine-to-refinery relationship model and scenario engine
- organization digest schedules and escalation policy editor
- external model adapter with citation-enforcement tests
- licensed satellite/environmental overlays

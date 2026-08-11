# Minerals Intelligence Platform — Completion Manifest

## 1. Architecture summary

The ClearGlass Minerals Intelligence Platform now has two deliberately separate deployment surfaces:

1. **Public GitHub Pages command surface** — `/minerals-platform.html` on the main ClearGlass site. It is public-data-safe, source-transparent, and can render unavailable/demo states without exposing private infrastructure.
2. **Authenticated service application** — `apps/minerals-platform/`, built with Next.js 15+, strict TypeScript, PostgreSQL/PostGIS, Prisma, Redis/BullMQ, MapLibre GL, ECharts, Framer Motion, Zod, OpenAPI, Vitest, and Playwright.

The service treats source ingestion as a staged provenance pipeline. Raw provider/webhook payloads are content-hashed, deduplicated, durably retained in `SourceDocument.metadata.rawPayload`, linked to provenance records, cached under per-source Redis TTLs, and explicitly reported as `STAGED_RAW_PROVENANCE` until a domain-specific transformer writes normalized records.

## 2. Files and systems created

Major service areas:

- `app/` — authenticated command shell and versioned API routes
- `components/` — MapLibre, ECharts, reduced-motion Framer Motion components
- `lib/` — database, Redis, RBAC, API errors, audit, risk, rate limits, provider adapters, imports, notification adapters
- `workers/` — ingestion and digest workers
- `scripts/` — source/digest scheduler registration, DB/OpenAPI checks
- `prisma/` — schema, PostGIS initialization, seed pipeline, baseline migration
- `config/` — provider examples, retention policy, performance budgets
- `tests/` — risk/HHI, imports, desktop/mobile, accessibility, opt-in visual regression
- `openapi.yaml` — API v1 contract
- `docker-compose.yml` — PostGIS + Redis local infrastructure
- `.env.example` — secret/configuration contract
- `README.md`, `SECURITY.md`, `DEPLOYMENT.md`, `OPERATOR_RUNBOOK.md` — operations documentation
- `.github/workflows/minerals-platform-service.yml` — isolated quality/integration workflow

## 3. Database schema summary

The Prisma/PostGIS model includes:

- minerals and mineral forms
- countries and jurisdictions
- mines, deposits, projects, facilities
- companies and ownership relationships
- production records
- reserve/resource estimates
- price series
- trade records
- logistics nodes and shipping routes
- risk assessments and risk factors
- alerts
- watchlists and watchlist items
- events
- source documents
- data sources
- ingestion runs
- provenance records
- analyst annotations
- saved views
- reports
- users
- organizations
- organization roles/memberships
- audit logs

UUID primary keys, timestamps, soft deletion where appropriate, relational indexes, and PostGIS GIST indexes are included in the baseline migration.

## 4. Available pages and routes

### Public

- `/minerals-platform.html`
- `/minerals.html`
- `/products.html`

### Authenticated service UI

- `/` — service-grade Command Center with Global Map, Market Series, and module navigation

### API v1

- `/api/v1/health`
- `/api/v1/search`
- `/api/v1/minerals`
- `/api/v1/projects`
- `/api/v1/mines`
- `/api/v1/companies`
- `/api/v1/map/features`
- `/api/v1/markets`
- `/api/v1/markets/analytics`
- `/api/v1/trade`
- `/api/v1/supply-chains`
- `/api/v1/exploration`
- `/api/v1/risk`
- `/api/v1/scenarios/supply-disruption`
- `/api/v1/provenance`
- `/api/v1/provenance/:id/review`
- `/api/v1/alerts`
- `/api/v1/alerts/:id`
- `/api/v1/alerts/:id/deliver`
- `/api/v1/watchlists`
- `/api/v1/watchlists/:id`
- `/api/v1/reports`
- `/api/v1/reports/:id`
- `/api/v1/sources`
- `/api/v1/ingestion`
- `/api/v1/ingestion/webhook/:sourceKey`
- `/api/v1/exports`
- `/api/v1/saved-views`
- `/api/v1/analyst`
- `/api/v1/stream`
- `/api/v1/admin/members`
- `/api/v1/admin/audit`
- `/api/v1/admin/audit/verify`
- `/api/v1/admin/review-queue`

## 5. Data sources — integrated, pending, demo

### Integrated source adapters

The authenticated service is wired to the existing public ClearGlass normalized snapshots for:

- prices
- production
- reserves
- trade
- policy
- sanctions
- supply risk
- news
- provenance

These adapters preserve each public feed's source status and metadata. `STATIC REFERENCE` is not relabeled as live. `OFFLINE` stays offline.

### Provider-gated / pending credentials or licensing

The repository does **not** fabricate or bundle paid provider entitlements. These remain disabled until lawful credentials/license terms are supplied:

- paid commodity/benchmark pricing
- licensed customs/trade provider APIs beyond existing public snapshots
- commercial satellite imagery/environmental layers
- private port/rail/shipping feeds
- private company/supplier datasets
- external AI model provider

`config/providers.example.json` records the enablement contract.

### Demo

The public static product keeps explicit synthetic demo data separately labeled. The authenticated service seed pipeline does not insert synthetic mines, projects, production, trade, or prices into production-domain tables.

## 6. Required environment variables — names only

Core runtime:

- `NODE_ENV`
- `APP_BASE_URL`
- `PUBLIC_MINERALS_BASE_URL`
- `INGESTION_CONCURRENCY`

Data/queue:

- `DATABASE_URL`
- `DIRECT_URL`
- `REDIS_URL`

Identity/security:

- `AUTH_MODE`
- `IDENTITY_GATEWAY_SECRET`
- `OIDC_ISSUER_URL`
- `OIDC_CLIENT_ID`
- `OIDC_CLIENT_SECRET`
- `SAML_ENTRYPOINT`
- `SAML_ISSUER`
- `SAML_CERT`
- `MFA_REQUIRED`
- `AUDIT_HASH_SECRET`
- `EXPORT_SIGNING_SECRET`
- `UPLOAD_MAX_BYTES`

Provider credentials:

- `USGS_API_KEY`
- `TRADE_API_KEY`
- `MARKET_DATA_API_KEY`
- `NEWS_API_KEY`
- `SATELLITE_API_KEY`
- `INGESTION_WEBHOOK_SECRET`

Alert/digest integrations:

- `SMTP_URL`
- `ALERT_EMAIL_FROM`
- `SLACK_WEBHOOK_URL`
- `TEAMS_WEBHOOK_URL`
- `ALERT_WEBHOOK_URL`
- `ALERT_WEBHOOK_SIGNING_SECRET`
- `DIGEST_EMAIL_TO`
- `DIGEST_DAILY_CRON`
- `DIGEST_WEEKLY_CRON`

AI adapter placeholders:

- `AI_PROVIDER`
- `AI_API_KEY`
- `AI_MODEL`

## 7. Local/database/test/deployment commands

```bash
cd apps/minerals-platform
cp .env.example .env
docker compose up -d
npm install
npm run db:generate
npm run db:migrate
npm run db:seed
npm run sources:register
npm run digests:register
npm run dev
```

Worker processes:

```bash
npm run worker
npm run worker:digests
```

Quality gates:

```bash
npm run openapi:check
npm run lint
npm run typecheck
npm test
npm run build
npm run test:e2e
```

Production database release:

```bash
npx prisma db execute --file prisma/init.sql --schema prisma/schema.prisma
npm run db:migrate
```

## 8. Security controls implemented

- fail-closed production middleware
- trusted OIDC/SAML identity-gateway contract
- application-side gateway proof secret
- MFA-ready identity boundary
- organization-aware RBAC
- Viewer / Analyst / Senior Analyst / Data Steward / Administrator / API Client roles
- server-only secrets
- CSP and security headers
- Zod request validation
- Redis rate limiting on search, analyst, export, and ingestion abuse-sensitive paths
- HMAC-signed generic alert webhook deliveries
- HMAC-signed machine-ingestion webhook with five-minute replay window
- source TTL enforcement and Administrator-only forced refresh
- same-organization alert assignment
- synchronous export caps and audit logging
- AI-assisted report publication blocked until human review
- provenance promotion to VERIFIED restricted to Administrator
- content-hash snapshot deduplication
- canonicalized, serialized HMAC-linked audit chain
- Administrator audit-chain verification endpoint
- no authenticated/private data added to GitHub Pages publishing allowlists
- no public file-upload endpoint in the initial service

## 9. Known data limitations and licensing considerations

- Existing public snapshots currently include feeds that are static-reference or offline; the service preserves those states.
- A configured adapter does not grant redistribution or retention rights. Provider license terms remain controlling.
- The generic ingestion worker stages raw evidence and provenance. It intentionally reports `domainRowsWritten: 0` until provider-specific field mappings are implemented and reviewed.
- Market analytics are observed-data calculations only; they do not produce forecasts.
- Supply-disruption scenarios use user-supplied arithmetic and are explicitly not forecasts.
- Supply-chain API exposes only verified ownership/logistics relationships. Inferred relationships remain separated and empty until evidence exists.
- Spatial queries use indexed geography contracts and latitude/longitude mirrors; deployment should verify consistency as provider-specific geospatial loaders are introduced.
- Synchronous exports are capped at 5,000 rows; larger exports should move to asynchronous signed artifacts.
- No private provider keys, commercial datasets, customer data, or paid source content are committed.

## 10. Next-priority enhancements

These are provider/integration expansions rather than missing platform foundations:

1. Implement reviewed provider-specific transformers that map staged raw payloads into normalized production/reserve/trade/market tables.
2. Add licensed basemap/satellite/environmental overlays only after entitlement review.
3. Add asynchronous large-export jobs and object-storage delivery.
4. Add organization-specific persisted risk methodology ownership if tenants require private risk histories rather than platform-global assessments.
5. Add external AI model adapter only after provider data-retention/privacy terms are approved; keep citation enforcement and human publication review mandatory.
6. Expand verified mine-to-refinery/manufacturing relationship ingestion as evidence becomes available.
7. Add deployment-specific monitoring/APM integration and managed backup provider hooks.

## Validation status

The repository contains an isolated service quality workflow for Prisma validation, migration diffing, OpenAPI, lint, typecheck, Vitest, Next production build, Playwright, accessibility, and disposable PostGIS/Redis integration.

During implementation, GitHub Actions jobs in this repository terminated before the Checkout step with zero executed job steps and no downloadable job log. Local package installation was also unavailable because the execution environment could not resolve the configured network proxy. Therefore this manifest does **not** claim a successful hosted or local dependency/build test run. The source, schema, migration, API contracts, and tests were reviewed and hardened directly in the repository, and the CI gate remains committed to execute when repository runner infrastructure is functioning.

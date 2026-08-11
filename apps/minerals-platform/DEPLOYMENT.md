# Minerals Platform Deployment Guide

The authenticated service is not a GitHub Pages workload. Deploy it to infrastructure that supports long-running Node.js processes, PostgreSQL/PostGIS, Redis, background workers, TLS, private networking, and a trusted identity gateway.

## Release artifacts

Deploy the same Git commit to two process types:

- Web: `npm run start`
- Ingestion worker: `npm run worker`

Both use the same Prisma schema and environment contract.

## Provisioning

1. PostgreSQL 16 with PostGIS enabled.
2. Redis 7 or compatible managed Redis.
3. Secret manager entries from `.env.example`.
4. OIDC/SAML-capable ingress with MFA and header sanitization.
5. Optional SMTP, Slack, Teams, webhook, market/trade/news/geospatial provider secrets.
6. Monitoring for web health, database saturation, Redis/queue lag, worker failures, source staleness, and alert-delivery failures.

## Build

```bash
cd apps/minerals-platform
npm install
npm run db:generate
npm run lint
npm run typecheck
npm test
npm run build
```

## Database release

Enable required extensions before the first schema migration:

```bash
npx prisma db execute --file prisma/init.sql --schema prisma/schema.prisma
npm run db:migrate
npm run db:seed
```

Never run development `db push` against production. CI may use `db push` only against its disposable test database.

## Identity gateway

Production ingress must:

- terminate TLS
- authenticate through OAuth/OIDC or SAML
- enforce organization MFA policy
- remove inbound `x-cg-user-id`, `x-cg-org-id`, `x-cg-role`, `x-cg-subject`
- inject those headers only from verified identity claims
- block direct access to the application origin

Set `AUTH_MODE=production` only after this boundary is active.

## Rollout

1. Back up the database and record restore point.
2. Apply migrations.
3. Deploy web and worker release.
4. Verify `GET /api/v1/health`.
5. Verify Viewer, Analyst, Senior Analyst, Data Steward and Administrator authorization paths.
6. Verify source registry and one non-forced ingestion job.
7. Verify one non-sensitive alert-delivery test.
8. Confirm no demo data exists in production tables.
9. Confirm audit entries for ingestion, export, risk/report actions.
10. Shift traffic gradually if the platform supports staged rollout.

## Rollback

Application rollback is safe only when the previous release is compatible with the current schema. Do not improvise destructive reverse migrations. If schema rollback is required, restore from the pre-release recovery point after preserving audit/provenance evidence created during the failed release.

## Post-deploy acceptance

- health endpoint returns 200
- source-health SSE connects
- map endpoint returns valid GeoJSON even when empty
- market endpoint preserves empty state when no licensed series exists
- exports enforce role and row caps
- AI-generated report cannot publish before review
- ingestion TTL prevents repeated provider refreshes
- stale/offline provider status remains visible
- no secrets are present in client bundles or logs

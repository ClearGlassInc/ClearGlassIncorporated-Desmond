# Minerals Platform Operator Runbook

## Daily checks

- `GET /api/v1/health` returns healthy database state.
- Data Sources view shows last success, last attempt, freshness status, license, and latest ingestion run.
- Failed/stale sources have an owner and remediation note.
- Open critical/high alerts are acknowledged or assigned.
- Worker failure/retry counts remain within provider expectations.
- No demo data appears in verified production views.

## Start local stack

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

Separate terminal:

```bash
npm run worker
```

## Source refresh

Use `POST /api/v1/ingestion` with Data Steward credentials:

```json
{"sourceKey":"production","force":false}
```

A 429 `SOURCE_TTL` response is expected when the source is still inside its configured refresh interval. Use `force:true` only for a documented operational reason and within provider limits.

## Failed ingestion

1. Check the `IngestionRun.error` and transformation log.
2. Confirm provider availability, credentials, license, and rate limits.
3. Do not relabel the source as live manually.
4. Correct adapter/schema mapping if the provider changed its payload.
5. Retry after the provider backoff window.
6. Confirm provenance and record counts before closing the incident.

## Stale data

Treat stale/delayed state as a data-quality condition, not a UI defect. Keep the last valid observation with its timestamp if licensing permits, show stale status, and do not substitute demo values.

## Risk override

Only Senior Analysts may override a calculated score. Require a written reason. Review the audit record and supporting evidence during the next risk-governance review.

## Alert workflow

OPEN → ACKNOWLEDGED / ASSIGNED → RESOLVED. SUPPRESSED is reserved for documented false-positive or policy decisions. Comments are stored as analyst annotations and retained with the organization record.

Before external delivery, verify destination and sensitivity. Deliver through email, Slack, Teams, or webhook only after connector configuration is tested.

## Report publication

AI-assisted reports remain DRAFT until a Senior Analyst records REVIEW. Publication is blocked when `generatedByAi=true` and `reviewedAt` is empty.

## Backup/restore

- Verify managed PostgreSQL backup success daily.
- Perform a quarterly point-in-time restore test to an isolated environment.
- After restore: run migrations, integrity queries, application health, source registry checks, and representative map/risk/report queries.
- Record measured RPO/RTO and discrepancies.

## Deployment

1. CI must pass schema validation, OpenAPI check, lint, typecheck, unit tests, build, and Playwright smoke/accessibility gates.
2. Apply database migrations before switching web/worker traffic to the new release.
3. Deploy web and worker from the same commit SHA.
4. Verify `/api/v1/health` and authentication boundary.
5. Run one authorized source refresh and one non-sensitive alert delivery test.
6. Roll back application code only if schema remains backward compatible; otherwise use the documented database recovery path.

## Security incident

Disable affected connector/secrets, preserve audit data, rotate credentials, validate identity-gateway policy, review exports and ingestion runs, then restore services incrementally. Never destroy evidence as a containment shortcut.

# ClearGlass Engineering Controller

Isolated GitHub App control plane for ClearGlass. This subtree does not modify the static website, commerce runtime, existing workflows, or production branch behavior.

## Safety model

- Fails closed when GitHub App credentials, webhook secret, or admin credential are missing.
- Verifies GitHub webhook HMAC signatures before parsing or processing payloads.
- Deduplicates webhook deliveries by `X-GitHub-Delivery`.
- Restricts repository operations to `GITHUB_ALLOWED_ORG`.
- Uses short-lived GitHub App installation tokens.
- Requires a separate admin bearer credential for controller endpoints.
- Requires a create → approve → consume flow before workflow dispatches and deployments.
- Records append-only audit events without persisting secret values.
- Uses bounded outbound request timeouts and refuses oversized webhook payloads.

## Runtime

Python 3.11 is used to match the monorepo engineering contract.

The service exposes health/readiness endpoints, GitHub webhook ingestion, installation discovery, Actions status reads, branch and draft pull-request creation, governed workflow dispatch, governed deployment creation, and audit inspection.

## Required runtime configuration

Copy `.env.example` into your platform's secret/configuration system. Never commit populated credentials.

Required secrets:

- `GITHUB_APP_ID`
- `GITHUB_PRIVATE_KEY`
- `GITHUB_WEBHOOK_SECRET`
- `ADMIN_API_KEY`

`GITHUB_PRIVATE_KEY` may be provided with literal `\n` sequences; the controller normalizes them at runtime.

## GitHub App permissions

Grant only what the deployed controller uses. Start with repository metadata read, contents read/write, pull requests read/write, actions read/write, workflows read/write, and deployments read/write. Avoid organization or enterprise write permissions unless a concrete controller capability requires them.

## Webhook

Point the GitHub App webhook URL at the deployed service's `/github/webhook` route. Keep webhook delivery disabled until the HTTPS deployment exists and the matching `GITHUB_WEBHOOK_SECRET` is stored in the runtime secret manager.

Webhook reception is intentionally non-mutating: incoming events are verified, deduplicated, scoped, and audited. They do not automatically trigger repository writes.

## Deployment

Deploy this subtree independently from the GitHub Pages site. The container listens on port 8000 and persists SQLite under `./data` for development. For production, place the persistent data directory on durable storage or replace the store with PostgreSQL before relying on it for long-term audit retention.

## Operational gate

Do not merge this PR merely because the files exist. Validate the isolated controller in its own runtime first, configure secrets outside Git, install the GitHub App on selected repositories, verify `/ready`, send a test webhook, and exercise only a non-production repository before enabling production write permissions.

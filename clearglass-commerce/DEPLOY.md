# Deploying the ClearGlass Commerce store

The control plane is a stateless FastAPI container + a Postgres database. The storefront and
admin are Next.js apps. Below are three paths — pick one.

## A. Render (one blueprint, recommended)

`render.yaml` in this folder provisions the API **and** a managed Postgres 16 database.

1. Push this repo to GitHub.
2. Render → **New +** → **Blueprint** → select the repo.
3. After the first deploy, open the `clearglass-commerce-api` service → **Environment** and set the
   `sync:false` secrets: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PUBLISHABLE_KEY`.
4. The service exposes `GET /health`; Render uses it for health checks.
5. Point a Stripe webhook at `https://<your-service>.onrender.com/webhooks/stripe` and paste the
   signing secret into `STRIPE_WEBHOOK_SECRET`.

The blueprint deploys **all three services** — API, storefront, admin — plus the database.

`AUTO_CREATE_TABLES=true` creates the schema on first boot. For production hardening, switch it
off and apply `control-plane/migrations/001_init.sql` (it adds the append-only ledger trigger).

### Continuous deploy (GitHub Actions)

`.github/workflows/commerce-deploy.yml` runs on every push to `main` that touches
`clearglass-commerce/**`: it gates on `ruff` + the test suite, then triggers a Render deploy via a
**Deploy Hook**. To enable it:

1. Render → your API service → **Settings** → **Deploy Hook** → copy the URL.
2. GitHub → repo **Settings** → **Secrets and variables** → **Actions** → add
   `RENDER_DEPLOY_HOOK_URL`.

Without the secret the deploy step is skipped (the test gate still runs), so the workflow is safe
to merge before you have a Render account.

## B. Docker Compose (self-host / VPS)

```bash
cp .env.example .env          # fill DATABASE_URL + STRIPE_* (or leave blank for mock mode)
docker compose up --build     # db + api(:8000) + storefront(:3000) + admin(:3001)
docker compose exec db psql -U commerce -d commerce -f /migrations/001_init.sql
```

## C. Fly.io (API only)

```bash
fly launch --dockerfile clearglass-commerce/control-plane/Dockerfile --no-deploy
fly postgres create && fly postgres attach <db>     # sets DATABASE_URL
fly secrets set STRIPE_SECRET_KEY=... STRIPE_WEBHOOK_SECRET=...
fly deploy
```

## Verify a live deploy

```bash
BASE=https://<your-host>
curl $BASE/health
# customer purchase (mock unless a live Stripe key is set):
curl -X POST $BASE/checkout/session -H 'Content-Type: application/json' \
  -d '{"items":[{"name":"Aurora Lamp","amount":4900,"quantity":1}],"customer_email":"a@b.com"}'
# a pricing change is gated — returns queued_for_approval, never executes inline:
curl -X POST $BASE/store/update-pricing -H 'Content-Type: application/json' \
  -d '{"sku":"AURORA-STD","old_price":49,"new_price":59}'
curl "$BASE/approvals?status=pending"
curl "$BASE/events?limit=20"
```

## Going from mock to real money

The store runs in **mock mode** with no Stripe key (safe for demos). To take real payments:
1. Add `STRIPE_SECRET_KEY` (live or test) → `/checkout/session` creates real Stripe Checkout URLs.
2. Add `STRIPE_WEBHOOK_SECRET` → `/webhooks/stripe` verifies signatures and rejects forgeries.
3. Refunds stay behind the approval gate; approve via `/approvals/{id}/approve` before any money moves.

## Morning sales-ops briefing (email)

`.github/workflows/sales-ops-briefing.yml` runs every morning (≈07:17 ET), builds a factual
briefing from the control-plane database — yesterday + month-to-date revenue, run-rate forecast
movement, new/stalled/at-risk orders, operator activity, and data-quality/approval-gate issues —
then emails it via Gmail SMTP. Build it manually any time with:

```bash
cd control-plane
python -m app.sales_ops_briefing            # markdown to stdout
python -m app.sales_ops_briefing --json     # machine-readable
python -m app.sales_ops_briefing --email    # also email (needs the secrets below)
```

Add these repo **Actions secrets** to send real numbers (without them it runs in safe mode: a
clearly-marked "no live source" briefing, no email, no fabricated figures):

| Secret | Purpose |
|--------|---------|
| `DATABASE_URL` | Control-plane Postgres URL (read-only use by the briefing) |
| `GMAIL_USER` | Sending Gmail address |
| `GMAIL_APP_PASSWORD` | Gmail **App Password** (requires 2FA; not your account password) |
| `BRIEFING_TO` | Recipient(s), comma-separated (defaults to `GMAIL_USER`) |

> Coverage note: the source is commerce/Stripe, **not a deal CRM**. "Deals" map to orders and
> "rep activity" maps to operator/automation ledger activity. For true rep-level pipeline,
> forecast, and stage data, connect a CRM (HubSpot/Salesforce) as the source instead.

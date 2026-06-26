# CLAUDE.md

Guidance for agents working in this repository.

## What this repo is

`ClearGlassInc.github.io` is the ClearGlass Inc. GitHub Pages site **plus** the
source for several backend systems that ship from the same monorepo. The root is
a large static marketing/product site (many top-level `*.html` pages, shared
`*.css`/`*.js`, `assets/`, `sitemap.xml`). Backend systems live in their own
subtrees and deploy independently.

The flagship backend is the **Autonomous E‑Commerce Operator** in
`clearglass-commerce/` — a *governed* commerce engine. Treat its safety model
(below) as non‑negotiable when changing it.

## Map of the repo

| Path | What it is |
|------|-----------|
| `*.html`, `*.css`, `*.js` (root) | Static GitHub Pages site (product/landing pages, shared UI) |
| `clearglass-commerce/` | **Active** governed e‑commerce OS: FastAPI control plane + Next.js storefront/admin + agent prompts |
| `apps/autostore/` | Earlier/parallel control plane + cockpit. Appears superseded by `clearglass-commerce/` — confirm before extending it |
| `agents/` | Per‑agent definitions (`agent.json`, `system_prompt.md`, tool schemas) |
| `bots/` | Standalone Python automation bots invoked by workflows (e.g. `store_smoke_bot.py`) |
| `data/` | Committed JSON feeds: `data/store/catalog.json`, `data/control-surface/*` |
| `operations/` | Generated reports + handoff pages (priority matrix, SEO, health, defender) |
| `.github/workflows/` | ~29 workflows: CI, Pages deploy, commerce gates, scheduled bot loops |

## The commerce OS safety model (read before touching `clearglass-commerce/`)

Core invariant: **read‑only analysis → draft → human approval → execution.**
`control-plane/app/governance.py` scores every proposed action 0–100 and routes it:

- **low** (generate copy, read metrics, reconcile) → auto‑execute + log
- **medium** (content publish, non‑price catalog edits) → queue approval
- **high / critical** (pricing, payment/tax/refund/fulfillment, reorders, mass
  outbound) → **blocked until an `approvals` row reaches `approved`**

Every material change is written to an append‑only audit ledger (`events` table,
`app/audit.py`) with a risk score. Do not add a code path that lets a
high/critical action execute without an approval — `daily_loop.py`'s governance
self‑check (and `tests/test_governance.py`) will fail if you do, by design.

Operating rules also enforced in code/prompt: never fabricate inventory, reviews,
sales, or urgency; never change live pricing/tax/payment/refund/fulfillment
without approval; log every action.

## Running & testing the commerce control plane

```bash
cd clearglass-commerce/control-plane
pip install -r requirements.txt        # fastapi, sqlalchemy, stripe, httpx (TestClient), …
ruff check .                           # lint (must pass)
python -m pytest tests/ -q             # 21 tests; payout tests need the full web stack
uvicorn app.main:app --reload          # http://localhost:8000/docs
python -m app.daily_loop --json        # governance self-check + executive report (stdlib only)
```

Note: `requirements.txt` pins `httpx` because `fastapi.testclient.TestClient`
needs it. Without it the webhook → DB → `/payouts` integration tests **silently
skip** (or error at collection on envs that have fastapi but not httpx) — so the
governed money‑movement paths would go unexercised. The `Commerce Deploy`
workflow installs `requirements.txt` for the same reason.

Storefront / admin (Next.js, deploy independently):

```bash
cd clearglass-commerce/storefront   # or admin
npm ci && npm run build             # Commerce Frontend CI runs tsc --noEmit + next build
```

Full stack via Docker: `cd clearglass-commerce && docker compose up --build`
(postgres + control‑plane :8000 + storefront :3000 + admin :3001). Deploy paths
are documented in `clearglass-commerce/DEPLOY.md` (Render blueprint recommended).

## CI gates that must stay green

- **Commerce Deploy** (`commerce-deploy.yml`): `ruff` + full pytest on
  `clearglass-commerce/**`, then optional Render deploy hook.
- **Commerce Frontend CI** (`commerce-frontend-ci.yml`): `tsc --noEmit` +
  `next build` for storefront and admin.
- **Commerce Daily Loop** (`commerce-daily-loop.yml`): storefront smoke test +
  governance self‑check + executive report (scheduled 13:00 UTC).

## Conventions

- Match the style of surrounding code; the commerce control plane is typed
  Python with stdlib‑only modules where noted (`governance.py`, `daily_loop.py`,
  parts of `payments.py`) so they run in minimal CI environments — keep them that
  way unless you also update the relevant gate.
- Don't commit secrets. Stripe keys are runtime env vars; the store runs in safe
  **mock mode** with no key.
- Static site changes deploy via GitHub Pages; keep `.nojekyll` and existing
  redirect/header files intact.

# ClearGlass Side Store — Storefront

Minimal **Next.js + Stripe Checkout** storefront for the cheap-wires-and-electronics
side store. It's the customer-facing counterpart to the `apps/autostore/cockpit`
(admin) and `apps/autostore/control_plane` (Python control plane), governed by the
agent spec in `agents/clearglass_side_store/SOUL.md`.

## What's real today

- **`data/catalog.json`** — 57 seed SKUs, all CAD ≤ $10, across 8 categories.
- **`lib/pricing.mjs`** — pure pricing engine (bundle discount ≤15%, free shipping
  over $25, Ontario HST). Dependency-free; shared by the app and the tests.
- **`lib/checkout.mjs`** — builds Stripe Checkout session params (pure, secret-free).
- **`lib/store.test.mjs`** — `node --test` smoke suite (8 tests). Also run by the
  repo's pytest CI via `tests/test_side_store_storefront.py`, so the pricing core is
  verified on every build.
- **`app/`** — a minimal storefront page + a `/api/checkout` route.

## What needs setup before it can take a payment

1. `npm install` inside this folder (pulls `next`, `react`, `stripe`).
2. A Stripe account; copy `.env.example` → `.env.local` and set `STRIPE_SECRET_KEY`.
3. `npm run dev` (port 3001).

Without `STRIPE_SECRET_KEY` the checkout route **fails closed** with HTTP 503 — no
payment path is silently half-wired.

## Run the tests

```bash
# from the repo root — runs in CI via pytest
node --test apps/autostore/storefront/lib/store.test.mjs
```

## Relationship to the live site

The static, GitHub-Pages-served storefront at `/side-store.html` (repo root) renders
the **same** `catalog.json` with the **same** pricing rules for browsing and cart
math. This Next.js app is the server-backed version that adds real Stripe Checkout
once accounts and secrets exist. Payments, billing, and personal data are Tier 3:
human-approved, audited, reversible (see the SOUL).

---

*ClearGlass Inc. · Burlington, Ontario · Clarity Is Power*

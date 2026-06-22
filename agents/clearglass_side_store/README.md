# ClearGlass Side Store Agent

A production-grade **agent specification** for an autonomous, low-cost
wires-and-electronics storefront. This folder is the **instruction + scaffold
layer** — it defines how the agent should think and behave. It is **not** a
running store and does not move money on its own.

## What's here

| File | Purpose |
|---|---|
| `SOUL.md` | The agent's soul: identity, mission, skills, hard constraints, cadence, output contract. |
| `agent.json` | Machine-readable config (pricing, constraints, deployment tiers, integration status). |
| `agentic-workflow.template.yml` | A GitHub Actions **template** — reference only, intentionally not in `.github/workflows/`. |
| `README.md` | This file. |

## Real today vs. needs setup

**Real today (committed artifacts):**
- The SOUL spec, the machine-readable config, and the workflow template.
- A coherent, internally-consistent ruleset an operator (or a future runtime)
  can follow.

**Needs accounts, credentials, and human setup before anything executes:**
- A Shopify-compatible catalog and a deployed Next.js storefront.
- Stripe (payments), and `STRIPE_API_KEY` / `SHOPIFY_API_KEY` in GitHub Secrets.
- Real, human-approved suppliers and funding for inventory.
- Social / email / SMS accounts and tokens for marketing.

Until those exist, the workflow template stays out of `.github/workflows/`. If it
ran now it would fail on every tick and waste Actions minutes.

## Two deliberate corrections to the original brief

1. **Discount contradiction resolved.** The brief listed both *"never discount
   more than 15% without approval"* and a *"50% off first 10 orders"* launch
   promo. Those conflict. The default launch offer is now **15% off the first
   order + free shipping over $25** (within policy). A deeper promo is allowed
   only as an **explicit, time-boxed, budget-capped owner-approval exception** —
   never autonomous.
2. **Revenue target is a goal, not a promise.** "$1,000 in 14 days" is framed as
   a target that guides prioritisation. The agent optimises the controllable
   inputs (SKUs, listings, bundles, uptime, response time) and reports honestly
   when results diverge.

## Safety posture

Anything that touches **payments, billing, or personal data is Tier 3**:
human-approved, audited, and reversible — no autonomous merge. Marketing is
**consent-first (CASL)**: consent on file, sender identified, one-click
unsubscribe honoured. Secrets live only in GitHub Secrets with least-privilege
tokens.

## Next step (opt-in)

When you're ready to make it real, the natural follow-on is a minimal
**Next.js + Stripe Checkout** storefront skeleton with a seed catalog and a
checkout smoke test — built once real accounts and secrets exist so it can be
verified end-to-end rather than scaffolded blind.

---

*ClearGlass Inc. · Burlington, Ontario · Clarity Is Power*

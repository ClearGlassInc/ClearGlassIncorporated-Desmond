# ClearGlass BLACKGLASS-OMEGA Verification Contract

This document records the additive verification controls introduced on 2026-08-10.

## Invariants

- Existing routes, content, products, Stripe integration, analytics, and Pages behavior remain intact.
- Primary CI validates both Python and Node/TypeScript tooling.
- Node dependencies are installed from the committed lockfile with `npm ci`.
- TypeScript type checking, Stripe-sync unit tests, and the deterministic tooling build are required CI gates.
- Pages deployment keeps build authority separate from deployment authority.
- Production verification runs only after the Pages deploy job succeeds.
- The production probe reads the canonical host from `CNAME`, checks the homepage, `robots.txt`, `sitemap.xml`, and a bounded deterministic sample of same-origin sitemap URLs.
- Production checks use bounded retries and fail closed on unreachable or non-successful routes.
- Production verification emits a JSON evidence artifact without credentials or secret values.
- Repository-health controls treat the production probe as a critical deployment dependency.
- No branch protection, authentication, secret scanning, or GitHub authorization control is bypassed.

## Evidence states

`CODE PATCHED` is not equivalent to `WORKFLOW PASSED`.

`WORKFLOW PASSED` is not equivalent to `DEPLOYMENT COMPLETED`.

`DEPLOYMENT COMPLETED` is not equivalent to `PRODUCTION VERIFIED`.

Each state requires its own evidence before it can be reported as complete.

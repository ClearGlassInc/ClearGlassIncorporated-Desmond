# Repository Secrets

This document lists every GitHub Actions secret referenced by the workflows in
`.github/workflows/`, what it is for, and whether it is **required** for core
operation or **optional** (a feature degrades gracefully / is skipped when it is
absent).

> **Core GitHub Pages deployment requires no secrets.** The `Deploy GitHub
> Pages` workflow (`pages.yml`) runs entirely on the automatic `GITHUB_TOKEN`.
> Everything below is for backend systems, bots, and integrations that deploy
> independently.

No secret values are committed to this repository — a supply-chain scan
(`grep` for API-key / private-key patterns) returns clean. Secrets are injected
at runtime only via `${{ secrets.* }}`.

## Never commit secrets

- All keys are runtime environment variables supplied by GitHub Actions secrets.
- The commerce store runs in safe **mock mode** with no Stripe key present.
- If you add a new integration, add a placeholder row here and reference it as
  `${{ secrets.NAME }}` — never inline a literal value.

## Required (only if you use the associated system)

| Secret | Used by | Purpose | Missing behaviour |
|---|---|---|---|
| `GITHUB_TOKEN` | all workflows | Automatic token GitHub provides per run | Always present; no action needed |
| `DATABASE_URL` | `commerce-deploy.yml` | Postgres connection for the commerce control plane | Control-plane deploy/tests that need a DB fail |
| `CONTROL_PLANE_URL` | `commerce-daily-loop.yml` | Base URL of the deployed control plane for the daily loop | Daily loop cannot reach the API |
| `ANTHROPIC_API_KEY` / `CLAUDE_CODE_OAUTH_TOKEN` | `agent.yml` | Auth for the Claude Code agent action | Agent workflow cannot run |

## Optional (guarded — workflow skips or warns when absent)

| Secret | Used by | Purpose | Missing behaviour |
|---|---|---|---|
| `PAGES_ADMIN_TOKEN` | `pages.yml` | Admin-scoped PAT to pin the Pages source to "GitHub Actions" | Step is `continue-on-error`; a 403 is logged as a warning and never blocks the real deploy |
| `RENDER_DEPLOY_HOOK_URL` | `commerce-deploy.yml` | Render deploy hook to trigger a backend deploy | Deploy step is skipped; CI (ruff + pytest) still runs |
| `RENDER_ROLLBACK_HOOK_URL` | rollback flow | Render rollback hook (see `rollback.md`) | Manual rollback via Render dashboard instead |
| `OPENAI_API_KEY` | AI-assisted bot workflows | Optional model provider | Bot skips the enrichment step |
| `CG_ORG_PAT` | multi-repo audit / cross-repo actions | Read access across ClearGlass org repos | Cross-repo audit limited to this repo |
| `GMAIL_USER`, `GMAIL_APP_PASSWORD` | briefing / outreach workflows | SMTP send for scheduled briefings | Email send skipped; report still generated |
| `BRIEFING_TO` | `sales-ops-briefing.yml` | Recipient address for the sales-ops briefing | Briefing not emailed |
| `DEFENDER_SLACK_WEBHOOK_URL`, `DEFENDER_DISCORD_WEBHOOK_URL` | `defender-watch.yml` | Alert delivery for the defender watch | Alerts logged to run output only |
| `AUDIT_VALID_TOKEN`, `AUDIT_LOW_PRIV_TOKEN`, `AUDIT_OTHER_USER_ID` | access-control audit | Fixtures for the access-control audit test | Those audit assertions are skipped |

## Setting a secret

Repository → **Settings → Secrets and variables → Actions → New repository
secret**. Use the exact name from the tables above. For org-wide secrets
(`CG_ORG_PAT`), set them at the organization level and grant this repository
access.

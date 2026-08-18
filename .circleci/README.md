# ClearGlass Secure Orchestration Pipeline (CircleCI)

One **manually-triggered** pipeline (`.circleci/config.yml`, CircleCI 2.1) that
validates and — only on explicit request plus human approval — deploys the
approved automation components: GitHub-workflow integrations, application
automations, frontend/animation assets, and AI/agent services.

> **Guarantee:** this pipeline never bypasses GitHub branch protection, required
> status checks, environment approvals, repository rulesets, protected secrets,
> or deployment gates. It only **reads/validates** GitHub workflow files — it
> never triggers, reruns, cancels, approves, merges, or edits GitHub Actions or
> org settings, and it holds no write-scoped GitHub token.

---

## 1. Trigger parameters

Every deploy/mutation parameter **defaults to `false`**. A normal push therefore
runs the read-only `validate` workflow **only** — deploy jobs cannot run just
because a commit landed.

| Parameter | Type | Default | Effect |
|-----------|------|---------|--------|
| `run_validation` | boolean | `true` | Runs the read-only `validate` workflow (jobs 1–7). |
| `run_github_automation_checks` | boolean | `false` | Deeper `.github/workflows` validation inside job 5. |
| `run_agent_health_checks` | boolean | `false` | Full sandbox agent contract/health probes in job 7. |
| `deploy_staging` | boolean | `false` | Requests a staging deploy (needs `target_environment=staging`). |
| `deploy_production` | boolean | `false` | Requests a production deploy (needs approval + authorized ref). |
| `enable_agents` | boolean | `false` | Enables agent activation paths (**never** in production via this pipeline). |
| `deploy_animations` | boolean | `false` | Requests publish of built animation assets (separate approval). |
| `emergency_stop` | boolean | `false` | **Global kill switch** — blocks every deploy/mutation/agent/GitHub-write action. |
| `target_environment` | enum `none\|staging\|production` | `none` | Must match the requested deploy. |

### How to trigger manually

- **CircleCI UI:** Project → **Trigger Pipeline** → add the parameters above.
- **API:**

  ```bash
  curl -X POST https://circleci.com/api/v2/project/gh/ClearGlassInc/ClearGlassIncorporated-Desmond/pipeline \
    -H "Circle-Token: $CIRCLECI_PERSONAL_TOKEN" \
    -H "content-type: application/json" \
    -d '{
      "branch": "main",
      "parameters": { "deploy_staging": true, "target_environment": "staging" }
    }'
  ```

  A `Circle-Token` is a **personal** API token — it is not a GitHub write
  credential and cannot approve or bypass GitHub gates.

---

## 2. Workflows & approval flow

| Workflow | Fires when | Jobs |
|----------|-----------|------|
| `validate` | `run_validation=true` (default) — PRs & branches | 1 preflight → 2 checkout/lockfile → 3 lint/typecheck/test → 4 dep+secret scan → 5 github validation → 6 animation build/smoke → 7 agent sandbox |
| `staging_release` | `deploy_staging=true` **and** `target_environment=staging` **and** `emergency_stop=false` | validate jobs 1–7 → **8 deploy_staging** → 11 post-deploy verify |
| `production_release` | `deploy_production=true` **and** `target_environment=production` **and** `emergency_stop=false`, from **`main` or a signed release tag** | validate jobs 1–7 → **9 hold_production (manual approval)** → **10 deploy_production** → 11 post-deploy verify |
| `external_production_verify` | `run_validation=true` | read-only reachability monitor of the live control plane (preserved from the prior config) |

> **Staging must run from a branch, not a tag**, and a production release from a
> tag must be a **GPG-signed** tag whose signer fingerprint matches the trusted
> key (see contexts below). `enable_agents` and `deploy_animations` are
> hard-blocked in preflight until their `REPLACE_ME` activation/deploy adapters
> are configured — they cannot be set true today.

**Production approval flow:**

1. Trigger with `deploy_production=true`, `target_environment=production`, from
   `main` or a `v*` release tag. A tag build additionally requires a valid
   **GPG signature** by the trusted signer.
2. `security_preflight` re-checks the ref and parameter combination — including
   `git verify-tag` against `TRUSTED_RELEASE_SIGNER_FINGERPRINT` — and fails
   closed on anything unauthorized.
3. Jobs 1–7 must all pass.
4. **`hold_production`** appears in the CircleCI UI. A human clicks **Approve**.
   Nothing production-facing runs before this.
5. `deploy_production` re-verifies authorization, deploys the **immutable**
   artifact pinned to the exact `CIRCLE_SHA1`, then runs health + smoke checks.
   Success is **not** claimed unless endpoint verification passes.
6. `post_deploy_verify` records version/health/flow/error-rate evidence as
   artifacts.

### Restricted contexts (credential scoping)

| Context | Used by | Holds |
|---------|---------|-------|
| `ci-readonly` | jobs 1–7 + external monitor | read-only tokens; `TRUSTED_RELEASE_SIGNER_FINGERPRINT` + `TRUSTED_RELEASE_SIGNER_PUBLIC_KEY_B64` (tag-signature verification). No deploy or GitHub-write secrets |
| `staging-deploy` | `deploy_staging`, staging verify | `RENDER_STAGING_DEPLOY_HOOK_URL`, `STAGING_BASE_URL`, `STAGING_LAST_GOOD_SHA` |
| `production-deploy` | `deploy_production`, prod verify — **post-approval only** | `RENDER_PRODUCTION_DEPLOY_HOOK_URL`, `PRODUCTION_BASE_URL`, `PRODUCTION_LAST_GOOD_SHA` |

Restrict each context to the appropriate security group in CircleCI Org
Settings so only authorized users can run staging/production workflows.

### `emergency_stop`

Set `emergency_stop=true` to halt everything: `security_preflight` fails if any
mutating parameter is also set, the workflow-level `when` blocks the deploy
workflows, and each mutating job carries a defense-in-depth guard step that
aborts independently.

---

## 3. Commands used (project-standard)

- **Python** (`pyproject.toml` / `requirements.txt`): `ruff check .`,
  `ruff format --check .`, `python -m pytest`.
- **Frontend/animations** (`clearglass-commerce/storefront`,
  npm + `package-lock.json`): `npm ci`, `npx tsc --noEmit`, `npm run build`.
- **GitHub workflow validation:** `python scripts/workflow_doctor.py` (dry-run).
- **Agent self-check:** `python -m app.daily_loop --json` (governed, stdlib).
- **Security policy gate:** `python scripts/ci/scan_policy_gate.py`.

Placeholders marked `REPLACE_ME` in `config.yml` (mypy target, smoke-test
command, deploy-hook URLs, base URLs, error-rate query) must be filled with your
real values / context secrets before enabling deploys.

---

## 4. Rollback procedures

Every deploy is an **immutable artifact pinned to a git SHA**, so rollback =
re-deploy the previous known-good SHA. Rollback commands are **idempotent** and
**logged** (stored as job artifacts).

### Staging rollback

- **Automatic:** if `deploy_staging` health checks fail, the job's `on_fail`
  step re-deploys `STAGING_LAST_GOOD_SHA` via the staging deploy hook.
- **Manual:**

  ```bash
  curl -fsS -X POST "${RENDER_STAGING_DEPLOY_HOOK_URL}&ref=<LAST_GOOD_SHA>" -o /dev/null
  ```

  or use Render → staging service → **Rollback** to the previous deploy.

### Production rollback

- **Automatic:** if `deploy_production` verification fails, the job's `on_fail`
  step re-deploys `PRODUCTION_LAST_GOOD_SHA`.
- **Manual (preferred, audited):**
  1. Render → production service → **Rollback** → select the previous
     green release, **or**
  2. Re-run `production_release` with `deploy_production=true`,
     `target_environment=production` from the last known-good tag/commit and
     approve `hold_production`.

  ```bash
  curl -fsS -X POST "${RENDER_PRODUCTION_DEPLOY_HOOK_URL}&ref=<LAST_GOOD_SHA>" -o /dev/null
  ```

Set `STAGING_LAST_GOOD_SHA` / `PRODUCTION_LAST_GOOD_SHA` in the corresponding
context after each successful release so automatic rollback has a target.

> Rollback does **not** delete data or rotate secrets. Database/schema changes
> must ship behind backward-compatible migrations; a code rollback must remain
> safe against the already-migrated schema.

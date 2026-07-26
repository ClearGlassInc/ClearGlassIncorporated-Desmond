# GitHub Actions Remediation Report

**Scope:** all workflow files under `.github/workflows/`  
**Audit mode:** offline, non-executing, fail-closed source inspection  
**Rollback:** revert the remediation commit; no workflow was remotely dispatched and no deployment was performed.

## Executive decision

The repository contains 51 workflows. YAML parsing, local references, full-SHA action pinning, explicit permissions, job timeouts, deployment dependencies, secrets interpolation, artifact/cache declarations, environments, and recognizable deployment targets were inspected by `scripts/audit_github_actions.py`. The inventory below is generated from the checked-in workflow source.

Two least-privilege defects were patched immediately: the daily and weekly organic issue workflows requested `contents: write` although they only read the checkout, and both suppressed issue-creation failures. They now use `contents: read` and fail visibly if the promised issue is not created.

No remote workflow was executed. The source audit found unattended write paths and one production deployment path that require repository governance evidence unavailable in a checkout. Those workflows remain blocked from operator execution until an administrator verifies or adds protected environments and required reviewers.

## Apply fixes in this order

1. **Merged in this change:** least-privilege and fail-fast fixes for `organic-daily.yml` and `organic-weekly-review.yml`.
2. **Before any production commerce run:** bind the `commerce-deploy.yml` deploy job to a protected `production` environment with required reviewers, branch restrictions, and a documented Render rollback owner.
3. **Before unattended writer runs:** route `artemis-deploy.yml`, `bot-orchestrator.yml`, `clearglassinc-military-op.yml`, `content-pipeline.yml`, `control-surface-feeds.yml`, `dependency-updater.yml`, and `workflow-doctor.yml` writes through pull requests or protected approval environments. Do not allow direct scheduled pushes to a protected branch.
4. **Repository-admin verification:** confirm environment rules, Actions allowlist policy, branch protection, secret presence/rotation ownership, and Pages source = GitHub Actions. These settings cannot be proven offline.
5. Execute read-only validation workflows first; execute Pages only after its build artifact is inspected; execute production workflows only after the governance items above are closed.

## Exact remediation for blocked workflows

| Workflow | Blocked reason | Exact remediation |
|---|---|---|
| `artemis-deploy.yml` | Scheduled job can commit/push provenance without an approval boundary. | Replace direct push with a pull request, or split proposal and promotion jobs and bind promotion to a protected environment with required reviewers. |
| `auto-store.yml` | The rollback job can invoke a production rollback hook outside the `production` environment boundary. | Bind rollback to a separately protected break-glass environment, restrict the rollback secret to that environment, and document/test expedited incident approval. |
| `bot-orchestrator.yml` | Scheduled bot run has `contents: write` and pushes generated output directly. | Keep generation read-only, upload outputs as artifacts, then use a separately approved promotion job/PR. Make push failure fatal rather than warning-only. |
| `clearglassinc-military-op.yml` | Scheduled release/provenance path can push repository content. | Remove scheduled write authority; publish a candidate artifact and require an environment-approved promotion job. |
| `commerce-deploy.yml` | Render deploy hook runs without a GitHub Environment binding or checkout-verifiable approval gate. | Add `environment: production`, configure required reviewers/branch policy, add post-deploy health verification, and configure/test the rollback hook before execution. |
| `content-pipeline.yml` | `workflow_run` can push generated content directly after another automation run. | Download and validate the producing run's immutable artifact, verify its digest/path allowlist, and open a PR instead of pushing to the protected branch. |
| `control-surface-feeds.yml` | Scheduled feed publisher can commit/push and dispatch Pages without approval. | Open a feed-update PR; let the normal protected-branch merge trigger the validated Pages build/deploy chain. |
| `dependency-updater.yml` | Scheduled dependency updater can push directly. | Use Dependabot or create a signed, review-required PR with lockfile tests; remove direct protected-branch writes. |
| `release-supply-chain.yml` | Reusable release job can publish a GHCR image without an environment approval boundary. | Bind publication to a protected `release` environment, restrict callers and branches, and retain attestations plus the prior image digest for rollback. |
| `workflow-doctor.yml` | Scheduled repair has write authority and force-pushes a fixed branch. | Retain PR-only remediation, remove force-push or constrain it with lease, bind the repair job to an automation environment, and require CODEOWNERS review for workflow changes. |

## Validation and rollout runbook

### Local/source gate

1. Run `python scripts/audit_github_actions.py`; any `ERROR` is a hard stop.
2. Run `python scripts/audit_github_actions.py --markdown` and review inventory drift.
3. Run `python -m pytest tests/test_audit_github_actions.py -q`.
4. Run `python scripts/workflow_doctor.py`; apply no automatic repair without reviewing its diff.
5. Run `git diff --check` and inspect every workflow diff.

### GitHub validation (authorized operator)

1. Open a pull request and require `CI`, `Security`, policy gates, and relevant commerce gates to pass.
2. Confirm repository Actions policy permits only the SHA-pinned actions in the inventory.
3. Confirm `production` and `github-pages` environments have intended reviewers and branch rules.
4. Dispatch only read-only/manual validation workflows first. Capture run URL, actor, source SHA, inputs, job logs, artifact names/digests, and conclusion.
5. For Pages, inspect the `github-pages` artifact from the build job, then approve deployment. Verify the deployed URL and retain the prior successful deployment as rollback anchor.
6. For Render, verify the release SHA, approve the environment, monitor readiness and functional checks, and roll back to the last green release on any invariant failure.

### Post-deployment monitoring

Monitor failed/skipped gates, environment approvals, unexpected token permission elevation, artifact digest/path changes, Pages deployment URL/HTTP status, Render readiness and checkout health, rollback invocation, bot-created commits/issues, and repeated retry/warning patterns. Alert on any direct protected-branch push by automation or deployment without a corresponding approved environment record.

### Weekly health check

Run the offline audit and workflow doctor; review action SHA drift and upstream security advisories; audit environment/branch protection and token permissions; inspect secret age/ownership without exposing values; sample artifacts and retention; review scheduled-run failure rate/duration; test a non-production rollback; and reconcile workflow inventory against CODEOWNERS and deployment ownership.

## Workflow inventory

The table maps triggers, permissions, referenced secret names (never values), jobs, artifact/cache use, environment bindings, deployment targets, status, and exact source-verifiable risk. “Valid and ready” means **source-valid**; it does not attest that remote secrets or GitHub settings exist.

| Workflow | Status | Triggers | Permissions | Secrets | Jobs | Artifacts / caches | Environments | Targets | Exact risk |
|---|---|---|---|---|---|---|---|---|---|
| `agent-army-crypto.yml` | valid and ready | pull_request, push, workflow_dispatch | contents | none | secure-runtime | 0 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `agent-army.yml` | valid and ready | pull_request, push, workflow_dispatch | contents | none | validate | 0 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `agent-deployer.yml` | valid and ready | workflow_call, workflow_dispatch | contents | none | run | 0 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `agent-os.yml` | valid and ready | schedule, pull_request, workflow_dispatch | contents | none | self-check | 0 artifact step(s); cache: self-check:pip | none | none | No source-verifiable failure risk found. |
| `agent.yml` | valid and ready | workflow_dispatch | contents | ANTHROPIC_API_KEY, CLAUDE_CODE_OAUTH_TOKEN, GITHUB_TOKEN | repair | 0 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `api-security-audit.yml` | valid and ready | schedule, workflow_dispatch | contents, security-events, issues | AUDIT_LOW_PRIV_TOKEN, AUDIT_OTHER_USER_ID, AUDIT_VALID_TOKEN | api-security-audit | 2 artifact step(s); cache: none | staging | none | No source-verifiable failure risk found. |
| `artemis-browser.yml` | valid and ready | push, pull_request, workflow_dispatch | contents | none | browser-assistant | 0 artifact step(s); cache: browser-assistant:pip, browser-assistant:npm | none | none | No source-verifiable failure risk found. |
| `artemis-deploy.yml` | unsafe and requiring governance changes before execution | push, schedule, workflow_dispatch | contents | none | validate, ip-guardian-gate, provenance | 1 artifact step(s); cache: none | none | none | GOVERNANCE: unattended workflow can push repository content without a protected approval environment |
| `artemis-fawl.yml` | valid and ready | pull_request, workflow_dispatch | contents | none | validate | 0 artifact step(s); cache: validate:pip | none | none | No source-verifiable failure risk found. |
| `auto-store.yml` | unsafe and requiring governance changes before execution | pull_request, push, schedule, workflow_dispatch | contents | CONTROL_PLANE_URL, GITHUB_TOKEN, RENDER_DEPLOY_HOOK_URL, RENDER_ROLLBACK_HOOK_URL | validate, test, checkout-health, deploy, verify, rollback, alert | 2 artifact step(s); cache: none | production | Render | GOVERNANCE: deployment job 'rollback' has no protected environment binding |
| `bot-orchestrator.yml` | unsafe and requiring governance changes before execution | schedule, workflow_dispatch | contents | GITHUB_TOKEN | orchestrate | 1 artifact step(s); cache: orchestrate:pip | none | none | GOVERNANCE: unattended workflow can push repository content without a protected approval environment |
| `burlington-military-op.yml` | valid and ready | workflow_dispatch, schedule | contents | none | military-op | 1 artifact step(s); cache: none | ${{ github.event_name == 'workflow_dispatch' && inputs.environment || 'staging' }} | none | No source-verifiable failure risk found. |
| `burlington-release.yml` | valid and ready | workflow_dispatch, schedule | contents | none | release-gate | 1 artifact step(s); cache: none | ${{ github.event_name == 'workflow_dispatch' && inputs.environment || 'staging' }} | none | No source-verifiable failure risk found. |
| `cert-bot.yml` | valid and ready | schedule, workflow_dispatch | contents | none | track | 0 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `ci.yml` | valid and ready | push, pull_request, workflow_dispatch | contents | none | python-tests, lint, site-audit, workflow-doctor, osint-deck | 0 artifact step(s); cache: python-tests:pip, lint:pip, workflow-doctor:pip | none | none | No source-verifiable failure risk found. |
| `clearglassinc-military-op.yml` | unsafe and requiring governance changes before execution | workflow_dispatch, schedule | contents, id-token, actions, security-events | none | inspect, build-test, security, staging, production, release, audit | 3 artifact step(s); cache: none | {'name': 'production', 'url': 'https://www.clearglassinc.com'} | none | GOVERNANCE: unattended workflow can push repository content without a protected approval environment |
| `codex-autofix.yml` | valid and ready | workflow_dispatch | contents | OPENAI_API_KEY | autofix | 0 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `commerce-daily-loop.yml` | valid and ready | schedule, workflow_dispatch | contents | none | daily-loop | 0 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `commerce-deploy.yml` | unsafe and requiring governance changes before execution | push, workflow_dispatch | contents | RENDER_DEPLOY_HOOK_URL | gate, frontend-build, deploy | 0 artifact step(s); cache: frontend-build:npm | none | Render | GOVERNANCE: deployment job 'deploy' has no protected environment binding |
| `commerce-frontend-ci.yml` | valid and ready | push, pull_request | contents | none | build | 0 artifact step(s); cache: build:npm | none | none | No source-verifiable failure risk found. |
| `compliance-evidence.yml` | valid and ready | schedule, workflow_dispatch | contents | none | harvest | 1 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `content-pipeline.yml` | unsafe and requiring governance changes before execution | workflow_run, workflow_dispatch | contents | none | validate-and-commit | 0 artifact step(s); cache: none | none | none | GOVERNANCE: unattended workflow can push repository content without a protected approval environment |
| `control-surface-feeds.yml` | unsafe and requiring governance changes before execution | schedule, workflow_dispatch | contents | GITHUB_TOKEN | publish-feeds, dispatch-pages-deploy | 0 artifact step(s); cache: publish-feeds:pip | none | none | GOVERNANCE: unattended workflow can push repository content without a protected approval environment |
| `copilot-setup-steps.yml` | valid and ready | push, workflow_dispatch | contents | none | validate-site | 1 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `daily-marketing-content.yml` | valid and ready | schedule, workflow_dispatch | contents, issues | GITHUB_TOKEN | create-daily-page | 0 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `defender-watch.yml` | valid and ready | push, pull_request, schedule, workflow_dispatch | contents | DEFENDER_DISCORD_WEBHOOK_URL, DEFENDER_SLACK_WEBHOOK_URL, GITHUB_TOKEN | defend | 1 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `dependency-updater.yml` | unsafe and requiring governance changes before execution | schedule, workflow_dispatch | contents | GITHUB_TOKEN | update-python-deps | 0 artifact step(s); cache: update-python-deps:pip | none | none | GOVERNANCE: unattended workflow can push repository content without a protected approval environment |
| `dispatch-all-workflows.yml` | valid and ready | workflow_dispatch | contents, actions | GITHUB_TOKEN | dispatch | 0 artifact step(s); cache: dispatch:pip | none | none | No source-verifiable failure risk found. |
| `health-monitor.yml` | valid and ready | schedule, workflow_dispatch | contents | GITHUB_TOKEN | site-health | 1 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `internal-link-authority.yml` | valid and ready | pull_request, push, workflow_dispatch | contents | none | validate-authority-network | 3 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `ip-protection-scan.yml` | valid and ready | push, pull_request, schedule | contents, issues, pull-requests | GITHUB_TOKEN | scan | 1 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `master-orchestrator.yml` | valid and ready | workflow_dispatch, schedule | contents | none | web-seo, ai-agents, corporate-content, brand-viral | 0 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `multi-repo-audit.yml` | valid and ready | schedule, workflow_dispatch | contents | CG_ORG_PAT | audit | 1 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `organic-daily.yml` | valid and ready | schedule, workflow_dispatch | contents, issues | GITHUB_TOKEN | generate | 0 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `organic-weekly-review.yml` | valid and ready | schedule, workflow_dispatch | contents, issues | GITHUB_TOKEN | review | 0 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `pages.yml` | valid and ready | push, workflow_dispatch | contents, pages, id-token | none | build, deploy | 1 artifact step(s); cache: none | {'name': 'github-pages', 'url': '${{ steps.deployment.outputs.page_url }}'} | GitHub Pages | No source-verifiable failure risk found. |
| `percival-policy-gate.yml` | valid and ready | pull_request, workflow_dispatch | contents | none | call-policy-gate | 0 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `percival-policy-reusable.yml` | valid and ready | workflow_call | contents | none | policy-tests | 0 artifact step(s); cache: policy-tests:pip | none | none | No source-verifiable failure risk found. |
| `phoenix-self-heal.yml` | valid and ready | push, pull_request, workflow_dispatch | contents | none | self-heal-gate | 0 artifact step(s); cache: self-heal-gate:pip | none | none | No source-verifiable failure risk found. |
| `policy-gate.yml` | valid and ready | pull_request, push, workflow_dispatch | contents | none | opa | 0 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `pr-automation.yml` | valid and ready | pull_request | contents | GITHUB_TOKEN | triage | 0 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `release-supply-chain.yml` | unsafe and requiring governance changes before execution | workflow_call | contents | GITHUB_TOKEN | build-sign-attest | 0 artifact step(s); cache: none | none | GHCR | GOVERNANCE: deployment job 'build-sign-attest' has no protected environment binding |
| `remove-homepage-crimson-loader.yml` | valid and ready | push, workflow_dispatch | contents | none | patch | 0 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `repo-audit.yml` | valid and ready | schedule, workflow_dispatch | contents | GITHUB_TOKEN | audit | 1 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `sales-ops-briefing.yml` | valid and ready | schedule, workflow_dispatch | contents | BRIEFING_TO, DATABASE_URL, GMAIL_APP_PASSWORD, GMAIL_USER | briefing | 0 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `security.yml` | valid and ready | pull_request, push, schedule | contents | none | dependency-review, secret-scan, workflow-lint | 0 artifact step(s); cache: workflow-lint:pip | none | none | No source-verifiable failure risk found. |
| `seo-optimizer.yml` | valid and ready | workflow_call, workflow_dispatch | contents | none | run | 0 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `thought-leadership.yml` | valid and ready | workflow_call, workflow_dispatch | contents | none | run | 0 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `viral-content.yml` | valid and ready | workflow_call, workflow_dispatch | contents | none | run | 0 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |
| `workflow-doctor.yml` | unsafe and requiring governance changes before execution | schedule, push, workflow_dispatch | contents | GITHUB_TOKEN | audit, repair | 0 artifact step(s); cache: audit:pip, repair:pip | none | none | GOVERNANCE: unattended workflow can push repository content without a protected approval environment |
| `workflow-repair-agent.yml` | valid and ready | workflow_dispatch | contents, pull-requests, actions, id-token | none | inspect-and-fix | 1 artifact step(s); cache: none | none | none | No source-verifiable failure risk found. |

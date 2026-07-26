# GitHub Actions remediation report

**Audit date:** 2026-07-26  
**Scope:** every YAML file in `.github/workflows/` plus the local composite action in `.github/actions/`  
**Operating decision:** validate locally; do not dispatch remote, production, secret-bearing, repository-writing, or deployment workflows without a named human approval.

## Executive disposition

The repository contains 50 workflows. All 50 parse as YAML, every executable job has an explicit timeout, and all third-party actions in both workflows and composite actions are now pinned to immutable 40-character commit SHAs. The official Pages chain is `build` → validated `dist` artifact → `deploy`, with `needs: build` and the protected `github-pages` environment.

| State | Workflows | Exact risk / disposition |
|---|---|---|
| **Valid and ready** | `agent-army-crypto`, `agent-army`, `agent-deployer`, `agent-os`, `artemis-browser`, `artemis-deploy`, `artemis-fawl`, `burlington-military-op`, `burlington-release`, `cert-bot`, `ci`, `commerce-daily-loop`, `commerce-frontend-ci`, `compliance-evidence`, `content-pipeline`, `control-surface-feeds`, `copilot-setup-steps`, `daily-marketing-content`, `defender-watch`, `dependency-updater`, `health-monitor`, `internal-link-authority`, `master-orchestrator`, `multi-repo-audit`, `percival-policy-gate`, `percival-policy-reusable`, `phoenix-self-heal`, `policy-gate`, `pr-automation`, `release-supply-chain`, `repo-audit`, `security`, `seo-optimizer`, `thought-leadership`, `viral-content` | Read-only or narrowly scoped validation/automation; no immediate defect found. Secret-bearing jobs require the documented secret and remain unsuitable for forked/untrusted execution. |
| **Valid but improved in this patch** | `auto-store`, `commerce-deploy`, `organic-daily`, `organic-weekly-review`, `pages`, `workflow-doctor` | The composite action had a mutable action ref; the Render deploy lacked a protected environment binding; organic jobs had unnecessary `contents: write` and hid issue-creation failures; doctor dependencies floated. Corrected as described below. Pages required no patch and is the reference deployment pattern. |
| **Valid but needs improvement** | `api-security-audit`, `bot-orchestrator`, `clearglassinc-military-op`, `codex-autofix`, `ip-protection-scan`, `sales-ops-briefing` | Permissions are broader than individual steps need, optional-secret behavior can mask missing operational configuration, or external side effects lack a dedicated protected environment. Narrow permissions per job and bind side-effecting jobs to protected environments before treating these as unattended production automation. |
| **Unsafe pending governance change** | `agent`, `dispatch-all-workflows`, `remove-homepage-crimson-loader`, `workflow-repair-agent` | These can grant an agent repository write access, fan out into deploy/secret-bearing workflows, push directly to the default branch, or claim automated fixes that are currently placeholders. Do not dispatch. Require an allowlist, inspect/fix privilege separation, protected environment approval, branch-only writes, and PR review. |
| **Broken requiring immediate patching** | None remaining | The mutable action reference in `.github/actions/store-setup/action.yml` was the immediate supply-chain failure and is fixed. |

## Exact remediation applied

1. Pinned the composite action's `actions/setup-python` call to its reviewed SHA and pinned its PyYAML install. This closes the nested mutable-action gap that a workflow-only scan missed.
2. Added immutable-action validation for both `.github/workflows/*.yml` and `.github/actions/**/action.yml` to `scripts/workflow_doctor.py`. A mutable external action now fails the audit rather than being advisory.
3. Bound `commerce-deploy.yml`'s Render job to the `production` environment. Repository administrators should configure required reviewers there; missing configuration must never be interpreted as approval.
4. Reduced both organic workflows from `contents: write` to `contents: read`; retained only `issues: write`. Removed `|| true` so failed issue creation is observable.
5. Pinned PyYAML in the workflow-doctor and dispatcher bootstrap steps.

Rollback is a normal revert of this commit. Reverting the Render environment binding removes the approval boundary and is therefore not recommended. The Pages rollback path is redeploying a known-good commit; the auto-store path additionally retains a 30-day last-known-good artifact and invokes its configured rollback hook.

## Complete workflow inventory

`Secrets` lists references only; no secret value was read or printed. `Artifacts` names jobs that upload an artifact. Caches are configured through pinned setup actions where present. A dash means none found.

| Workflow | Triggers | Jobs | Effective top-level permissions | Secrets | Artifact jobs | Environment / target |
|---|---|---:|---|---|---|---|
| `agent-army-crypto.yml` | PR, push, manual | 1 | contents:read | — | — | — |
| `agent-army.yml` | PR, push, manual | 1 | contents:read | — | — | — |
| `agent-deployer.yml` | reusable, manual | 1 | contents:read | — | — | — |
| `agent-os.yml` | schedule, PR, manual | 1 | contents:read | — | — | — |
| `agent.yml` | manual | 1 | contents:read; job elevation | Anthropic credential, GitHub token | — | repository/PR writes |
| `api-security-audit.yml` | schedule, manual | 1 | contents:read; security-events/issues:write | three audit identities | `api-security-audit` | `staging` |
| `artemis-browser.yml` | push, PR, manual | 1 | contents:read | — | — | — |
| `artemis-deploy.yml` | push, schedule, manual | 3 | contents:read | — | `ip-guardian-gate` | validation only |
| `artemis-fawl.yml` | PR, manual | 1 | contents:read | — | — | — |
| `auto-store.yml` | PR, push, schedule, manual | 7 | contents:read; alert job issues:write | control URL, deploy/rollback hooks, GitHub token | rollback anchor | `production` / Render |
| `bot-orchestrator.yml` | schedule, manual | 1 | contents:read; job issues:write | GitHub token | `orchestrate` | issues |
| `burlington-military-op.yml` | manual, schedule | 1 | contents:read | — | `military-op` | selected environment; no deploy |
| `burlington-release.yml` | manual, schedule | 1 | contents:read | — | `release-gate` | selected environment; no deploy |
| `cert-bot.yml` | schedule, manual | 1 | contents:read | — | — | — |
| `ci.yml` | push, PR, manual | 5 | contents:read | — | — | — |
| `clearglassinc-military-op.yml` | manual, schedule | 7 | contents:read; OIDC/security writes | — | security, release, audit | `production`; release tag |
| `codex-autofix.yml` | manual | 1 | contents:read; job PR/contents write | OpenAI key | — | draft PR |
| `commerce-daily-loop.yml` | schedule, manual | 1 | contents:read | — | — | — |
| `commerce-deploy.yml` | main-path push, manual | 3 | contents:read | Render hook | — | `production` / Render |
| `commerce-frontend-ci.yml` | push, PR | 1 matrix | contents:read | — | — | — |
| `compliance-evidence.yml` | schedule, manual | 1 | contents:read | — | `harvest` | — |
| `content-pipeline.yml` | workflow completion, manual | 1 | contents:read | — | — | — |
| `control-surface-feeds.yml` | schedule, manual | 2 | contents:read; update job contents:write | GitHub token | — | branch commit |
| `copilot-setup-steps.yml` | push, manual | 1 | contents:read | — | `validate-site` | — |
| `daily-marketing-content.yml` | schedule, manual | 1 | contents:read; issues:write | GitHub token | — | issues |
| `defender-watch.yml` | push, PR, schedule, manual | 1 | contents:read; issues:write | notification webhooks, GitHub token | `defend` | issues/webhooks |
| `dependency-updater.yml` | schedule, manual | 1 | contents:read; job contents/PR write | GitHub token | — | PR |
| `dispatch-all-workflows.yml` | manual | 1 | contents:read; actions:write | GitHub token | — | workflow fan-out |
| `health-monitor.yml` | schedule, manual | 1 | contents:read; issues:write | GitHub token | `site-health` | issues |
| `internal-link-authority.yml` | PR, push, manual | 1 | contents:read | — | validation bundle | — |
| `ip-protection-scan.yml` | push, PR, schedule | 1 | contents:read; issues/PR:write | GitHub token | `scan` | issues |
| `master-orchestrator.yml` | manual, schedule | 4 reusable jobs | contents:read | — | — | reusable fan-out |
| `multi-repo-audit.yml` | schedule, manual | 1 | contents:read | organization PAT | `audit` | organization read |
| `organic-daily.yml` | schedule, manual | 1 | contents:read; issues:write | GitHub token | — | issues |
| `organic-weekly-review.yml` | schedule, manual | 1 | contents:read; issues:write | GitHub token | — | issues |
| `pages.yml` | main push, manual | 2 | contents:read; pages/OIDC:write | — | Pages artifact | `github-pages` / Pages |
| `percival-policy-gate.yml` | PR, manual | 1 reusable | contents:read | — | — | — |
| `percival-policy-reusable.yml` | reusable | 1 | contents:read | — | — | — |
| `phoenix-self-heal.yml` | push, PR, manual | 1 | contents:read | — | — | simulation only |
| `policy-gate.yml` | PR, push, manual | 1 | contents:read | — | — | — |
| `pr-automation.yml` | PR | 1 | contents:read; scoped job writes | GitHub token | — | PR metadata |
| `release-supply-chain.yml` | reusable | 1 | contents:read; packages/OIDC attestations | GitHub token | — | GHCR |
| `remove-homepage-crimson-loader.yml` | workflow-file push, manual | 1 | contents:write | — | — | direct default-branch push |
| `repo-audit.yml` | schedule, manual | 1 | contents:read; issues:write | GitHub token | `audit` | issues |
| `sales-ops-briefing.yml` | schedule, manual | 1 | contents:read | database/mail credentials | — | email |
| `security.yml` | PR, push, schedule | 3 | contents:read; scoped security-events write | — | — | CodeQL/security |
| `seo-optimizer.yml` | reusable, manual | 1 | contents:read | — | — | — |
| `thought-leadership.yml` | reusable, manual | 1 | contents:read | — | — | — |
| `viral-content.yml` | reusable, manual | 1 | contents:read | — | — | — |
| `workflow-doctor.yml` | schedule, workflow push, manual | 2 | contents:read; repair job contents/PR write | GitHub token | — | repair PR |
| `workflow-repair-agent.yml` | manual | 1 | read defaults; job contents/PR write | GitHub token | audit bundle | PR |

## Validation and rollout runbook

### Apply in this order

1. Merge immutable action and doctor enforcement changes.
2. Merge least-privilege organic changes.
3. Configure required reviewers on the `production` environment, then merge the commerce binding.
4. Run read-only CI/security/policy workflows. Do not use the fan-out dispatcher.
5. After green validation and named release approval, run the applicable deploy workflow against a reviewed commit SHA.

### Preflight commands

```bash
python scripts/workflow_doctor.py
python -m pytest tests/test_workflow_doctor.py tests/test_dispatch_all_workflows.py -q
python scripts/dispatch_all_workflows.py --dry-run
python tools/internal_links.py --check
```

Before deployment, confirm the target environment has required reviewers, the deploy hook exists without printing it, the build artifact is from the current run, and a known-good commit is recorded. Abort on any mismatch.

### Post-deployment monitoring

- Verify the Pages deployment URL and `/index.html`, `_headers`, `_redirects`, `.nojekyll`, and representative static assets.
- Verify Render readiness and functional health, not merely hook acceptance.
- Watch Actions audit events, environment approvals, unexpected token elevation, artifact provenance, and rollback alerts for the observation window.
- Roll back Pages by redeploying the last known-good commit; roll back Render through the configured rollback hook or provider dashboard.

### Weekly health checks

- Run Workflow Doctor and the read-only CI, security, policy, dependency, IP, and repository audits.
- Review action SHAs against approved upstream releases and dependency advisories; never auto-advance a SHA without review.
- Review workflow permissions, environment reviewers, secret age/usage, skipped optional-secret paths, failed schedules, artifact retention, cache hit anomalies, and runner duration drift.
- Dry-run the dispatcher inventory only. Review the four governance-blocked workflows until their controls are implemented.

## ClearGlassInc Artemis platform note

The repository's existing Artemis architecture documents remain specifications rather than evidence of deployed Palantir Gotham, Foundry, AIP, or Apollo infrastructure. Workflow automation must preserve the governed lifecycle: telemetry and proposals may be automatic, but prompt/workflow/model changes require evaluation evidence, explicit human approval, versioned promotion, and Apollo-style rollback control before production activation.

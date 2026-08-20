# Incident Report — GitHub Actions Runner Admission / Pages Deployment Degradation

**Date:** 2026-08-14  
**Repository:** `ClearGlassInc/ClearGlassIncorporated-Desmond`  
**Branch:** `main`  
**Latest observed commit:** `5fe91ff9db927d7d7caab0eae81e583e3ed2db77`  
**Status:** CONTAINED — production remains available through legacy GitHub Pages; Actions-backed deployment remains unavailable.  
**Severity:** SEV-3 — release pipeline degraded, no verified public-site outage.

## INCIDENT SUMMARY

- Environment: production delivery via GitHub Pages, plus GitHub Actions CI/CD control plane.
- Service/application: ClearGlassInc.com and repository automation.
- Deployment/version: latest source commit `5fe91ff9...`; latest successful Pages build observed at `8022a9af...`.
- Customer/system impact: public Pages reports `built`, but the Actions deployment workflow for `5fe91ff9...` failed before executing user steps. The latest service-worker cache-control commit is not represented by the latest successful Pages build record.
- Detection time: 2026-08-14 13:08 America/New_York investigation start; latest failing Actions run started 2026-08-14 12:44:51 America/New_York.

## VERIFIED EVIDENCE

1. Repository default branch is `main`; latest observed commit is `5fe91ff9db927d7d7caab0eae81e583e3ed2db77`.
2. GitHub Pages configuration reports:
   - status `built`
   - custom domain `www.clearglassinc.com`
   - HTTPS enforced
   - build type `legacy`
   - source `main` at `/`
3. Latest successful Pages build observed:
   - build `1151384389`
   - status `built`
   - commit `8022a9af0ee3ece63089455dfea5048c75a40c51`
   - created `2026-08-14T16:44:49Z`
4. The same commit `8022a9af...` also had a zero-duration Pages build failure immediately before the successful build, proving that at least that failed Pages event was not caused by deterministic repository content.
5. Latest Actions `Deploy Pages` run for `5fe91ff9...`:
   - run `31820781773`
   - conclusion `failure`
   - build job `94833224777`
   - step list empty
   - deploy and production-verification jobs skipped
6. `Sync Stripe Products` run `31820793457` also failed with its `Type check and tests` job reporting no executed steps and no retrievable job log blob.
7. Existing repository runbook `docs/ACTIONS_BILLING_FALLBACK.md` records the operational condition as a GitHub account billing lock that occurs before runner allocation.
8. Direct billing-detail verification through the GitHub integration is blocked with HTTP 403 (`Resource not accessible by integration`), so account billing metadata itself was not exposed or read.

## HYPOTHESES

| Rank | Hypothesis | Confidence | Evidence | Disproving test | Risk |
|---|---|---:|---|---|---|
| 1 | GitHub-hosted Actions cannot allocate runners because of the existing account-level billing lock | High | Multiple unrelated workflows fail with zero executed steps; repository runbook records the same condition | After account billing access is restored, rerun one failed job and confirm checkout/setup steps actually start | Low |
| 2 | Repository code or dependency failure causes the current Actions failures | Low | No user step starts, so code is never executed | A runner starting and then failing inside checkout/build/test would support this | Low |
| 3 | Legacy Pages has an independent transient admission/build issue | Medium | Zero-duration failed build for `8022a9af...` followed immediately by a successful build of the exact same SHA | Repeated deterministic failures on the same SHA with build logs pointing to repository content | Low |

## ACTIONS TAKEN

- Performed read-only repository, workflow-run, job, Pages configuration, and Pages build-history inspection.
- Confirmed no secret values were read or exposed.
- Created isolated branch `fix/sre-deployment-containment-20260814` from `5fe91ff9...`.
- Prepared a minimal containment change to:
  - make the Actions-backed production Pages workflow manual-only;
  - remove its automatic mutation of the repository's production Pages publishing mode;
  - replace that mutation with a read-only fail-closed check;
  - retain deployment permissions only in the explicit deployment job;
  - add a regression test enforcing these invariants.
- No merge, deployment, rollback, DNS change, billing change, secret change, or Pages-setting mutation was performed.

## ROOT CAUSE

Primary operational root cause: GitHub-hosted Actions runner admission is blocked before user code execution, consistent with the already documented account-level billing lock.

Secondary Pages symptom: several legacy Pages builds failed at zero duration, including one for a SHA that then built successfully without a source change. That symptom is consistent with a transient platform/build-admission failure and is not attributable to deterministic repository content based on current evidence.

Existing controls did not prevent the incident because the repository still had push-triggered Actions workflows that attempted to start hosted runners while the account-level runner gate was unavailable. The production Pages workflow also contained logic that could mutate the repository Pages source mode from inside the workflow, coupling deployment execution to production configuration.

## FIX

Proposed containment on the isolated branch:

1. Keep production delivery on the currently configured legacy Pages source.
2. Stop automatic push-triggered execution of the Actions-backed `Deploy Pages` workflow while runner access is externally blocked.
3. Require an explicit manual dispatch for any future Actions-backed production deployment.
4. Replace automatic `PUT /pages` source-mode changes with a read-only verification that refuses to deploy unless an administrator has intentionally configured `build_type=workflow`.
5. Add a regression test that fails if the deployment workflow becomes push-triggered again or regains source-mode mutation logic.

Rollback: close the PR or delete the isolated branch. No production state has changed.

## VERIFICATION

Completed:
- GitHub API evidence collection for repository metadata, workflow runs, jobs, Pages configuration, and Pages build history.
- YAML syntax validation for the proposed `pages.yml`.
- Python syntax validation for the proposed regression test.
- Confirmed the proposed workflow grants `pages: write` and `id-token: write` only to the deployment job.

Not yet possible:
- Execute GitHub-hosted CI on the patch while runner admission remains blocked.
- Verify an Actions-backed production deployment without explicit production approval and restored account-level runner access.
- Confirm the precise billing-account state because the integration lacks billing-resource permission.

## PREVENTION

- Regression test: enforce manual-only Actions deployment while the legacy fallback is active.
- CI/CD guardrail: reject any deployment workflow that silently changes Pages publishing source mode.
- Operational guardrail: keep legacy Pages and Actions-backed Pages as explicitly selected modes, not self-mutating modes.
- Recovery runbook: after account runner access is restored, first run a non-production/read-only workflow, then request explicit approval before changing Pages source mode or performing a production deployment.

## RISKS AND UNKNOWNS

- The latest source commit `5fe91ff9...` is not the commit reported by the latest successful Pages build; therefore latest-release parity is not verified.
- Public-site runtime behavior was not modified by this investigation.
- Billing-account status is operationally high-confidence but cannot be directly read through the connected GitHub integration.
- Other workflows may continue to create failed/skipped records while GitHub-hosted runner admission is blocked.

## APPROVAL REQUIRED

To restore Actions-backed production deployment after runner access is fixed:

- Target: GitHub Pages production for `ClearGlassInc/ClearGlassIncorporated-Desmond`.
- Change: explicitly switch Pages publishing source from `legacy` to `workflow`, then manually dispatch `Deploy Pages` for the approved commit.
- Expected result: build, artifact verification, Pages deployment, and production probe execute on real runners.
- Rollback: switch Pages publishing source back to `main` `/` legacy mode and retain the last known-good published commit.
- Blast radius: public production website deployment control plane; no database or customer-data mutation expected.

# GitHub Actions Billing-Lock Fallback

## Purpose

Keep the ClearGlass public platform deployable and observable when GitHub-hosted Actions cannot start because the GitHub account is billing-locked.

## Current failure mode

A billing lock occurs before runner allocation. Workflow YAML changes, retries, self-healing jobs, dependency changes, or test changes cannot repair that condition because no job process is started.

## Operational fallback

1. **Repository writes continue through the GitHub API / Contents API.** Code and content changes can still be committed through an authenticated GitHub App or authorized user.
2. **Changes are isolated on a branch and merged through a pull request.** This preserves reviewability and rollback even while CI is unavailable.
3. **GitHub Pages remains the public delivery path from `main`.** The repository is configured for the legacy Pages source (`main` / repository root), which does not require the blocked repository workflow to execute.
4. **Runtime validation moves to the browser for public data.** `/data-fabric.html` loads `/data/catalog.json`, probes browser-loadable root datasets, and reports whether the governed public data fabric is reachable.
5. **Offline integrity validation remains available.** `python3 scripts/validate_data_fabric.py` recursively validates the local `/data` tree using only the Python standard library. `node --check assets/js/clearglass-data-fabric.js` syntax-checks the browser runtime.
6. **The CI gates themselves still run locally.** `python3 scripts/ci_local.py` executes the `ci.yml` gate set on your machine. Run it before merging anything while the lock is active.

## Gate blindness is the real hazard

A billing lock does not only stop deployment. It stops *feedback*. Workflows are
still queued and still reported, but with zero executed steps, so a red gate and a
never-started gate look identical in the Actions tab. Merges keep landing, and
nothing contradicts them.

Twice now that has let regressions sit on `main` unseen. The 2026-08-14
containment commit shipped a lint error and a stale provenance hash. On
2026-08-20 the root pytest gate was found aborting at collection — running **zero
of ~1,900 tests while reporting no test failures** — and a duplicated dictionary
literal in `tools/internal_links.py` had silently reverted a page registration
from the merge that introduced it. Every one of those reproduces locally in about
two minutes.

So while runners are unavailable:

- Run `python3 scripts/ci_local.py` on the branch before merging.
- Treat a skipped gate as unverified, never as passing — the runner says so
  itself, and it means it.
- Commit whatever the generators rewrite; that drift *is* the gate failing.
- A collection error is the dangerous one. `pytest` aborting the session reports
  no failed tests, so it reads like success at a glance. Check the exit status
  and the test count, not the absence of red.

## What this fallback does not pretend to do

- It does not bypass GitHub billing controls.
- It does not make blocked GitHub-hosted Actions execute.
- It does not fabricate passing CI checks.
- It does not expose private secrets or the restricted `data/leads` module to browser loading.

## Recovery

When the GitHub billing lock is removed:

1. Re-run the failed `Data Fabric Integrity` workflow.
2. Re-run other failed workflows that were annotated as not started because of the billing lock.
3. Confirm `Validate governed data assets` executes actual steps rather than returning an empty step list.
4. Keep the Actions-independent runtime diagnostics in place as a secondary production health signal.

## Release decision rule

A Pages build may be considered **published** when GitHub Pages reports `built` for the intended commit. It must not be described as **CI-verified** until the blocked Actions jobs have actually executed and passed.

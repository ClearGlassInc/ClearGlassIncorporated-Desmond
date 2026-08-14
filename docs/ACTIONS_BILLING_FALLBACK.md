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

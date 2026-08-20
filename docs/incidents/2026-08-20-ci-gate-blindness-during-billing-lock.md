# Incident Report — CI Gate Blindness During the Actions Billing Lock

**Date:** 2026-08-20
**Repository:** `ClearGlassInc/ClearGlassIncorporated-Desmond`
**Branch investigated:** `main` @ `b70010a800a58803776d8c88265387981a87a0b7`
**Remediation branch:** `claude/sre-incident-diagnosis-2plxct`
**Status:** RESOLVED (local verification) / AWAITING APPROVAL (production deploy)
**Severity:** SEV-3 — no verified customer-facing outage; release verification was absent and five gates were red on the default branch.

## INCIDENT SUMMARY

- **Environment:** GitHub Actions CI/CD control plane for the repository; production delivery remains legacy GitHub Pages.
- **Service/application:** repository quality gates protecting ClearGlassInc.com, the governed commerce control plane, and the RFED audit trail.
- **Deployment/version:** `main` at `b70010a`, the merge of the 2026-08-14 containment PR #1465.
- **Customer/system impact:** no verified public-site outage. The impact was to assurance: the root Python gate executed **0 of 1,890 tests** while reporting no failures, so every merge since 2026-08-12 landed unverified.
- **Severity:** SEV-3.
- **Detection time:** 2026-08-20, during follow-up on the 2026-08-14 incident (`docs/incidents/2026-08-14-deployment-runner-admission-failure.md`).

This is the follow-on to that incident. That one correctly contained *deployment*. It did not address *verification*, which is where the damage actually accumulated.

## VERIFIED EVIDENCE

All findings below were reproduced locally in isolated virtualenvs. Two environments were used deliberately, because the bug only exists in one of them:

- **Root CI env** — `pip install -c requirements.txt -e ".[test]" "PyYAML==6.0.2"`, exactly `ci.yml`'s Python Tests job. Ships `fastapi`/`httpx`, **not** `sqlalchemy`.
- **Commerce env** — `pip install -r clearglass-commerce/control-plane/requirements.txt pytest`, exactly `commerce-deploy.yml`. Ships `sqlalchemy`.

1. **Root pytest aborted at collection.** `python -m pytest --cov=artemis --cov-report=xml -q` exited **2** with `Interrupted: 3 errors during collection` — `2 skipped, 3 errors`. Zero of 1,890 tests ran. Failing modules: `test_fulfillment.py`, `test_route_auth_coverage.py`, `test_sales_ops_briefing.py`, all `ModuleNotFoundError: No module named 'sqlalchemy'`.
2. **The cause is a configuration coupling, not a code defect.** `pyproject.toml` sets `testpaths` to include `clearglass-commerce/control-plane/tests`, while `[project.optional-dependencies].test` installs only `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx`. Nothing in the root dependency set pulls `sqlalchemy`.
3. **One of the three failures was transitive.** `test_route_auth_coverage.py` imports no database module directly; it imports `app.main`, which imports `app.routers.approvals`, which imports `sqlalchemy`. A static scan for `import sqlalchemy` would not have found it.
4. **Introduced 2026-08-12 by `5c03d0e`.** That commit created `pyproject.toml` (establishing both the four-path `testpaths` and the bare `pytest` invocation in `ci.yml`). The three modules already imported `sqlalchemy` unguarded at that revision, verified via `git show 5c03d0e:<path>`.
5. **Six further failures were masked behind the abort.** With the commerce path excluded, `tests/test_workspace.py` failed 6 tests on the same missing dependency — imported lazily inside test bodies, so those modules collected cleanly and failed only at run time.
6. **`ruff check .` failed** with `F401 'pathlib.Path' imported but unused` at `tests/test_deployment_workflow_containment.py:2` — a file added by the 2026-08-14 containment commit `3d43261`.
7. **The provenance manifest was stale.** `tests/test_security_release_manifest.py` failed; `provenance/release-manifest.json` pinned `sha256 3ba2ff87…` for `.github/workflows/pages.yml` while the file on disk hashed to `f1903853…`. The same containment commit `3d43261` edited that workflow without regenerating the manifest.
8. **`data-fabric.html` shipped unregistered.** Added 2026-08-14 by `ec9b736`, it appeared in no generator input: absent from `internal_links.PAGES`/`EXCLUDED_PAGES`, from `design_system.EXEMPT`, from `sitemap.xml`, and carried no tab icon, logo badge, or shared enhancement layer. This produced 8 distinct test failures plus two red `--check` gates.
9. **`sitemap.xml` was stale.** Regenerating produced a deterministic 5-line diff: `lastmod` for five `operations/*.html` pages moved from 2026-08-09/08-11 to 2026-08-12, matching `git log` for those files. The generator derives dates via `git_date(path)`, and a second run produced no further change, confirming determinism rather than clock drift.
10. **Runner admission remains externally blocked.** Consistent with `docs/ACTIONS_BILLING_FALLBACK.md`; no billing metadata was read, and no credential or secret value was accessed at any point in this investigation.

### Gate status on `main` before remediation

| Gate | Result | Introduced by |
|---|---|---|
| CI / Python Tests | **exit 2** — collection aborted, 0/1,890 tests ran | `5c03d0e` 2026-08-12 |
| CI / Lint (ruff) | **exit 1** — F401 | `3d43261` 2026-08-14 |
| CI / Search discovery | **drift** — stale `sitemap.xml` | `5c03d0e` 2026-08-12 |
| Internal links `--check` | **exit 1** — page unclassified | `ec9b736` 2026-08-14 |
| Design system `--check` | **exit 1** — contracts missing | `ec9b736` 2026-08-14 |

## HYPOTHESES

| Rank | Hypothesis | Confidence | Evidence | Disproving test | Risk |
|---|---|---:|---|---|---|
| 1 | Root `testpaths` includes a subtree whose dependencies the root extra never installs | Confirmed | Reproduced exit 2; the three modules resolve to one missing distribution; commerce env runs them all green | Collect the commerce path with `sqlalchemy` hidden and see it succeed | Low |
| 2 | The billing lock removed gate feedback, so unverified merges accumulated | Confirmed | Five independent gates red across 4 commits over 8 days, none reported | Find a completed Actions run with executed steps in the window | Low |
| 3 | Commerce test code is itself broken | Rejected | 274/274 pass with `sqlalchemy` installed, zero skipped | A failure that persists once the dependency is present | Low |
| 4 | `sitemap.xml` drift is clock-dependent and would flap in CI | Rejected | `lastmod` comes from `git_date()`; a second run produced no further diff | Non-idempotent regeneration | Low |

## ACTIONS TAKEN

All changes are on `claude/sre-incident-diagnosis-2plxct`. No production state was altered; every item is reversible by reverting the branch.

| # | Change | Files | Result |
|---|---|---|---|
| 1 | Guard commerce-only imports with `pytest.importorskip`, matching the existing convention in `test_resilience.py` | `test_fulfillment.py`, `test_route_auth_coverage.py`, `test_sales_ops_briefing.py`, `test_workspace.py` | collection restored: 1,890 collected, exit 0 |
| 2 | Remove the unused `Path` import | `tests/test_deployment_workflow_containment.py` | `ruff check .` exit 0 |
| 3 | Regenerate the provenance manifest | `provenance/release-manifest.json` | one-line re-pin of `pages.yml` |
| 4 | Classify `data-fabric.html` as a noindex private-operations surface | `tools/internal_links.py`, `tools/design_system.py` | both `--check` gates exit 0 |
| 5 | Wire the page's required shared layer (tab icons via `tools/tab_icons.py`; logo badge and future-buttons CSS/JS by hand, matching `platform-command-center.html`) | `data-fabric.html` | 8 failing tests pass |
| 6 | Bump the service-worker cache generation `cg-v64` → `cg-v65`, as `tools/tab_icons.py` instructs after an icon change | `sw.js` | returning visitors refetch |
| 7 | Regenerate search assets | `sitemap.xml` | drift resolved, idempotent |
| 8 | Add the collection-integrity regression test | `tests/test_root_collection_integrity.py` | fails on pre-fix code, passes after |
| 9 | Add the Actions-independent gate preflight | `scripts/gate_preflight.py` | 9/9 gates pass, exit 0 |
| 10 | Document gate blindness and correct the CI description | `docs/ACTIONS_BILLING_FALLBACK.md`, `CLAUDE.md` | — |

### On the choice to guard rather than install

`sqlalchemy` was deliberately **not** added to the root `[test]` extra. `CLAUDE.md` warns that a silently skipped money-movement test is worse than a loud failure, so the load-bearing question was whether guarding weakens the commerce gate. It does not: in the commerce environment the suite runs **274 passed, 0 skipped**, including all 7 tests in `test_route_auth_coverage.py` and all 24 in `test_workspace.py`. `importorskip` skips only where the dependency is genuinely absent — the root job, which was never that gate's venue and where the alternative is not "runs" but "aborts everything".

Adding the dependency to the root extra would also have duplicated commerce's pinned dependency management in a second place, inviting version drift between two suites that must agree.

### Classification of `data-fabric.html`

The page declares `<meta name="robots" content="noindex,follow">` and is a read-only diagnostics console. Every comparable surface — `platform-command-center.html`, `mission-control.html`, `seo-dashboard.html`, `threads.html`, and the `sentinel/` consoles — is listed in `design_system.EXEMPT` with a stated reason. Exemption follows that precedent and the page's own declared intent, rather than injecting public marketing chrome into an operations console. The `EXCLUDED_PAGES` and `EXEMPT` entries agree with each other and each carry a reason, as the enforcing tests require.

## ROOT CAUSE

**Primary — the failure that let everything else through.** GitHub-hosted runner admission is blocked before user code executes, so a workflow that never started and a workflow that failed are indistinguishable in the Actions tab: both show a conclusion with no executed steps. Gate feedback stopped, merges did not. Five gates went red across four commits over eight days with nothing to contradict them.

**Secondary — the largest single defect.** `pyproject.toml` pointed root `testpaths` at the commerce subtree without the root `[test]` extra providing that subtree's database dependency. Because pytest aborts the *entire* run on a collection error, one unsatisfied import in one module silenced 1,890 tests while reporting zero failures. Its worst property is its shape: a suite that runs nothing looks far more like a suite that passes than like one that fails.

**Why existing controls did not prevent it.** The controls were sound and their coverage was complete; their *execution* was not. `tests/test_design_system.py`, `test_internal_links.py`, and `test_security_release_manifest.py` would each have caught their respective regression on the commit that introduced it. Two of them could not run at all, because the collection abort preceded them. The rest never ran, because no runner started. The repository had no way to execute its own gates without GitHub-hosted compute — so when that compute became unavailable, verification did not degrade, it disappeared.

The 2026-08-14 response is the clearest illustration: it added a regression test to prevent recurrence, and that very file shipped a lint error and a stale provenance hash, because the incident it was containing had disabled the checks that would have caught both.

## FIX

1. **`pytest.importorskip` guards** on the four commerce modules that reach the database stack at import or call time. Root collection completes; the commerce gate is unchanged and still runs all 274 tests.
2. **Lint and provenance repairs** for the two defects left by the previous containment commit.
3. **`data-fabric.html` registered** across every generator that governs a shipped page, with the two exemption entries each carrying a stated reason.
4. **Derived assets regenerated** — `sitemap.xml`, `provenance/release-manifest.json`, tab icons — and the service-worker cache generation bumped.

**Rollback:** revert the branch, or `git revert` the single commit. No production state, DNS, billing, secret, Pages setting, or database was touched.

## VERIFICATION

Executed locally; every command and its exit status:

| Check | Command | Result |
|---|---|---|
| Root suite (root CI env) | `pytest --cov=artemis --cov-report=xml -q` | **1,857 passed, 38 skipped — exit 0** (was exit 2, 0 run) |
| Commerce suite (commerce env) | `pytest tests/ -q` | **274 passed, 0 skipped — exit 0** |
| Lint | `ruff check .` | **exit 0** (was exit 1) |
| Commerce lint | `ruff check clearglass-commerce` | **exit 0** |
| Internal links | `tools/internal_links.py --check` | **all 170 pages current — exit 0** |
| Design system | `tools/design_system.py --check` | **current across 185 routes — exit 0** |
| SEO audit | `tools/seo_audit.py` | **exit 0** (7 pre-existing warnings, unrelated) |
| Site reliability | `scripts/site_reliability_audit.py` | **0 errors, 0 warnings — exit 0** |
| Search assets | `tools/generate_search_assets.py` + `git diff` | **idempotent, no drift** |
| Preflight | `scripts/gate_preflight.py` | **9 passed, 0 failed, 0 skipped — exit 0** |

**The regression test was verified against the defect, not merely observed to pass.** With one guard reverted to its pre-fix state, `tests/test_root_collection_integrity.py` fails with `assert 2 in (0, 5)` and reports `204 tests collected, 1 error`. With the guard restored, it passes in both environments. A test that has never failed proves nothing, so this one was made to fail first.

**Not verified — and not claimed:**

- No GitHub-hosted CI job executed against this branch; runner admission is still blocked. This work is locally verified, **not CI-verified**.
- Node tooling (`npm ci`, `tsc --noEmit`, `next build`), Lighthouse budgets, and the Playwright browser suites were not run.
- No production deployment or Pages publish was performed or requested here.
- Billing-account state remains unread; the integration lacks that permission and it was not probed.

## PREVENTION

- **Regression test.** `tests/test_root_collection_integrity.py` collects the commerce testpath in a subprocess with `sqlalchemy` and `stripe` hidden from the import system. It reproduces the real condition rather than pattern-matching source, so it catches the transitive case that broke `test_route_auth_coverage.py`. Verified to fail on the pre-fix tree.
- **Runner-independent gate execution.** `scripts/gate_preflight.py` (standard library only) runs all nine locally runnable gates and prints a verdict. It reports a missing tool as SKIP rather than PASS, names the hosted-runner-only jobs it cannot cover, and states plainly that a green preflight is not a CI-verified release.
- **Runbook.** `docs/ACTIONS_BILLING_FALLBACK.md` gains a "Gate blindness is the real hazard" section: during a lock, run the preflight before merging, treat skipped gates as unverified, and commit generator output because the drift *is* the gate failing.
- **Corrected guidance.** `CLAUDE.md` described the root job as `pytest tests/`. It runs bare `pytest` across all four `testpaths` — the misreading that let this land. It now documents the real scope, the missing-dependency hazard, and the guard requirement.

## RISKS AND UNKNOWNS

**Verified facts** are listed above with their commands and exit statuses. The following are explicitly *not* verified:

- Whether hosted CI passes on this branch. Unknowable until runner admission is restored; the preflight narrows but does not close this gap.
- Node/Lighthouse/Playwright gates remain unexercised. The changes here touch one HTML page's `<head>`/`<body>` and Python test guards, so the risk is low but not zero — `data-fabric.html` now loads `future-buttons.css`/`.js` and `logo-badge.js`, which alters its rendering.
- Latest-release parity from the 2026-08-14 report is still open: `main` is ahead of the last successful Pages build record.
- The billing lock itself is unaddressed. It is an account-level condition outside this repository, and every finding here will recur in a future lock unless the preflight is actually run during one.
- 7 pre-existing SEO warnings (oversized HTML, multiple `<h1>`) are untouched, being unrelated to this incident.

## APPROVAL REQUIRED

Nothing below was performed. Each needs explicit authorization.

1. **Merge to `main`.** Target: default branch. Change: merge the draft PR from `claude/sre-incident-diagnosis-2plxct`. Expected: five gates return green and the root suite runs 1,857 tests instead of zero. Rollback: `git revert` the merge. Blast radius: repository CI configuration, test guards, and one noindex diagnostics page — no runtime service, database, or customer-data path.
2. **Restore Actions runner admission.** Account-level billing action outside this repository. Afterwards, re-run `CI` and confirm the Python Tests job reports executed steps and a real test count rather than an empty step list.
3. **Actions-backed production deployment.** Unchanged from the 2026-08-14 report: switching Pages publishing from `legacy` to `workflow` and dispatching `Deploy Pages` still requires explicit approval, and should follow — not precede — a verified green CI run on real runners.

# Incident Report — CI Gate Blindness During the Actions Billing Lock

**Date:** 2026-08-20
**Repository:** `ClearGlassInc/ClearGlassIncorporated-Desmond`
**Branch investigated:** `main` @ `e5df4c3c9a67ade897928d000f694747210f83d1` (merge of #1500)
**Remediation branch:** `claude/sre-incident-diagnosis-2plxct`
**Status:** RESOLVED (locally verified) / AWAITING APPROVAL (merge, runner restoration)
**Severity:** SEV-3 — no verified customer-facing outage; the default branch's quality gates were red and one class of failure was silent.

## INCIDENT SUMMARY

- **Environment:** GitHub Actions CI/CD control plane. Production delivery remains legacy GitHub Pages and was not touched.
- **Service/application:** the gates protecting ClearGlassInc.com, the governed commerce control plane, and the RFED audit trail.
- **Deployment/version:** `main` at `e5df4c3c`.
- **Customer/system impact:** no verified public-site outage. The impact was to assurance — the root Python gate executed **0 of ~1,900 tests** while reporting no test failures, so merges landed unverified. One public page (`helix.html`) shipped unregistered across every site generator.
- **Detection time:** 2026-08-20, following up the 2026-08-14 incident (`docs/incidents/2026-08-14-deployment-runner-admission-failure.md`).

This is the follow-on to that incident. That one contained *deployment*. It did not address *verification*, which is where the damage accumulated.

## VERIFIED EVIDENCE

Reproduced locally in isolated virtualenvs. Two environments were used deliberately, because the primary defect exists in only one of them:

- **Root CI env** — `pip install -c requirements.txt -e ".[test]" "PyYAML==6.0.2"`, exactly `ci.yml`'s Python Tests job. Ships `fastapi`/`httpx`, **not** `sqlalchemy` or `stripe`.
- **Commerce env** — `pip install -r clearglass-commerce/control-plane/requirements.txt pytest`, exactly `commerce-deploy.yml`. Ships `sqlalchemy`.

1. **Runner admission is still blocked.** Every `CI` run on `main` from 2026-08-17 through 2026-08-20 concluded `failure` in **5–8 seconds**. On the remediation branch, run `32390241036` failed with all 8 jobs completing in 2–4 seconds, no step data, and `HTTP 404` when fetching job logs — no log blob exists because no runner ever started. This matches `docs/ACTIONS_BILLING_FALLBACK.md` and the 2026-08-14 report. **No billing metadata was read**; the integration lacks that permission and it was not probed.
2. **Root pytest aborted at collection.** On `e5df4c3c`, `python -m pytest -q` exited **2** with `Interrupted: 5 errors during collection`. Zero tests ran. Failing modules: `test_approval_executor.py`, `test_fulfillment.py`, `test_order_routing.py`, `test_route_auth_coverage.py`, `test_sales_ops_briefing.py` — all `ModuleNotFoundError: No module named 'sqlalchemy'`.
3. **The defect is a configuration coupling and it is growing.** `pyproject.toml` sets `testpaths` to include `clearglass-commerce/control-plane/tests`; the root `[test]` extra installs neither `sqlalchemy` nor `stripe`. The same failure was three modules on 2026-08-14 and is five on 2026-08-20. One is transitive — `test_route_auth_coverage.py` imports `app.main` → `app.routers.approvals` → `sqlalchemy` — so a static scan for `import sqlalchemy` would not find it.
4. **22 further failures were masked behind the abort.** With collection restored, the suite reported 22 failures that no gate had ever surfaced.
5. **`tools/internal_links.py` contained the `CLUSTERS` map twice.** Lines 270–438 held an expanded copy; lines 439–450 held single-line copies of the same 12 keys. Python keeps the last, so the expanded block was dead code. `ruff` reported this as 12 × `F601`.
6. **That duplication silently reverted a feature.** `f1b8d24d` (#1500) added `helix.html` to the intelligence cluster **in the dead copy**. The live copy never gained it, so `helix.html` was `in PAGES but no cluster`. Verified by evaluating both blocks separately: the dead copy's only unique member was `helix.html`, while the live copy held ~35 members the dead copy lacked (16 services pages, 16 blog posts, `minerals.html`, `mission-control.html`, and others).
7. **`checkout/index.html` was registered as both mapped and excluded.** The `EXCLUDED_PAGES` entry was added by the same commit `f1b8d24d`. The page has no `robots` meta (indexable), is emitted into `sitemap.xml`, and already carries a generated `cg-related` block — so the new exclusion was the erroneous side, not the long-standing `PAGES` entry.
8. **`sw.js` declared `VERSION` twice** — `cg-v40` on line 19 and `cg-v66` on line 20. JavaScript keeps the later value, so the cache generation was functionally correct, but `tests/test_homepage_cinematic_motion.py` uses `re.search`, which matched the **first** declaration and failed its `>= 57` threshold. A latent trap: editing line 19 would change nothing.
9. **`helix.html` shipped unregistered across every generator** — absent from the effective cluster map and the authority-network discovery grid, missing the design-system CSS, global nav, a11y contract and Twitter card, missing the shared enhancement layer, and carrying a 274-character meta description against a 165-character budget.

### Gate status on `main` @ `e5df4c3c` before remediation

| Gate | Result |
|---|---|
| CI / Python Tests | **exit 2** — collection aborted, 0 of ~1,900 tests ran |
| CI / Lint (ruff) | **exit 1** — 12 × F601 duplicate dictionary keys |
| Internal links `--check` | **exit 1** — `helix.html` unclustered; `checkout/index.html` both mapped and excluded |
| Design system `--check` | **exit 1** — `helix.html` missing all four contracts |
| CI / Search discovery | **drift** — `helix.html` absent from `sitemap.xml` |

## HYPOTHESES

| Rank | Hypothesis | Confidence | Evidence | Disproving test | Risk |
|---|---|---:|---|---|---|
| 1 | Runner admission is blocked, so no gate feedback reaches `main` | Confirmed | Every run 2026-08-17→20 failed in 5–8s; 8/8 jobs with no steps; job logs 404 | One completed run with executed steps in the window | Low |
| 2 | Root `testpaths` covers a subtree whose dependencies the root extra never installs | Confirmed | Reproduced exit 2; all 5 modules resolve to one missing distribution; all pass with it installed | Collect that path with `sqlalchemy` hidden and see it succeed | Low |
| 3 | A duplicated `CLUSTERS` literal silently reverted #1500's page registration | Confirmed | 12 × F601; `helix.html` present only in the overridden copy | The live copy containing `helix.html` | Low |
| 4 | Commerce test code is itself broken | Rejected | 274/274 pass with `sqlalchemy` present, zero skipped | A failure that persists once the dependency is installed | Low |
| 5 | `checkout/index.html` should be excluded from the discovery graph | Rejected | Indexable, in the sitemap, already carries a generated block; the exclusion was added today | A `noindex` meta on the page | Low |

## ACTIONS TAKEN

All on `claude/sre-incident-diagnosis-2plxct`, branched from `e5df4c3c`. No production state was altered.

| # | Change | Files |
|---|---|---|
| 1 | `pytest.importorskip` guards on the modules reaching the database stack, matching the convention in `test_resilience.py` | `test_approval_executor.py`, `test_fulfillment.py`, `test_order_routing.py`, `test_route_auth_coverage.py`, `test_sales_ops_briefing.py`, `test_workspace.py` |
| 2 | Deleted the dead expanded `CLUSTERS` copy; added `helix.html` to the live intelligence cluster | `tools/internal_links.py` |
| 3 | Removed the erroneous `checkout/index.html` exclusion, restoring the page to `PAGES` and the services cluster | `tools/internal_links.py` |
| 4 | Removed the stale duplicate `var VERSION`; bumped `cg-v66` → `cg-v67` for the 11 changed pages | `sw.js` |
| 5 | Registered `helix.html`: design-system contracts, authority-grid link, shared enhancement layer, meta description trimmed to 161 chars | `helix.html`, `authority-network.html` |
| 6 | Regenerated derived assets | `sitemap.xml`, `feed.xml`, `data/seo/page-intents.json`, `SITE_WIRING_PLAN.md`, `DESIGN_SYSTEM_AUDIT.md`, 11 pages' generated blocks |
| 7 | Added the collection-integrity regression test | `tests/test_root_collection_integrity.py` |
| 8 | Documented the hazard; corrected the CI description | `docs/ACTIONS_BILLING_FALLBACK.md`, `CLAUDE.md` |

### On guarding rather than installing

`sqlalchemy` was deliberately **not** added to the root `[test]` extra. `CLAUDE.md` warns that a silently skipped money-movement test is worse than a loud failure, so the load-bearing question was whether guarding weakens the commerce gate. It does not: in the commerce environment the suite runs **274 passed, 0 skipped**, including all 7 tests in `test_route_auth_coverage.py` and all 24 in `test_workspace.py`. `importorskip` skips only where the dependency is genuinely absent — the root job, which was never that gate's venue and where the alternative was not "runs" but "aborts everything". Installing it there would also duplicate commerce's pinned dependency set in a second place, inviting drift between two suites that must agree.

### On deleting the dead cluster block

The two copies were compared programmatically before either was touched. Because the duplicate wins at evaluation time, deleting the expanded copy is functionally inert — it changes no cluster membership. The only content unique to the dead copy was `helix.html`, which was re-added to the live map explicitly.

### What was deliberately *not* added

An earlier draft of this work added `scripts/gate_preflight.py`, a local gate runner. That was **dropped**: `scripts/ci_local.py` already exists on `main`, already runs the ci.yml gate set, and is itself covered by `tests/test_ci_local.py`, which asserts it omits no job. A second runner would compete with it and could drift into reporting green over gates it does not run. The existing tool is referenced instead.

## ROOT CAUSE

**Primary.** GitHub-hosted runner admission is blocked before user code executes, so a workflow that never started and one that failed are indistinguishable in the Actions tab — both show a red conclusion with no executed steps. Gate feedback stopped; merges did not.

**Secondary, and the reason it went unnoticed so long.** `pyproject.toml` pointed root `testpaths` at the commerce subtree without the root `[test]` extra providing that subtree's database dependency. pytest aborts the *whole* run on a collection error, so one unsatisfied import in one module silenced ~1,900 tests while reporting zero failures. Its worst property is its shape: a suite that runs nothing resembles a suite that passes far more than one that fails.

**Why existing controls did not prevent it.** The controls were sound and their coverage was complete; their *execution* was not. `tests/test_design_system.py`, `test_internal_links.py` and `test_authority_network.py` would each have caught their regression on the commit that introduced it. Some could not run at all, because the collection abort preceded them; the rest never ran, because no runner started. Repository-side engineering cannot fix an account-level billing condition — but it can stop that condition from being *invisible*, which is what `scripts/ci_local.py` exists for and what nothing compelled anyone to run.

The pattern is self-illustrating. The 2026-08-14 response added a regression test to prevent recurrence, and that file shipped a lint error and a stale provenance hash. Six days later, #1500 added a page to a dictionary key that had been silently overridden, and nothing said otherwise.

## FIX

1. **Guards** on the six commerce modules that reach the database stack at import or call time. Root collection completes; the commerce gate is untouched.
2. **De-duplicated `CLUSTERS`**, restoring #1500's intended registration of `helix.html`.
3. **Resolved the `checkout/index.html` contradiction** on the evidence of the page's own indexability.
4. **Repaired `sw.js`** and bumped the cache generation.
5. **Registered `helix.html`** across the generators that govern a shipped public page.

**Rollback:** revert the branch, or `git revert` the single commit. No production state, DNS, billing, secret, Pages setting, or database was touched.

## VERIFICATION

| Check | Result |
|---|---|
| Root suite, root CI env (no `sqlalchemy`) | **1,959 passed, 40 skipped — exit 0** (was exit 2, 0 tests run) |
| Commerce suite, commerce env | **274 passed, 0 skipped — exit 0** |
| `ruff check .` | **exit 0** (was 12 errors) |
| `tools/internal_links.py --check` | **all 179 pages current — exit 0** |
| `tools/design_system.py --check` | **current across 194 routes — exit 0** |
| `scripts/site_reliability_audit.py` | **0 errors, 0 warnings — exit 0** |
| `scripts/ci_local.py` | see the run summary in the pull request |

**The regression test was verified against the defect, not merely observed to pass.** With one guard reverted, `tests/test_root_collection_integrity.py` fails with `assert 2 in (0, 5)` and reports `204 tests collected, 1 error`; with the guard restored it passes in both environments. A test that has never failed proves nothing.

**Not verified, and not claimed:**

- No GitHub-hosted CI job has executed against this branch. This work is **locally verified, not CI-verified**.
- Lighthouse budgets and the Playwright browser suites were not run.
- No production deployment or Pages publish was performed or requested.
- Billing-account state remains unread.

## PREVENTION

- **Regression test.** `tests/test_root_collection_integrity.py` collects the commerce testpath in a subprocess with `sqlalchemy` and `stripe` hidden from the import system, reproducing the real condition rather than pattern-matching source, so the transitive case is caught. It is honest about its limits: it cannot rescue a root run that has already aborted (that aborts this module too). Its value is that a contributor or CI job *with* the full stack installed — where the breakage is otherwise invisible — sees it at the moment it is introduced.
- **Use the runner that already exists.** `scripts/ci_local.py` runs the ci.yml gate set locally and reports a missing tool as SKIP with the line "Skipped gates were not verified — do not read this as a green run." The runbook now directs operators to run it before merging while the lock is active.
- **Corrected guidance.** `CLAUDE.md` described the root job as `pytest tests/`. It runs bare `pytest` across all four `testpaths` — the misreading that let this land twice. It now documents the real scope, the missing-dependency hazard, and the guard requirement.

## RISKS AND UNKNOWNS

- **Whether hosted CI passes on this branch is unknown** and unknowable until runner admission is restored. Local verification narrows this gap; it does not close it.
- **The billing lock is unaddressed.** It is an account-level condition outside this repository. Every finding here will recur in a future lock unless `scripts/ci_local.py` is actually run during one — the tool existed throughout this incident and nothing required its use.
- **Duplicate content observed but not fixed:** `authority-network.html` carries two near-identical "ClearGlass Intelligence" cluster articles (the blog cluster, rendered twice). No gate covers it and it is unrelated to this incident's failures, so it was left alone rather than widened into scope. It is the same duplication signature as the `CLUSTERS` literal and is worth a look.
- **`helix.html`'s meta description was rewritten** to fit the 165-character budget. The wording is mine, derived from the page's existing `og:description`; it deserves a human read for voice.
- **Design-system chrome is now injected into `helix.html`.** That is the documented default for a public page, but its rendering was not visually verified — Playwright and Lighthouse need runners.

## APPROVAL REQUIRED

Nothing below was performed.

1. **Merge to `main`.** Expected: five gates return green and the root suite runs ~1,959 tests instead of zero. Rollback: `git revert` the merge. Blast radius: CI configuration, test guards, generated site assets, and two public pages (`helix.html`, `authority-network.html`) — no runtime service, database, or customer-data path.
2. **Restore Actions runner admission** — an account-level billing action outside this repository. Afterwards, re-run `CI` and confirm the Python Tests job reports executed steps and a real test count rather than an empty step list.
3. **Actions-backed production deployment** — unchanged from the 2026-08-14 report; it should follow, not precede, a verified green CI run on real runners.

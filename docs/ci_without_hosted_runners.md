# Validating changes when GitHub Actions will not start

## What this is for

Since 2026-08-12 every workflow in this repository has failed without executing a
single step. The signature is unmistakable and worth being able to recognise:

| Signal | Value on a rejected job |
|---|---|
| `runner_id` / `runner_name` | `0` / empty — no runner was ever assigned |
| Duration | 3–6 seconds, for every job in parallel |
| Steps executed | none |
| Log download | HTTP 404 — no logs were produced |

A job that finishes in three seconds with no runner and no logs never reached
`actions/checkout`, so it never saw the branch's contents. **A red check in this
state carries no information about the code.** `.github/workflows/auto-heal.yml`
names the cause in its circuit-breaker comment: the account is locked for
billing.

The practical consequence is that merges land unvalidated. Five separate rounds
of breakage reached `main` this way, including a homepage truncated to a
head-only fragment, a `sitemap.xml` that was not well-formed XML, and a syntax
error that stopped pytest collecting **any** of the repository's tests.

## Do this before every merge, until Actions is back

```bash
python3 scripts/ci_local.py            # every gate
python3 scripts/ci_local.py --fast     # skip the two that need the network
python3 scripts/ci_local.py --list     # what the gate set covers
```

The runner executes the same commands `.github/workflows/ci.yml` runs, in the
same order, and exits non-zero if any gate fails. `tests/test_ci_local.py`
asserts it covers every job in `ci.yml`, so it cannot quietly drop a gate and
report green — that failure mode would be worse than having no runner at all.

Gates needing `npm` or the network are reported as **SKIP**, never as pass, and
the summary says explicitly that a skipped gate was not verified.

To stop unvalidated pushes at the source:

```bash
python3 scripts/ci_local.py --install-hook   # pre-push hook, runs --fast
```

Bypass a single push with `git push --no-verify`.

## Restoring real CI

### Option 1 — clear the billing lock (the only complete fix)

Settings → Billing → Actions, and Settings → Actions → General. Nothing in this
repository substitutes for it. Once runners return, **re-running the failed jobs
on the already-merged commits is the real confirmation** — no new push is
needed, and every "verified locally" claim in the recent PR history should be
re-checked that way.

### Option 2 — self-hosted runners (works for a spending limit, not for a lock)

Self-hosted runners do not consume GitHub-hosted minutes, so they keep working
when a *spending limit* or an exhausted included-minutes allowance is what
blocks hosted jobs. They do **not** help if Actions has been disabled
account-wide, which is what a billing lock can do.

Which case applies here has not been confirmed from inside this repository —
billing state is not visible to it. The distinction is cheap to settle: register
one runner, point one workflow at it, and see whether a job starts.

```bash
# on a machine you control, from Settings → Actions → Runners → New runner
./config.sh --url https://github.com/ClearGlassInc/ClearGlassIncorporated-Desmond --token <token>
./run.sh
```

Then change the job you are testing:

```yaml
jobs:
  python-tests:
    runs-on: self-hosted        # was: ubuntu-latest
```

All 137 jobs in this repository currently specify `runs-on: ubuntu-latest`. Move
them deliberately and one at a time rather than in bulk — a self-hosted runner
executes untrusted workflow code on your own hardware, so it wants a dedicated,
disposable machine, not a workstation with credentials on it.

## What not to do

- **Do not disable or bypass required checks to merge.** The checks are the only
  thing that would have caught the five regressions above. A red check that
  never ran is uninformative, not permission to skip the gate.
- **Do not mark a check green by hand.** A status that claims a run happened when
  none did is worse than the outage, because it is indistinguishable from a real
  pass afterwards.
- Run `scripts/ci_local.py` instead and paste its summary into the PR, so a
  reviewer can see exactly which gates were verified and which were skipped.

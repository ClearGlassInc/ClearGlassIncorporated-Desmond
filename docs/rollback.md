# Rollback Runbook

How to safely undo a deployment or a bad change. Every path below is reversible
and requires no paid services for the static site.

See also: `docs/DEPLOYMENT.md` (§4 Rollback) for the deployment architecture.

---

## 1. Static site (GitHub Pages) — most common

The site is published from `main` by `.github/workflows/pages.yml`. To roll back
a bad publish, revert on `main` and let the workflow redeploy.

### Fast path — revert the offending commit(s)

```bash
git fetch origin main
git checkout main && git pull origin main
git revert --no-edit <bad_sha>        # or a range: <first>^..<last>
git push origin main
```

The `Deploy GitHub Pages` workflow re-runs on push and republishes the reverted
tree. Confirm the run is green under **Actions → Deploy GitHub Pages**.

### Roll back to a known-good commit (multiple bad commits)

```bash
git checkout main && git pull origin main
git revert --no-commit <good_sha>..HEAD
git commit -m "Roll back site to <good_sha>"
git push origin main
```

Prefer `revert` over force-pushing `main` — it preserves history and keeps the
audit trail intact. Only force-push `main` if you fully understand the impact.

### Re-deploy without a code change

If the tree is correct but a deploy failed transiently, re-run the last
successful workflow: **Actions → Deploy GitHub Pages → Run workflow**
(`workflow_dispatch` is enabled).

---

## 2. Commerce control plane (Render)

The commerce backend deploys independently via `commerce-deploy.yml` and an
optional Render deploy hook.

- **Preferred:** Render dashboard → the service → **Deploys** → pick the last
  healthy deploy → **Rollback**.
- **Automated:** if `RENDER_ROLLBACK_HOOK_URL` is configured (see
  `docs/secrets.md`), trigger it to redeploy the previous image:

  ```bash
  curl -fsS -X POST "$RENDER_ROLLBACK_HOOK_URL"
  ```

- **Governance safety:** rolling the backend never bypasses the
  read-only → draft → approval → execute model. High/critical actions remain
  blocked until an `approvals` row is `approved`; a rollback does not
  auto-approve anything.

---

## 3. Reverting a workflow change

Workflow files are versioned like any other file. To restore a prior version:

```bash
git checkout <good_sha> -- .github/workflows/<file>.yml
git commit -m "Revert <file>.yml to <good_sha>"
git push origin main
```

Validate before pushing:

```bash
python scripts/workflow_doctor.py          # workflow lint / policy gate
python scripts/site_reliability_audit.py   # links, assets, sitemap, SEO
```

---

## 4. Verifying a rollback succeeded

```bash
python -m pytest tests/ -q                 # 423 tests
ruff check .                               # lint
python scripts/site_reliability_audit.py   # site integrity
```

Then confirm the live site (or `curl -I` the affected page) reflects the
reverted state and the relevant Actions run is green.

---

## ClearGlassInc Artemis validation rollback addendum

After any rollback, run the consolidated static validation gate before redeploying:

```bash
python scripts/validate-site
python scripts/check-links
python scripts/audit-assets
```

If agent routing changes caused the rollback, revert `agents/company_system/agent_registry.json`, then rerun the same validation commands.

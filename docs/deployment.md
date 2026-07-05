# Deployment Runbook Alias

This file exists because some tooling and prompts reference `docs/deployment.md` while the canonical runbook is `docs/DEPLOYMENT.md`.

Use the canonical deployment and operations runbook here:

- `docs/DEPLOYMENT.md`

Core rule: GitHub Pages deployment is handled by `.github/workflows/pages.yml` on merge to `main`, with no paid service and no required repository secret. Optional external deploy hooks must remain guarded and documented in `docs/secrets.md`.

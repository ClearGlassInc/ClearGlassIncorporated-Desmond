# ClearGlassInc Artemis Deployment Guide

## Core deployment

The production website deploys from `main` to GitHub Pages through `.github/workflows/pages.yml` using GitHub Actions Pages artifacts. Core deployment requires no paid services and no external secrets.

Required job permissions:

```yaml
contents: read
pages: write
id-token: write
```

## Local validation

```bash
python scripts/validate-site
python scripts/check-links
python scripts/audit-assets
python scripts/site_reliability_audit.py
```

## Manual deploy

1. Push to `main`, or open **Actions → Deploy GitHub Pages → Run workflow**.
2. Confirm the validation step passes.
3. Confirm `upload-pages-artifact` uploads `.` as the static artifact.
4. Confirm `deploy-pages` reports the `github-pages` environment URL.

## Optional Pages admin token

`PAGES_ADMIN_TOKEN` is optional. If present, the workflow attempts to pin repository Pages source to **GitHub Actions** to avoid legacy branch-build failures. Without it, deployment still continues.

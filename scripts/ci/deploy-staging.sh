#!/usr/bin/env bash
set -euo pipefail
[ "${EMERGENCY_STOP:-true}" = false ] || { echo 'NOT VERIFIED: emergency stop active' >&2; exit 2; }
[ "${DRY_RUN:-true}" = false ] || { echo 'NOT VERIFIED: dry_run=true' >&2; exit 2; }
[ "${TARGET_ENVIRONMENT:-}" = staging ] || { echo 'NOT VERIFIED: staging target required' >&2; exit 2; }
: "${FLY_API_TOKEN:?NOT VERIFIED: FLY_API_TOKEN missing from staging-deploy context}"
[ "${STAGING_FLY_APP:-REPLACE_ME}" != REPLACE_ME ] || { echo 'NOT VERIFIED: STAGING_FLY_APP missing' >&2; exit 2; }
bash scripts/ci/fly_deploy.sh staging
mkdir -p artifacts/evidence
cp -R deploy-evidence/. artifacts/evidence/
printf '%s\n' '{"status":"PASS","provider":"Fly.io","environment":"staging"}' > artifacts/evidence/staging-deploy.json
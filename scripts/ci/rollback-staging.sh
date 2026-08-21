#!/usr/bin/env bash
set -euo pipefail
[ "${EMERGENCY_STOP:-true}" = false ] || { echo 'NOT VERIFIED: emergency stop active' >&2; exit 2; }
[ "${TARGET_ENVIRONMENT:-}" = staging ] || { echo 'NOT VERIFIED: staging rollback target required' >&2; exit 2; }
: "${FLY_API_TOKEN:?NOT VERIFIED: FLY_API_TOKEN missing from staging-deploy context}"
[ -s deploy-evidence/staging-previous-image.txt ] || { echo 'NOT VERIFIED: no recorded prior staging image' >&2; exit 2; }
bash scripts/ci/fly_rollback.sh staging
mkdir -p artifacts/evidence
cp -R deploy-evidence/. artifacts/evidence/
printf '%s\n' '{"status":"PASS","provider":"Fly.io","environment":"staging","rollback":"previous-recorded-immutable-image"}' > artifacts/evidence/staging-rollback.json
#!/usr/bin/env bash
set -euo pipefail
[ "${EMERGENCY_STOP:-true}" = false ] || { echo 'NOT VERIFIED: emergency stop active' >&2; exit 2; }
[ "${TARGET_ENVIRONMENT:-}" = production ] || { echo 'NOT VERIFIED: production rollback target required' >&2; exit 2; }
[ -n "${CHANGE_REFERENCE:-}" ] || { echo 'NOT VERIFIED: change reference required' >&2; exit 2; }
: "${FLY_API_TOKEN:?NOT VERIFIED: FLY_API_TOKEN missing from production-deploy context}"
[ -s deploy-evidence/production-previous-image.txt ] || { echo 'NOT VERIFIED: no recorded prior production image' >&2; exit 2; }
bash scripts/ci/fly_rollback.sh production
mkdir -p artifacts/evidence
cp -R deploy-evidence/. artifacts/evidence/
printf '%s\n' '{"status":"PASS","provider":"Fly.io","environment":"production","rollback":"previous-recorded-immutable-image"}' > artifacts/evidence/production-rollback.json
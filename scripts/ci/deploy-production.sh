#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
[ "${EMERGENCY_STOP:-true}" = false ] || { echo 'NOT VERIFIED: emergency stop active' >&2; exit 2; }
[ "${DRY_RUN:-true}" = false ] || { echo 'NOT VERIFIED: dry_run=true' >&2; exit 2; }
[ "${TARGET_ENVIRONMENT:-}" = production ] || { echo 'NOT VERIFIED: production target required' >&2; exit 2; }
[ -n "${CHANGE_REFERENCE:-}" ] || { echo 'NOT VERIFIED: change reference required' >&2; exit 2; }
[ -f release-bundle.tar.gz ] || { echo 'NOT VERIFIED: immutable artifact missing' >&2; exit 2; }
DEPLOY_COMMAND='REPLACE_ME_DEPLOY_COMMAND'
PRODUCTION_URL='REPLACE_ME_PRODUCTION_URL'
[ "$DEPLOY_COMMAND" != REPLACE_ME_DEPLOY_COMMAND ] || { echo 'NOT VERIFIED: REPLACE_ME_DEPLOY_COMMAND' >&2; exit 2; }
[ "$PRODUCTION_URL" != REPLACE_ME_PRODUCTION_URL ] || { echo 'NOT VERIFIED: REPLACE_ME_PRODUCTION_URL' >&2; exit 2; }
# shellcheck disable=SC2086
$DEPLOY_COMMAND release-bundle.tar.gz
python3 - <<'PY'
import json,os
json.dump({'status':'PASS','environment':'production','artifact':'release-bundle.tar.gz','change_reference':os.getenv('CHANGE_REFERENCE','')},open('artifacts/evidence/production-deploy.json','w'),indent=2)
PY
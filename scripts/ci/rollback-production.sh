#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
[ "${EMERGENCY_STOP:-true}" = false ] || { echo 'NOT VERIFIED: emergency stop active' >&2; exit 2; }
[ "${TARGET_ENVIRONMENT:-}" = production ] || { echo 'NOT VERIFIED: production rollback target required' >&2; exit 2; }
[ -n "${CHANGE_REFERENCE:-}" ] || { echo 'NOT VERIFIED: change reference required' >&2; exit 2; }
ROLLBACK_COMMAND='REPLACE_ME_DEPLOY_COMMAND'
LAST_VERIFIED_ARTIFACT='REPLACE_ME_LAST_VERIFIED_PRODUCTION_ARTIFACT'
[ "$ROLLBACK_COMMAND" != REPLACE_ME_DEPLOY_COMMAND ] || { echo 'NOT VERIFIED: production rollback adapter not configured' >&2; exit 2; }
[ "$LAST_VERIFIED_ARTIFACT" != REPLACE_ME_LAST_VERIFIED_PRODUCTION_ARTIFACT ] || { echo 'NOT VERIFIED: prior verified production release lookup not configured' >&2; exit 2; }
# shellcheck disable=SC2086
$ROLLBACK_COMMAND "$LAST_VERIFIED_ARTIFACT"
python3 - <<'PY'
import json,os
json.dump({'status':'PASS','environment':'production','rollback':'verified-artifact-only','change_reference':os.getenv('CHANGE_REFERENCE','')},open('artifacts/evidence/production-rollback.json','w'),indent=2)
PY
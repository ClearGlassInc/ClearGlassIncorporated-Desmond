#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
[ "${EMERGENCY_STOP:-true}" = false ] || { echo 'NOT VERIFIED: emergency stop active' >&2; exit 2; }
[ "${DRY_RUN:-true}" = false ] || { echo 'NOT VERIFIED: dry_run=true' >&2; exit 2; }
[ "${TARGET_ENVIRONMENT:-}" = staging ] || { echo 'NOT VERIFIED: staging target required' >&2; exit 2; }
[ -f release-bundle.tar.gz ] || { echo 'NOT VERIFIED: immutable artifact missing' >&2; exit 2; }
command -v flyctl >/dev/null 2>&1 || { echo 'NOT VERIFIED: pinned flyctl is required in staging-deploy context' >&2; exit 2; }
: "${FLY_API_TOKEN:?NOT VERIFIED: FLY_API_TOKEN missing}"
app="${STAGING_FLY_APP:-REPLACE_ME_STAGING_FLY_APP}"
[ "$app" != REPLACE_ME_STAGING_FLY_APP ] || { echo 'NOT VERIFIED: staging Fly app not configured' >&2; exit 2; }
image="registry.fly.io/${app}:sha-${CIRCLE_SHA1}"
flyctl status --app "$app" --json > artifacts/evidence/staging-before.json
flyctl deploy --app "$app" --image "$image" --strategy immediate --yes
printf '%s\n' "${image}" > artifacts/evidence/staging-release-image.txt
python3 - <<'PY'
import json,os
json.dump({'status':'PASS','provider':'Fly.io','app':os.getenv('STAGING_FLY_APP',''),'image':'registry.fly.io/'+os.getenv('STAGING_FLY_APP','')+':sha-'+os.getenv('CIRCLE_SHA1','')},open('artifacts/evidence/staging-deploy.json','w'),indent=2)
PY
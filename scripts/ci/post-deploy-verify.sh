#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
url=''
case "${TARGET_ENVIRONMENT:-}" in staging) url='REPLACE_ME_STAGING_URL';; production) url='REPLACE_ME_PRODUCTION_URL';; *) echo 'NOT VERIFIED: target environment' >&2; exit 2;; esac
[ "$url" != REPLACE_ME_STAGING_URL ] && [ "$url" != REPLACE_ME_PRODUCTION_URL ] || { echo 'NOT VERIFIED: deployment URL is not configured' >&2; exit 2; }
status=$(curl --silent --show-error --location --max-time 20 --connect-timeout 5 --output /tmp/body --dump-header /tmp/headers --write-out '%{http_code}' "$url") || { echo 'NOT VERIFIED: endpoint unavailable' >&2; exit 2; }
[ "$status" = 200 ] || { echo "NOT VERIFIED: HTTP status $status" >&2; exit 2; }
digest=$(sha256sum /tmp/body | awk '{print $1}')
# A configured marker is required; do not infer version from mutable content.
marker='REPLACE_ME_HEALTH_ENDPOINT'
if [ "$marker" != REPLACE_ME_HEALTH_ENDPOINT ]; then curl --fail --silent --show-error --max-time 10 "$marker" >/tmp/health.json; fi
if [ "${TARGET_ENVIRONMENT}" = production ]; then
  monitor='REPLACE_ME_READONLY_MONITORING_API'
  [ "$monitor" != REPLACE_ME_READONLY_MONITORING_API ] || { echo 'NOT VERIFIED: production error-rate monitoring integration is not configured' >&2; exit 2; }
fi
python3 - "$status" "$digest" <<'PY'
import json,os,sys,time
json.dump({'status':'PASS','environment':os.environ['TARGET_ENVIRONMENT'],'http_status':int(sys.argv[1]),'body_sha256':sys.argv[2],'verified_at_epoch':time.time(),'headers_file':'/tmp/headers'},open('artifacts/evidence/post-deploy-verification.json','w'),indent=2)
PY
cat /tmp/headers | sed -E 's/([Aa]uthorization:|[Ss]et-[Cc]ookie:).*/\1 [REDACTED]/' > artifacts/evidence/response-headers.txt
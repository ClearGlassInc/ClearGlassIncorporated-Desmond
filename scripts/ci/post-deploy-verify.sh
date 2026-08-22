#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
ENVIRONMENT="${1:-${TARGET_ENVIRONMENT:-}}"
[[ "$ENVIRONMENT" == staging || "$ENVIRONMENT" == production ]] || { echo 'usage: post-deploy-verify.sh staging|production' >&2; exit 2; }
case "$ENVIRONMENT" in
  staging) url="${STAGING_URL:-REPLACE_ME_STAGING_URL}" ;;
  production) url="${PRODUCTION_URL:-REPLACE_ME_PRODUCTION_URL}" ;;
esac
[[ "$url" != REPLACE_ME_STAGING_URL && "$url" != REPLACE_ME_PRODUCTION_URL ]] || { echo 'NOT VERIFIED: HTTPS URL unconfigured' >&2; exit 2; }
status="$(curl --silent --show-error --location --max-time 20 --connect-timeout 5 --output /tmp/body --dump-header /tmp/headers --write-out '%{http_code}' "$url")" || { echo 'NOT VERIFIED: endpoint unavailable' >&2; exit 2; }
[[ "$status" == 200 ]] || { echo "NOT VERIFIED: HTTP status $status" >&2; exit 2; }
marker="${RELEASE_MARKER:-REPLACE_ME_RELEASE_MARKER}"
[[ "$marker" != REPLACE_ME_RELEASE_MARKER ]] || { echo 'NOT VERIFIED: release marker unconfigured' >&2; exit 2; }
grep -Fq -- "$marker" /tmp/body || { echo 'NOT VERIFIED: release marker missing' >&2; exit 2; }
digest="$(sha256sum /tmp/body | awk '{print $1}')"
python3 - "$ENVIRONMENT" "$status" "$digest" "$marker" <<'PY'
import json,sys,time
m={'status':'PASS','environment':sys.argv[1],'http_status':int(sys.argv[2]),'response_sha256':sys.argv[3],'release_marker':sys.argv[4],'verified_at_epoch':time.time()}
json.dump(m,open('artifacts/evidence/post-deploy-verification.json','w'),indent=2); print()
PY
sed -E 's/([Aa]uthorization:|[Ss]et-[Cc]ookie:).*/\1 [REDACTED]/' /tmp/headers > artifacts/evidence/response-headers.txt

#!/usr/bin/env bash
set -euo pipefail
ENVIRONMENT=${1:?environment required}
[[ "$ENVIRONMENT" == staging || "$ENVIRONMENT" == production ]] || exit 2
if [[ "$ENVIRONMENT" == staging ]]; then APP="${STAGING_FLY_APP:-REPLACE_ME_STAGING_FLY_APP}"; URL="${STAGING_HEALTH_URL:-}"; else APP="${PRODUCTION_FLY_APP:-clearglass-agent-service}"; URL="${PRODUCTION_HEALTH_URL:-}"; fi
[[ "$APP" != REPLACE_ME* ]] || { echo 'health verification app not configured' >&2; exit 1; }
mkdir -p deploy-evidence
if [ -z "$URL" ]; then URL="https://${APP}.fly.dev/health"; fi
printf '%s\n' "$URL" > "deploy-evidence/${ENVIRONMENT}-verified-url.txt"
for i in $(seq 1 20); do curl --fail --silent --show-error --max-time 10 "$URL" >/dev/null || { echo "health check $i/20 failed" >&2; exit 1; }; done
if command -v flyctl >/dev/null; then flyctl status --app "$APP" --json > "deploy-evidence/${ENVIRONMENT}-status.json"; fi
printf '%s\n' "environment=$ENVIRONMENT" "revision=$CIRCLE_SHA1" 'health_checks=20/20' 'error_rate=0%' 'status=PASS' > "deploy-evidence/${ENVIRONMENT}-verification.txt"

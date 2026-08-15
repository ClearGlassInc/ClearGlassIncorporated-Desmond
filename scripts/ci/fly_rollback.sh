#!/usr/bin/env bash
set -euo pipefail

environment="${1:-}"
case "$environment" in
  staging|production) ;;
  *) echo "ERROR: usage: $0 <staging|production>" >&2; exit 2 ;;
esac

if [ -z "${FLY_API_TOKEN:-}" ]; then
  echo "ERROR: FLY_API_TOKEN is required for rollback." >&2
  exit 2
fi

if [ "$environment" = "staging" ]; then
  app="${STAGING_FLY_APP:-REPLACE_ME}"
  health_url="${STAGING_HEALTH_URL:-}"
else
  app="${PRODUCTION_FLY_APP:-clearglass-agent-service}"
  health_url="${PRODUCTION_HEALTH_URL:-}"
fi

if [ -z "$app" ] || [ "$app" = "REPLACE_ME" ]; then
  echo "ERROR: ${environment} Fly.io app is not configured." >&2
  exit 2
fi
if [ -z "$health_url" ]; then
  health_url="https://${app}.fly.dev/health"
fi

previous_file="deploy-evidence/${environment}-previous-image.txt"
[ -s "$previous_file" ] || {
  echo "ERROR: rollback evidence is missing: ${previous_file}" >&2
  exit 2
}
previous_image="$(cat "$previous_file")"

bash scripts/ci/install_flyctl.sh
if [ -x "$HOME/.fly/bin/flyctl" ]; then
  flyctl_bin="$HOME/.fly/bin/flyctl"
else
  flyctl_bin="$(command -v flyctl)"
fi

echo "Rolling ${environment} back to the recorded previous immutable image."
"$flyctl_bin" deploy --app "$app" --image "$previous_image"

for attempt in 1 2 3 4 5 6; do
  code="$(curl --silent --show-error --output /tmp/rollback-health.json \
    --write-out '%{http_code}' --max-time 30 "$health_url" || true)"
  if [ "$code" = "200" ]; then
    printf 'rollback=%s\nimage=%s\nhealth=PASS\n' "$environment" "$previous_image" \
      > "deploy-evidence/${environment}-rollback-result.txt"
    echo "${environment} rollback: PASS"
    exit 0
  fi
  sleep 10
done

echo "ERROR: rollback completed but health verification did not recover." >&2
exit 1

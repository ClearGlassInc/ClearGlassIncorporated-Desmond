#!/usr/bin/env bash
set -euo pipefail
ENVIRONMENT=${1:?environment required}; ACTION=${2:-deploy}
[[ "$ENVIRONMENT" == staging || "$ENVIRONMENT" == production ]] || { echo 'invalid environment' >&2; exit 2; }
[[ "${EMERGENCY_STOP:-false}" == false ]] || { echo 'EMERGENCY STOP ACTIVE' >&2; exit 1; }
command -v flyctl >/dev/null || { echo 'flyctl is required in deploy context' >&2; exit 1; }
[ -n "${FLYCTL_VERSION:-}" ] && [ "$FLYCTL_VERSION" != latest ] || { echo 'FLYCTL_VERSION must be an exact approved version' >&2; exit 1; }
flyctl version | grep -F "$FLYCTL_VERSION" >/dev/null || { echo 'flyctl version mismatch' >&2; exit 1; }
if [[ "$ENVIRONMENT" == staging ]]; then APP="${STAGING_FLY_APP:-REPLACE_ME_STAGING_FLY_APP}"; HEALTH="${STAGING_HEALTH_URL:-}"; else APP="${PRODUCTION_FLY_APP:-clearglass-agent-service}"; HEALTH="${PRODUCTION_HEALTH_URL:-}"; fi
[[ "$APP" != REPLACE_ME* ]] || { echo "${ENVIRONMENT} app is not configured" >&2; exit 1; }
mkdir -p deploy-evidence
if [[ "$ACTION" == rollback ]]; then
  [ -s "deploy-evidence/${ENVIRONMENT}-previous-image.txt" ] || { echo 'previous immutable image evidence missing; rollback refused' >&2; exit 1; }
  IMAGE=$(cat "deploy-evidence/${ENVIRONMENT}-previous-image.txt")
  flyctl deploy --app "$APP" --image "$IMAGE" --yes
  printf '%s\n' "$IMAGE" > "deploy-evidence/${ENVIRONMENT}-rollback-image.txt"
  exit 0
fi
IMAGE="${FLY_IMAGE_REF:-REPLACE_ME_IMMUTABLE_IMAGE_REF}"
[[ "$IMAGE" != REPLACE_ME* ]] || { echo 'FLY_IMAGE_REF must be an immutable commit-addressed image reference' >&2; exit 1; }
[[ "$IMAGE" == *"sha-$CIRCLE_SHA1"* || "$IMAGE" == *"@sha256:"* ]] || { echo 'image must be commit-addressed or digest-pinned' >&2; exit 1; }
flyctl releases --app "$APP" --json > "deploy-evidence/${ENVIRONMENT}-releases-before.json"
flyctl image show "$APP" --json > "deploy-evidence/${ENVIRONMENT}-previous-image.json" || true
flyctl image show "$APP" --json | grep -Eo 'registry[^" ]+|[A-Za-z0-9._/-]+@sha256:[a-f0-9]{64}' | head -1 > "deploy-evidence/${ENVIRONMENT}-previous-image.txt" || true
[ -s "deploy-evidence/${ENVIRONMENT}-previous-image.txt" ] || { echo 'previous immutable image could not be recorded; refusing deployment' >&2; exit 1; }
flyctl deploy --app "$APP" --image "$IMAGE" --yes
printf '%s\n' "$IMAGE" > "deploy-evidence/${ENVIRONMENT}-deployed-image.txt"
printf '%s\n' "$HEALTH" > "deploy-evidence/${ENVIRONMENT}-health-url.txt"

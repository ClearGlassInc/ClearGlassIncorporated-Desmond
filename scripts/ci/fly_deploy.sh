#!/usr/bin/env bash
set -euo pipefail

environment="${1:-}"
case "$environment" in
  staging|production) ;;
  *) echo "ERROR: usage: $0 <staging|production>" >&2; exit 2 ;;
esac

if [ "${EMERGENCY_STOP:-false}" != "false" ]; then
  echo "ERROR: emergency_stop prevents deployment." >&2
  exit 2
fi
if [ "${ENABLE_AGENTS:-false}" != "false" ]; then
  echo "ERROR: agent activation is not configured; deployment stopped." >&2
  exit 2
fi
if [ "${DEPLOY_ANIMATIONS:-false}" != "false" ]; then
  echo "ERROR: animation publication adapter is REPLACE_ME; deployment stopped." >&2
  exit 2
fi
if [ -z "${FLY_API_TOKEN:-}" ]; then
  echo "ERROR: FLY_API_TOKEN is required in the restricted deployment context." >&2
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
  echo "ERROR: ${environment} Fly.io app is not configured in its restricted CircleCI context." >&2
  exit 2
fi
if [ -z "$health_url" ]; then
  health_url="https://${app}.fly.dev/health"
fi

bash scripts/ci/install_flyctl.sh
if [ -x "$HOME/.fly/bin/flyctl" ]; then
  flyctl_bin="$HOME/.fly/bin/flyctl"
else
  flyctl_bin="$(command -v flyctl)"
fi

mkdir -p deploy-evidence

status_json="$("$flyctl_bin" status --app "$app" --json)"
previous_image="$(
  STATUS_JSON="$status_json" python - <<'PY'
import json
import os

data = json.loads(os.environ["STATUS_JSON"])
machines = data.get("Machines") or data.get("machines") or []
image = ""
if machines:
    machine = machines[0]
    config = machine.get("config") or machine.get("Config") or {}
    image = config.get("image") or config.get("Image") or ""
print(image)
PY
)"
if [ -z "$previous_image" ] || [ "$previous_image" = "null" ]; then
  echo "ERROR: no previous immutable image was found; refusing a deployment without rollback readiness." >&2
  exit 2
fi

printf '%s\n' "$previous_image" > "deploy-evidence/${environment}-previous-image.txt"
printf 'app=%s\nhealth_url=%s\ncommit=%s\n' \
  "$app" "$health_url" "$CIRCLE_SHA1" \
  > "deploy-evidence/${environment}-metadata.txt"

"$flyctl_bin" auth docker >/dev/null

image_tag="registry.fly.io/${app}:sha-${CIRCLE_SHA1}"
manifest_json=""
if manifest_json="$(docker manifest inspect --verbose "$image_tag" 2>/dev/null)"; then
  digest="$(
    MANIFEST_JSON="$manifest_json" python - <<'PY'
import json
import os

data = json.loads(os.environ["MANIFEST_JSON"])
if isinstance(data, list) and data:
    data = data[0]
descriptor = data.get("Descriptor") or data.get("descriptor") or {}
print(descriptor.get("digest") or "")
PY
  )"
  if [ -z "$digest" ]; then
    echo "ERROR: existing commit image did not expose a registry digest." >&2
    exit 2
  fi
  echo "Reusing existing versioned image for commit ${CIRCLE_SHA1}."
else
  echo "Building first immutable image for commit ${CIRCLE_SHA1}."
  docker build \
    -f services/clearglass_agent_service/Dockerfile \
    -t "$image_tag" \
    .
  push_log="$(mktemp)"
  trap 'rm -f "$push_log"' EXIT
  docker push "$image_tag" | tee "$push_log"
  digest="$(awk '/digest: sha256:/ {print $3}' "$push_log" | tail -n 1)"
  if [ -z "$digest" ]; then
    echo "ERROR: registry push did not return an immutable digest." >&2
    exit 2
  fi
fi

immutable_image="registry.fly.io/${app}@${digest}"
printf '%s\n' "$immutable_image" > "deploy-evidence/${environment}-deployed-image.txt"
printf 'rollback: flyctl deploy --app %q --image %q\n' \
  "$app" "$previous_image" \
  > "deploy-evidence/${environment}-rollback.txt"

rollback_staging() {
  if [ "$environment" != "staging" ]; then
    return 0
  fi
  echo "Staging deployment verification failed; restoring the previous immutable image."
  "$flyctl_bin" deploy --app "$app" --image "$previous_image"
  for attempt in 1 2 3 4 5 6; do
    code="$(curl --silent --show-error --output /tmp/rollback-health.json \
      --write-out '%{http_code}' --max-time 30 "$health_url" || true)"
    if [ "$code" = "200" ]; then
      echo "Staging rollback health verification: PASS"
      return 0
    fi
    sleep 10
  done
  echo "ERROR: staging rollback did not recover the health endpoint." >&2
  return 1
}

echo "Deploying ${environment} image digest ${digest}."
if ! "$flyctl_bin" deploy --app "$app" --image "$immutable_image"; then
  rollback_staging || true
  exit 1
fi

healthy=false
for attempt in 1 2 3 4 5 6; do
  code="$(curl --silent --show-error --output /tmp/health.json \
    --write-out '%{http_code}' --max-time 30 "$health_url" || true)"
  if [ "$code" = "200" ]; then
    healthy=true
    break
  fi
  echo "Health attempt ${attempt}: HTTP ${code}; retrying."
  sleep 10
done

if [ "$healthy" != "true" ]; then
  echo "ERROR: deployment endpoint verification failed." >&2
  rollback_staging || true
  exit 1
fi

printf 'deployment=%s\nimage=%s\nhealth=PASS\n' \
  "$environment" "$immutable_image" \
  >> "deploy-evidence/${environment}-metadata.txt"
echo "${environment} deployment and immediate endpoint verification: PASS"

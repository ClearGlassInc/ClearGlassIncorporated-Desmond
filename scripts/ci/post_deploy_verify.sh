#!/usr/bin/env bash
set -euo pipefail

environment="${1:-}"
case "$environment" in
  staging|production) ;;
  *) echo "ERROR: usage: $0 <staging|production>" >&2; exit 2 ;;
esac

if [ "${EMERGENCY_STOP:-false}" = "true" ]; then
  echo "ERROR: emergency_stop is active; post-deploy mutation/verification workflow halted." >&2
  exit 2
fi
if [ -z "${FLY_API_TOKEN:-}" ]; then
  echo "ERROR: FLY_API_TOKEN is required for deployment verification." >&2
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

expected_file="deploy-evidence/${environment}-deployed-image.txt"
[ -s "$expected_file" ] || {
  echo "ERROR: deployment evidence is missing: ${expected_file}" >&2
  exit 2
}
expected_image="$(cat "$expected_file")"

bash scripts/ci/install_flyctl.sh
if [ -x "$HOME/.fly/bin/flyctl" ]; then
  flyctl_bin="$HOME/.fly/bin/flyctl"
else
  flyctl_bin="$(command -v flyctl)"
fi

status_json="$("$flyctl_bin" status --app "$app" --json)"
current_image="$(
  STATUS_JSON="$status_json" python - <<'PY'
import json
import os

data = json.loads(os.environ["STATUS_JSON"])
machines = data.get("Machines") or data.get("machines") or []
images = set()
for machine in machines:
    config = machine.get("config") or machine.get("Config") or {}
    image = config.get("image") or config.get("Image")
    if image:
        images.add(image)
if len(images) == 1:
    print(next(iter(images)))
elif not images:
    print("")
else:
    print("MULTIPLE:" + ",".join(sorted(images)))
PY
)"

if [ -z "$current_image" ]; then
  echo "ERROR: deployed image could not be read from Fly status." >&2
  exit 1
fi
if [[ "$current_image" == MULTIPLE:* ]]; then
  echo "ERROR: deployment is not converged on one image." >&2
  exit 1
fi

"$flyctl_bin" auth docker >/dev/null
expected_digest="${expected_image##*@}"
if [[ "$current_image" == *@sha256:* ]]; then
  current_digest="${current_image##*@}"
else
  manifest_json="$(docker manifest inspect --verbose "$current_image")"
  current_digest="$(
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
fi
[ -n "$current_digest" ] || {
  echo "ERROR: could not resolve deployed image digest." >&2
  exit 1
}
[ "$current_digest" = "$expected_digest" ] || {
  echo "ERROR: deployed image digest does not match pipeline evidence." >&2
  exit 1
}

mkdir -p deploy-evidence
verify_file="deploy-evidence/${environment}-post-verify.txt"
: > "$verify_file"

success=0
attempts=20
for attempt in $(seq 1 "$attempts"); do
  code="$(curl --silent --show-error --output /tmp/health-${attempt}.json \
    --write-out '%{http_code}' --max-time 20 "$health_url" || true)"
  if [ "$code" = "200" ]; then
    success=$((success + 1))
  fi
  printf 'health_attempt_%s=%s\n' "$attempt" "$code" >> "$verify_file"
done

failures=$((attempts - success))
error_rate=$((failures * 100 / attempts))
printf 'health_success=%s/%s\nsynthetic_error_rate_percent=%s\n' \
  "$success" "$attempts" "$error_rate" >> "$verify_file"
if [ "$failures" -ne 0 ]; then
  echo "ERROR: synthetic health error-rate guardrail exceeded 0%." >&2
  exit 1
fi

policy_url="${health_url%/health}/policy"
policy_code="$(curl --silent --show-error --output /tmp/policy-unauthorized.json \
  --write-out '%{http_code}' --max-time 20 "$policy_url" || true)"
printf 'unauthenticated_policy_status=%s\n' "$policy_code" >> "$verify_file"
case "$policy_code" in
  401|403|503) ;;
  *)
    echo "ERROR: protected policy endpoint did not fail closed." >&2
    exit 1
    ;;
esac

if [ "$environment" = "production" ]; then
  homepage_code="$(curl --silent --show-error --location --output /tmp/home.html \
    --write-out '%{http_code}' --max-time 30 https://www.clearglassinc.com/ || true)"
  printf 'critical_homepage_status=%s\n' "$homepage_code" >> "$verify_file"
  [ "$homepage_code" = "200" ] || {
    echo "ERROR: production critical user-flow guardrail failed." >&2
    exit 1
  }
  grep -qi "ClearGlass" /tmp/home.html || {
    echo "ERROR: production homepage content verification failed." >&2
    exit 1
  }
fi

printf 'expected_image=%s\nverified_digest=%s\nstatus=PASS\n' \
  "$expected_image" "$current_digest" >> "$verify_file"

echo "${environment} post-deploy verification: PASS"

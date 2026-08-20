#!/usr/bin/env bash
set -euo pipefail

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 2
}

require_bool() {
  local name="$1"
  local value="$2"
  case "$value" in
    true|false) ;;
    *) fail "${name} must be true or false; received '${value}'" ;;
  esac
}

for pair in \
  "RUN_VALIDATION:${RUN_VALIDATION:-}" \
  "RUN_GITHUB_AUTOMATION_CHECKS:${RUN_GITHUB_AUTOMATION_CHECKS:-}" \
  "RUN_AGENT_HEALTH_CHECKS:${RUN_AGENT_HEALTH_CHECKS:-}" \
  "DEPLOY_STAGING:${DEPLOY_STAGING:-}" \
  "DEPLOY_PRODUCTION:${DEPLOY_PRODUCTION:-}" \
  "ENABLE_AGENTS:${ENABLE_AGENTS:-}" \
  "DEPLOY_ANIMATIONS:${DEPLOY_ANIMATIONS:-}" \
  "EMERGENCY_STOP:${EMERGENCY_STOP:-}"
do
  name="${pair%%:*}"
  value="${pair#*:}"
  require_bool "$name" "$value"
done

case "${TARGET_ENVIRONMENT:-}" in
  none|staging|production) ;;
  *) fail "TARGET_ENVIRONMENT must be one of none, staging, production" ;;
esac

printf '%s\n' \
  "security_preflight parameters:" \
  "  run_validation=${RUN_VALIDATION}" \
  "  run_github_automation_checks=${RUN_GITHUB_AUTOMATION_CHECKS}" \
  "  run_agent_health_checks=${RUN_AGENT_HEALTH_CHECKS}" \
  "  deploy_staging=${DEPLOY_STAGING}" \
  "  deploy_production=${DEPLOY_PRODUCTION}" \
  "  enable_agents=${ENABLE_AGENTS}" \
  "  deploy_animations=${DEPLOY_ANIMATIONS}" \
  "  emergency_stop=${EMERGENCY_STOP}" \
  "  target_environment=${TARGET_ENVIRONMENT}" \
  "  branch=${CIRCLE_BRANCH:-<tag>}" \
  "  tag=${CIRCLE_TAG:-<none>}"

mutation_requested=false
if [ "$DEPLOY_STAGING" = "true" ] || \
   [ "$DEPLOY_PRODUCTION" = "true" ] || \
   [ "$ENABLE_AGENTS" = "true" ] || \
   [ "$DEPLOY_ANIMATIONS" = "true" ]; then
  mutation_requested=true
fi

if [ "$EMERGENCY_STOP" = "true" ] && [ "$mutation_requested" = "true" ]; then
  fail "emergency_stop=true forbids deployments, agent activation, animation publication, and other mutations"
fi

if [ "$DEPLOY_STAGING" = "true" ] && [ "$DEPLOY_PRODUCTION" = "true" ]; then
  fail "deploy_staging and deploy_production are mutually exclusive"
fi

if [ "$DEPLOY_STAGING" = "true" ]; then
  [ "$RUN_VALIDATION" = "true" ] || fail "staging deployment requires run_validation=true"
  [ "$TARGET_ENVIRONMENT" = "staging" ] || \
    fail "deploy_staging=true requires target_environment=staging"
  [ -z "${CIRCLE_TAG:-}" ] || fail "staging deployment must run from a branch, not a tag"
fi

if [ "$DEPLOY_PRODUCTION" = "true" ]; then
  [ "$RUN_VALIDATION" = "true" ] || fail "production deployment requires run_validation=true"
  [ "$TARGET_ENVIRONMENT" = "production" ] || \
    fail "deploy_production=true requires target_environment=production"

  if [ "${CIRCLE_BRANCH:-}" = "main" ] && [ -z "${CIRCLE_TAG:-}" ]; then
    echo "Production ref eligibility: protected main branch."
  elif [ -n "${CIRCLE_TAG:-}" ]; then
    case "$CIRCLE_TAG" in
      v[0-9]*) ;;
      *) fail "production release tags must start with v followed by a numeric version" ;;
    esac

    [ -n "${TRUSTED_RELEASE_SIGNER_FINGERPRINT:-}" ] || \
      fail "signed-tag production requires TRUSTED_RELEASE_SIGNER_FINGERPRINT in ci-readonly"
    [ -n "${TRUSTED_RELEASE_SIGNER_PUBLIC_KEY_B64:-}" ] || \
      fail "signed-tag production requires TRUSTED_RELEASE_SIGNER_PUBLIC_KEY_B64 in ci-readonly"

    command -v gpg >/dev/null 2>&1 || fail "gpg is required to verify signed production tags"
    git fetch --quiet --force origin \
      "refs/tags/${CIRCLE_TAG}:refs/tags/${CIRCLE_TAG}" || \
      fail "unable to fetch production tag ${CIRCLE_TAG}"

    gpg_home="$(mktemp -d)"
    verify_log="$(mktemp)"
    trap 'rm -rf "$gpg_home" "$verify_log"' EXIT

    printf '%s' "$TRUSTED_RELEASE_SIGNER_PUBLIC_KEY_B64" |
      base64 --decode |
      GNUPGHOME="$gpg_home" gpg --batch --quiet --import

    if ! GNUPGHOME="$gpg_home" git verify-tag --raw "$CIRCLE_TAG" 2>"$verify_log"; then
      fail "production tag signature verification failed"
    fi

    signer="$(
      awk '/^\[GNUPG:\] VALIDSIG / {print $3; exit}' "$verify_log" |
        tr '[:lower:]' '[:upper:]'
    )"
    expected="$(printf '%s' "$TRUSTED_RELEASE_SIGNER_FINGERPRINT" | tr -d ' ' | tr '[:lower:]' '[:upper:]')"
    [ -n "$signer" ] || fail "verified tag did not yield a signer fingerprint"
    [ "$signer" = "$expected" ] || fail "production tag was signed by an untrusted key"
    echo "Production ref eligibility: trusted signed release tag."
  else
    fail "production deployment is allowed only from protected main or a trusted signed release tag"
  fi
fi

if [ "$DEPLOY_STAGING" = "false" ] && [ "$DEPLOY_PRODUCTION" = "false" ]; then
  [ "$TARGET_ENVIRONMENT" = "none" ] || \
    fail "target_environment must be none when no deployment is requested"
  [ "$ENABLE_AGENTS" = "false" ] || \
    fail "enable_agents=true requires an approved staging or production deployment"
  [ "$DEPLOY_ANIMATIONS" = "false" ] || \
    fail "deploy_animations=true requires an approved staging or production deployment"
fi

if [ "$ENABLE_AGENTS" = "true" ]; then
  fail "enable_agents=true is blocked until REPLACE_ME_AGENT_ACTIVATION_ADAPTER and an enforceable rate-limit policy are configured"
fi

if [ "$DEPLOY_ANIMATIONS" = "true" ]; then
  fail "deploy_animations=true is blocked until REPLACE_ME_ANIMATION_DEPLOY_ADAPTER is configured for an approved non-GitHub-write deployment target"
fi

echo "security_preflight: PASS"

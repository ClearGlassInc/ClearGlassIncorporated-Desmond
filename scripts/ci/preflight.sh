#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
fail(){ echo "PREFLIGHT FAILED: $1" >&2; exit 1; }
[[ "${RUN_VALIDATION}" == true || "${RUN_VALIDATION}" == false ]] || fail "run_validation must be boolean"
[[ "${TARGET_ENVIRONMENT}" =~ ^(none|staging|production)$ ]] || fail "target_environment invalid"
[[ "${EMERGENCY_STOP}" == true || "${EMERGENCY_STOP}" == false ]] || fail "emergency_stop must be boolean"
for v in RUN_GITHUB_AUTOMATION_CHECKS RUN_AGENT_HEALTH_CHECKS DEPLOY_STAGING DEPLOY_PRODUCTION ENABLE_AGENTS DEPLOY_ANIMATIONS; do x=${!v}; [[ "$x" == true || "$x" == false ]] || fail "$v must be boolean"; done
if [[ "$EMERGENCY_STOP" == true ]] && [[ "$DEPLOY_STAGING" == true || "$DEPLOY_PRODUCTION" == true || "$ENABLE_AGENTS" == true || "$DEPLOY_ANIMATIONS" == true ]]; then fail "emergency_stop blocks all mutation/activation/publication"; fi
[[ "$DEPLOY_STAGING" != true || "$DEPLOY_PRODUCTION" != true ]] || fail "staging and production cannot be requested together"
[[ "$DEPLOY_STAGING" != true || "$TARGET_ENVIRONMENT" == staging ]] || fail "staging requires target_environment=staging"
[[ "$DEPLOY_PRODUCTION" != true || "$TARGET_ENVIRONMENT" == production ]] || fail "production requires target_environment=production"
if [[ "$DEPLOY_STAGING" == true || "$DEPLOY_PRODUCTION" == true ]]; then [[ "$RUN_VALIDATION" == true ]] || fail "deployment requires run_validation=true"; fi
if [[ "$ENABLE_AGENTS" == true ]]; then fail "enable_agents is fail-closed until a separately reviewed activation adapter exists"; fi
if [[ "$DEPLOY_ANIMATIONS" == true ]]; then fail "deploy_animations is fail-closed until a separately reviewed publication adapter exists"; fi
if [[ "$DEPLOY_PRODUCTION" == true ]]; then
  if [[ "${CIRCLE_BRANCH:-}" == main ]]; then :
  elif [[ -n "${CIRCLE_TAG:-}" && "${CIRCLE_TAG}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    [[ -n "${TRUSTED_RELEASE_SIGNER_FINGERPRINT:-}" ]] || fail "trusted release signer fingerprint missing"
    command -v gpg >/dev/null || fail "gpg unavailable for signed tag verification"
    git fetch --tags --force >/dev/null 2>&1
    git tag -v "$CIRCLE_TAG" 2>&1 | tee artifacts/evidence/tag-verification.txt >/dev/null || fail "release tag signature verification failed"
    grep -qi "$TRUSTED_RELEASE_SIGNER_FINGERPRINT" artifacts/evidence/tag-verification.txt || fail "release signer fingerprint mismatch"
  else fail "production is allowed only from main or a trusted signed vX.Y.Z tag"; fi
fi
printf '%s\n' "run_validation=$RUN_VALIDATION" "run_github_automation_checks=$RUN_GITHUB_AUTOMATION_CHECKS" "run_agent_health_checks=$RUN_AGENT_HEALTH_CHECKS" "deploy_staging=$DEPLOY_STAGING" "deploy_production=$DEPLOY_PRODUCTION" "enable_agents=$ENABLE_AGENTS" "deploy_animations=$DEPLOY_ANIMATIONS" "emergency_stop=$EMERGENCY_STOP" "target_environment=$TARGET_ENVIRONMENT" > artifacts/evidence/parameters.txt
chmod 600 artifacts/evidence/parameters.txt
printf '%s\n' "preflight=PASS" "sha=$CIRCLE_SHA1" > artifacts/evidence/preflight.txt

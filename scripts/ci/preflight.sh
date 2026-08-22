#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
fail(){ echo "PREFLIGHT FAILED: $1" >&2; exit 1; }
for v in RUN_VALIDATION RUN_GITHUB_AUTOMATION_CHECKS RUN_AGENT_HEALTH_CHECKS DEPLOY_STAGING DEPLOY_PRODUCTION ROLLBACK_STAGING ROLLBACK_PRODUCTION EMERGENCY_STOP; do x=${!v:-}; [[ "$x" == true || "$x" == false ]] || fail "$v must be boolean"; done
[[ "${TARGET_ENVIRONMENT:-}" =~ ^(none|staging|production)$ ]] || fail "target_environment invalid"
[[ "${CHANGE_REFERENCE:-}" =~ ^(|CHG-[0-9]{4,}|RFC-[0-9]{4,}|INC-[0-9]{4,}|SEC-[0-9]{4,})$ ]] || fail "change_reference format invalid"
[[ "$DEPLOY_STAGING" != true || "$DEPLOY_PRODUCTION" != true ]] || fail "staging and production deployment cannot be combined"
[[ "$ROLLBACK_STAGING" != true || "$ROLLBACK_PRODUCTION" != true ]] || fail "staging and production rollback cannot be combined"
[[ "$EMERGENCY_STOP" != true || ( "$DEPLOY_STAGING" != true && "$DEPLOY_PRODUCTION" != true && "$ROLLBACK_STAGING" != true && "$ROLLBACK_PRODUCTION" != true ) ]] || fail "emergency_stop blocks mutation"
[[ "$DEPLOY_STAGING" != true || "$TARGET_ENVIRONMENT" == staging ]] || fail "staging target required"
[[ "$DEPLOY_PRODUCTION" != true || "$TARGET_ENVIRONMENT" == production ]] || fail "production target required"
[[ "$ROLLBACK_STAGING" != true || "$TARGET_ENVIRONMENT" == staging ]] || fail "staging rollback target required"
[[ "$ROLLBACK_PRODUCTION" != true || "$TARGET_ENVIRONMENT" == production ]] || fail "production rollback target required"
[[ "$DEPLOY_STAGING" != true || "$RUN_VALIDATION" == true ]] || fail "staging requires validation"
[[ "$DEPLOY_PRODUCTION" != true || "$RUN_VALIDATION" == true ]] || fail "production requires validation"
[[ "$DEPLOY_PRODUCTION" != true || -n "$CHANGE_REFERENCE" ]] || fail "production requires change_reference"
[[ "$ROLLBACK_PRODUCTION" != true || -n "$CHANGE_REFERENCE" ]] || fail "production rollback requires change_reference"
if [[ "$DEPLOY_PRODUCTION" == true ]]; then
  if [[ "${CIRCLE_BRANCH:-}" == main ]]; then :; elif [[ "${CIRCLE_TAG:-}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then command -v gpg >/dev/null || fail "gpg unavailable"; git fetch --tags --force >/dev/null 2>&1; git tag -v "$CIRCLE_TAG" > artifacts/evidence/tag-verification.txt 2>&1 || fail "signed tag verification failed"; else fail "production ref not authorized"; fi
fi
printf '%s\n' "status=PASS" "sha=${CIRCLE_SHA1:-unknown}" "target=${TARGET_ENVIRONMENT}" "change_reference=${CHANGE_REFERENCE}" > artifacts/evidence/preflight.txt

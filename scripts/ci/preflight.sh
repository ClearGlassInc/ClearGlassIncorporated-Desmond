#!/usr/bin/env bash
set -euo pipefail
fail(){ printf 'NOT VERIFIED: %s\n' "$*" >&2; exit 2; }
bool(){ case "$2" in true|false) ;; *) fail "$1 must be boolean";; esac; }
for p in RUN_VALIDATION RUN_GITHUB_AUTOMATION_CHECKS RUN_AGENT_HEALTH_CHECKS DEPLOY_ANIMATIONS ENABLE_AGENTS DEPLOY_STAGING DEPLOY_PRODUCTION ROLLBACK_STAGING ROLLBACK_PRODUCTION EMERGENCY_STOP ALLOW_NONCRITICAL_SCAN_FINDINGS DRY_RUN; do bool "$p" "${!p:-}"; done
case "${TARGET_ENVIRONMENT:-}" in none|staging|production) ;; *) fail "invalid target environment";; esac
[ -n "${CIRCLE_SHA1:-}" ] || fail "CIRCLE_SHA1 missing"
actual="$(git rev-parse HEAD 2>/dev/null || true)"; [ "$actual" = "$CIRCLE_SHA1" ] || fail "HEAD does not equal CIRCLE_SHA1"
mutation=false
for p in DEPLOY_STAGING DEPLOY_PRODUCTION ROLLBACK_STAGING ROLLBACK_PRODUCTION ENABLE_AGENTS; do [ "${!p}" = true ] && mutation=true; done
[ "$EMERGENCY_STOP" = true ] && [ "$mutation" = true ] && fail "emergency_stop=true blocks all mutation"
[ "$DEPLOY_STAGING" = true ] && { [ "$TARGET_ENVIRONMENT" = staging ] || fail "staging target required"; [ "$DRY_RUN" = false ] || fail "staging requires dry_run=false"; [ "$DEPLOY_PRODUCTION" = false ] || fail "staging/production deploy mutually exclusive"; [ "$ROLLBACK_STAGING" = false ] || fail "deploy/rollback mutually exclusive"; [ "$ROLLBACK_PRODUCTION" = false ] || fail "deploy/rollback mutually exclusive"; }
[ "$DEPLOY_PRODUCTION" = true ] && { [ "$TARGET_ENVIRONMENT" = production ] || fail "production target required"; [ "$DRY_RUN" = false ] || fail "production requires dry_run=false"; [ "$DEPLOY_STAGING" = false ] || fail "staging/production deploy mutually exclusive"; [ "$ROLLBACK_STAGING" = false ] || fail "deploy/rollback mutually exclusive"; [ "$ROLLBACK_PRODUCTION" = false ] || fail "deploy/rollback mutually exclusive"; [ -n "${CHANGE_REFERENCE:-}" ] || fail "production requires change_reference"; }
[ "$ROLLBACK_STAGING" = true ] && { [ "$TARGET_ENVIRONMENT" = staging ] || fail "staging rollback requires staging target"; [ "$DRY_RUN" = false ] || fail "rollback requires dry_run=false"; [ "$ROLLBACK_PRODUCTION" = false ] || fail "rollback targets mutually exclusive"; }
[ "$ROLLBACK_PRODUCTION" = true ] && { [ "$TARGET_ENVIRONMENT" = production ] || fail "production rollback requires production target"; [ "$DRY_RUN" = false ] || fail "rollback requires dry_run=false"; [ "$ROLLBACK_STAGING" = false ] || fail "rollback targets mutually exclusive"; [ -n "${CHANGE_REFERENCE:-}" ] || fail "production rollback requires change_reference"; }
if [ -n "${RELEASE_REF:-}" ]; then case "$RELEASE_REF" in main|v[0-9]*) ;; *) fail "release_ref must be main or v<version>";; esac; fi
if [ -n "${EXPECTED_ARTIFACT_SHA256:-}" ]; then printf '%s' "$EXPECTED_ARTIFACT_SHA256" | grep -Eq '^[A-Fa-f0-9]{64}$' || fail "expected_artifact_sha256 must be SHA-256"; fi
if [ "${ALLOW_NONCRITICAL_SCAN_FINDINGS}" = true ]; then [ -f policy/security-allowlist.json ] || fail "allowlist policy missing"; fi
if [ "$DEPLOY_PRODUCTION" = true ] || [ "$ROLLBACK_PRODUCTION" = true ]; then [ "${RELEASE_REF:-}" = main ] || [ -n "${CIRCLE_TAG:-}" ] || fail "production requires main or signed release tag"; fi
if [ "$ENABLE_AGENTS" = true ]; then fail "enable_agents is disabled until a sandbox/canary activation adapter is configured"; fi
if [ "$DEPLOY_ANIMATIONS" = true ] && [ "$TARGET_ENVIRONMENT" = none ]; then fail "deploy_animations requires a target environment"; fi
mkdir -p artifacts/evidence
python3 - <<'PY'
import json,os
safe=['CIRCLE_PIPELINE_ID','CIRCLE_WORKFLOW_ID','CIRCLE_SHA1','CIRCLE_BRANCH','CIRCLE_TAG']
params=['RUN_VALIDATION','RUN_GITHUB_AUTOMATION_CHECKS','RUN_AGENT_HEALTH_CHECKS','DEPLOY_ANIMATIONS','ENABLE_AGENTS','DEPLOY_STAGING','DEPLOY_PRODUCTION','ROLLBACK_STAGING','ROLLBACK_PRODUCTION','EMERGENCY_STOP','ALLOW_NONCRITICAL_SCAN_FINDINGS','TARGET_ENVIRONMENT','RELEASE_REF','EXPECTED_ARTIFACT_SHA256','CHANGE_REFERENCE','DRY_RUN']
json.dump({'status':'PASS','pipeline':{k:os.getenv(k,'') for k in safe},'parameters':{k:os.getenv(k,'') for k in params}},open('artifacts/evidence/preflight.json','w'),indent=2)
PY
printf '%s\n' 'security_preflight: PASS'
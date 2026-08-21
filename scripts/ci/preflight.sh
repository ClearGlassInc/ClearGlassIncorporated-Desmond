#!/usr/bin/env bash
set -euo pipefail
fail(){ printf 'NOT VERIFIED: %s\n' "$*" >&2; exit 2; }
bool(){ case "$2" in true|false) ;; *) fail "$1 must be boolean";; esac; }
for p in RUN_VALIDATION RUN_GITHUB_AUTOMATION_CHECKS RUN_AGENT_HEALTH_CHECKS DEPLOY_ANIMATIONS ENABLE_AGENTS DEPLOY_STAGING DEPLOY_PRODUCTION ROLLBACK_STAGING ROLLBACK_PRODUCTION EMERGENCY_STOP ALLOW_NONCRITICAL_SCAN_FINDINGS DRY_RUN; do bool "$p" "${!p:-}"; done
case "${TARGET_ENVIRONMENT:-}" in none|staging|production) ;; *) fail "invalid target environment";; esac
[ -n "${CIRCLE_SHA1:-}" ] || fail "CIRCLE_SHA1 missing"
actual="$(git rev-parse HEAD 2>/dev/null || true)"; [ "$actual" = "$CIRCLE_SHA1" ] || fail "HEAD does not equal CIRCLE_SHA1"

if [ -n "${RELEASE_REF:-}" ]; then
  case "$RELEASE_REF" in main|v[0-9]*) ;; *) fail "release_ref must be main or v<version>";; esac
  if [ -n "${CIRCLE_BRANCH:-}" ]; then [ "$RELEASE_REF" = "$CIRCLE_BRANCH" ] || fail "release_ref does not match CircleCI branch"; fi
  if [ -n "${CIRCLE_TAG:-}" ]; then [ "$RELEASE_REF" = "$CIRCLE_TAG" ] || fail "release_ref does not match CircleCI tag"; fi
fi
if [ -n "${EXPECTED_ARTIFACT_SHA256:-}" ]; then printf '%s' "$EXPECTED_ARTIFACT_SHA256" | grep -Eq '^[A-Fa-f0-9]{64}$' || fail "expected_artifact_sha256 must be SHA-256"; fi
if [ -n "${CHANGE_REFERENCE:-}" ]; then
  [ -f policy/release-policy.json ] || fail "release policy missing"
  python3 - "$CHANGE_REFERENCE" <<'PY'
import json,re,sys
p=json.load(open('policy/release-policy.json'))
if not re.fullmatch(p['change_reference_regex'],sys.argv[1]): raise SystemExit('invalid change_reference format')
PY
fi

mutation=false
for p in DEPLOY_STAGING DEPLOY_PRODUCTION ROLLBACK_STAGING ROLLBACK_PRODUCTION ENABLE_AGENTS; do [ "${!p}" = true ] && mutation=true; done
[ "$EMERGENCY_STOP" = true ] && [ "$mutation" = true ] && fail "emergency_stop=true blocks all mutation"
[ "$DEPLOY_STAGING" = true ] && { [ "$RUN_VALIDATION" = true ] || fail "staging requires run_validation=true"; [ "$TARGET_ENVIRONMENT" = staging ] || fail "staging target required"; [ "$DRY_RUN" = false ] || fail "staging requires dry_run=false"; [ "$DEPLOY_PRODUCTION" = false ] || fail "staging/production deploy mutually exclusive"; [ "$ROLLBACK_STAGING" = false ] || fail "deploy/rollback mutually exclusive"; [ "$ROLLBACK_PRODUCTION" = false ] || fail "deploy/rollback mutually exclusive"; }
[ "$DEPLOY_PRODUCTION" = true ] && { [ "$RUN_VALIDATION" = true ] || fail "production requires run_validation=true"; [ "$TARGET_ENVIRONMENT" = production ] || fail "production target required"; [ "$DRY_RUN" = false ] || fail "production requires dry_run=false"; [ "$DEPLOY_STAGING" = false ] || fail "staging/production deploy mutually exclusive"; [ "$ROLLBACK_STAGING" = false ] || fail "deploy/rollback mutually exclusive"; [ "$ROLLBACK_PRODUCTION" = false ] || fail "deploy/rollback mutually exclusive"; [ -n "${CHANGE_REFERENCE:-}" ] || fail "production requires change_reference"; }
[ "$ROLLBACK_STAGING" = true ] && { [ "$TARGET_ENVIRONMENT" = staging ] || fail "staging rollback requires staging target"; [ "$DRY_RUN" = false ] || fail "rollback requires dry_run=false"; [ "$ROLLBACK_PRODUCTION" = false ] || fail "rollback targets mutually exclusive"; }
[ "$ROLLBACK_PRODUCTION" = true ] && { [ "$TARGET_ENVIRONMENT" = production ] || fail "production rollback requires production target"; [ "$DRY_RUN" = false ] || fail "rollback requires dry_run=false"; [ "$ROLLBACK_STAGING" = false ] || fail "rollback targets mutually exclusive"; [ -n "${CHANGE_REFERENCE:-}" ] || fail "production rollback requires change_reference"; }

if [ "$DEPLOY_PRODUCTION" = true ] || [ "$ROLLBACK_PRODUCTION" = true ]; then
  if [ "${CIRCLE_BRANCH:-}" = main ] && [ -z "${CIRCLE_TAG:-}" ]; then
    [ "${RELEASE_REF:-main}" = main ] || fail "production release_ref must be main"
  elif [ -n "${CIRCLE_TAG:-}" ]; then
    [ "${RELEASE_REF:-$CIRCLE_TAG}" = "$CIRCLE_TAG" ] || fail "release_ref must equal production tag"
    [[ "$CIRCLE_TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+([+-][0-9A-Za-z.-]+)?$ ]] || fail "production tag must be semver-like vX.Y.Z"
    [ -n "${TRUSTED_RELEASE_SIGNER_FINGERPRINT:-}" ] || fail "trusted release signer fingerprint missing"
    [ -n "${TRUSTED_RELEASE_SIGNER_PUBLIC_KEY_B64:-}" ] || fail "trusted release signer public key missing"
    command -v gpg >/dev/null 2>&1 || fail "gpg unavailable for signed-tag verification"
    git fetch --quiet --force origin "refs/tags/${CIRCLE_TAG}:refs/tags/${CIRCLE_TAG}" || fail "cannot fetch production tag"
    gh="$(mktemp -d)"; log="$(mktemp)"; trap 'rm -rf "$gh" "$log"' EXIT
    printf '%s' "$TRUSTED_RELEASE_SIGNER_PUBLIC_KEY_B64" | base64 --decode | GNUPGHOME="$gh" gpg --batch --quiet --import
    GNUPGHOME="$gh" git verify-tag --raw "$CIRCLE_TAG" 2>"$log" || fail "production tag signature verification failed"
    signer="$(awk '/^\[GNUPG:\] VALIDSIG / {print $3; exit}' "$log" | tr -d ' ' | tr '[:lower:]' '[:upper:]')"
    expected="$(printf '%s' "$TRUSTED_RELEASE_SIGNER_FINGERPRINT" | tr -d ' ' | tr '[:lower:]' '[:upper:]')"
    [ "$signer" = "$expected" ] || fail "production tag signer is not trusted"
    [ "$(git rev-list -1 "$CIRCLE_TAG")" = "$CIRCLE_SHA1" ] || fail "signed tag does not resolve to CIRCLE_SHA1"
  else
    fail "production requires protected main or trusted signed release tag"
  fi
fi

[ "$ENABLE_AGENTS" = true ] && fail "enable_agents is blocked until a reviewed sandbox/canary activation adapter exists"
[ "$DEPLOY_ANIMATIONS" = true ] && [ "$TARGET_ENVIRONMENT" = none ] && fail "deploy_animations requires a target environment"
if [ "$ALLOW_NONCRITICAL_SCAN_FINDINGS" = true ]; then [ -f policy/security-allowlist.json ] || fail "security allowlist missing"; fi

mkdir -p artifacts/evidence
python3 - <<'PY'
import json,os
safe=['CIRCLE_PIPELINE_ID','CIRCLE_WORKFLOW_ID','CIRCLE_SHA1','CIRCLE_BRANCH','CIRCLE_TAG']
params=['RUN_VALIDATION','RUN_GITHUB_AUTOMATION_CHECKS','RUN_AGENT_HEALTH_CHECKS','DEPLOY_ANIMATIONS','ENABLE_AGENTS','DEPLOY_STAGING','DEPLOY_PRODUCTION','ROLLBACK_STAGING','ROLLBACK_PRODUCTION','EMERGENCY_STOP','ALLOW_NONCRITICAL_SCAN_FINDINGS','TARGET_ENVIRONMENT','RELEASE_REF','EXPECTED_ARTIFACT_SHA256','CHANGE_REFERENCE','DRY_RUN']
json.dump({'status':'PASS','pipeline':{k:os.getenv(k,'') for k in safe},'parameters':{k:os.getenv(k,'') for k in params}},open('artifacts/evidence/preflight.json','w'),indent=2)
PY
printf '%s\n' 'security_preflight: PASS'
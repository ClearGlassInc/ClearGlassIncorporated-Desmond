#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
[ "${EMERGENCY_STOP:-true}" = false ] || { echo 'NOT VERIFIED: emergency stop active' >&2; exit 2; }
[ "${TARGET_ENVIRONMENT:-}" = staging ] || { echo 'NOT VERIFIED: staging rollback target required' >&2; exit 2; }
ROLLBACK_COMMAND='REPLACE_ME_DEPLOY_COMMAND'
[ "$ROLLBACK_COMMAND" != REPLACE_ME_DEPLOY_COMMAND ] || { echo 'NOT VERIFIED: rollback adapter not configured' >&2; exit 2; }
# The adapter must resolve the last VERIFIED immutable staging release; it must not accept a mutable branch/tag.
LAST_VERIFIED_ARTIFACT='REPLACE_ME_LAST_VERIFIED_STAGING_ARTIFACT'
[ "$LAST_VERIFIED_ARTIFACT" != REPLACE_ME_LAST_VERIFIED_STAGING_ARTIFACT ] || { echo 'NOT VERIFIED: prior verified release lookup is not configured' >&2; exit 2; }
# shellcheck disable=SC2086
$ROLLBACK_COMMAND "$LAST_VERIFIED_ARTIFACT"
printf '%s\n' '{"status":"PASS","environment":"staging","rollback":"verified-artifact-only"}' > artifacts/evidence/staging-rollback.json
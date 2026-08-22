#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
[ "${EMERGENCY_STOP:-true}" = false ] || { echo 'NOT VERIFIED: emergency stop active' >&2; exit 2; }
[ "${TARGET_ENVIRONMENT:-}" = staging ] || { echo 'NOT VERIFIED: staging rollback target required' >&2; exit 2; }
artifact="${LAST_VERIFIED_STAGING_ARTIFACT:-}"
[ -n "$artifact" ] && [ -f "$artifact" ] || { echo 'NOT VERIFIED: last verified staging artifact unavailable' >&2; exit 2; }
expected="$(sha256sum "$artifact" | awk '{print $1}')"
printf '%s\n' "rollback_artifact=$artifact" "artifact_sha256=$expected" > artifacts/evidence/staging-rollback.txt
: "${REPLACE_ME_ROLLBACK_COMMAND:?REPLACE_ME_ROLLBACK_COMMAND must be supplied by restricted staging context}"
[[ "$REPLACE_ME_ROLLBACK_COMMAND" != 'REPLACE_ME_ROLLBACK_COMMAND' ]] || { echo 'NOT VERIFIED: rollback command is unconfigured' >&2; exit 78; }
bash -c "$REPLACE_ME_ROLLBACK_COMMAND"

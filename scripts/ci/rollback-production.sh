#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
[ "${EMERGENCY_STOP:-true}" = false ] || { echo 'NOT VERIFIED: emergency stop active' >&2; exit 2; }
[ "${TARGET_ENVIRONMENT:-}" = production ] || { echo 'NOT VERIFIED: production rollback target required' >&2; exit 2; }
[ -n "${CHANGE_REFERENCE:-}" ] || { echo 'NOT VERIFIED: change reference required' >&2; exit 2; }
artifact="${LAST_VERIFIED_PRODUCTION_ARTIFACT:-}"
[ -n "$artifact" ] && [ -f "$artifact" ] || { echo 'NOT VERIFIED: last verified production artifact unavailable' >&2; exit 2; }
expected="$(sha256sum "$artifact" | awk '{print $1}')"
printf '%s\n' "rollback_artifact=$artifact" "artifact_sha256=$expected" "change_reference=$CHANGE_REFERENCE" > artifacts/evidence/production-rollback.txt
: "${REPLACE_ME_ROLLBACK_COMMAND:?REPLACE_ME_ROLLBACK_COMMAND must be supplied by restricted production context}"
[[ "$REPLACE_ME_ROLLBACK_COMMAND" != 'REPLACE_ME_ROLLBACK_COMMAND' ]] || { echo 'NOT VERIFIED: rollback command is unconfigured' >&2; exit 78; }
bash -c "$REPLACE_ME_ROLLBACK_COMMAND"

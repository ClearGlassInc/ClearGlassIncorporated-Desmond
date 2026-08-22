#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
[ "${EMERGENCY_STOP:-true}" = false ] || { echo 'NOT VERIFIED: emergency stop active' >&2; exit 2; }
[ "${TARGET_ENVIRONMENT:-}" = staging ] || { echo 'NOT VERIFIED: staging target required' >&2; exit 2; }
artifact="${RELEASE_ARTIFACT:-release-bundle.tar.gz}"
test -f "$artifact"
expected="$(awk '{print $1}' artifacts/release/artifact.sha256)"
actual="$(sha256sum "$artifact" | awk '{print $1}')"
[[ "$actual" == "$expected" ]] || { echo 'NOT VERIFIED: artifact digest mismatch' >&2; exit 2; }
printf '%s\n' "version_before=${CURRENT_STAGING_VERSION:-UNKNOWN}" > artifacts/evidence/staging-current-version.txt
: "${REPLACE_ME_DEPLOY_COMMAND:?REPLACE_ME_DEPLOY_COMMAND must be supplied by restricted staging context}"
[[ "$REPLACE_ME_DEPLOY_COMMAND" != 'REPLACE_ME_DEPLOY_COMMAND' ]] || { echo 'NOT VERIFIED: deploy command is unconfigured' >&2; exit 78; }
bash -c "$REPLACE_ME_DEPLOY_COMMAND"
printf '%s\n' "status=PASS" "artifact_sha256=$actual" "target=staging" > artifacts/evidence/staging-deploy.txt

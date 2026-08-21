#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
[ "${EMERGENCY_STOP:-true}" = false ] || { echo 'NOT VERIFIED: emergency stop active' >&2; exit 2; }
[ "${DRY_RUN:-true}" = false ] || { echo 'NOT VERIFIED: dry_run=true' >&2; exit 2; }
[ "${TARGET_ENVIRONMENT:-}" = staging ] || { echo 'NOT VERIFIED: staging target required' >&2; exit 2; }
[ -f release-bundle.tar.gz ] || { echo 'NOT VERIFIED: immutable artifact missing' >&2; exit 2; }
# Deployment provider is intentionally not fabricated. Configure these in the restricted staging-deploy context.
DEPLOY_COMMAND='REPLACE_ME_DEPLOY_COMMAND'
STAGING_URL='REPLACE_ME_STAGING_URL'
[ "$DEPLOY_COMMAND" != REPLACE_ME_DEPLOY_COMMAND ] || { echo 'NOT VERIFIED: REPLACE_ME_DEPLOY_COMMAND' >&2; exit 2; }
[ "$STAGING_URL" != REPLACE_ME_STAGING_URL ] || { echo 'NOT VERIFIED: REPLACE_ME_STAGING_URL' >&2; exit 2; }
# shellcheck disable=SC2086
$DEPLOY_COMMAND release-bundle.tar.gz
printf '%s\n' '{"status":"PASS","environment":"staging","artifact":"release-bundle.tar.gz"}' > artifacts/evidence/staging-deploy.json
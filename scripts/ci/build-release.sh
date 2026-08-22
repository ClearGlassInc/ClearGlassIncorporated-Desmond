#!/usr/bin/env bash
set -euo pipefail
rm -rf release-staging release-bundle.tar.gz
mkdir -p release-staging artifacts/evidence
printf '%s\n' "$CIRCLE_SHA1" > release-staging/REVISION
printf '%s\n' "built_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)" > release-staging/METADATA
cp package.json package-lock.json release-staging/
if [ -d dist ]; then cp -a dist release-staging/; fi
if [ -d services/clearglass_agent_service ]; then cp -a services/clearglass_agent_service release-staging/; fi
tar -czf release-bundle.tar.gz -C release-staging .
sha256sum release-bundle.tar.gz | tee artifacts/evidence/release-bundle.sha256
printf '%s\n' "revision=$CIRCLE_SHA1" 'immutable=true' > artifacts/evidence/release-manifest.txt

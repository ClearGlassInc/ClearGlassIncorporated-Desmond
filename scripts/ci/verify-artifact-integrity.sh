#!/usr/bin/env bash
set -euo pipefail
[ -f release-bundle.tar.gz ] || { echo 'NOT VERIFIED: release artifact missing' >&2; exit 2; }
[ -f artifacts/evidence/release-manifest.json ] || { echo 'NOT VERIFIED: release manifest missing' >&2; exit 2; }
actual=$(sha256sum release-bundle.tar.gz | awk '{print $1}')
expected=$(python3 -c 'import json; print(json.load(open("artifacts/evidence/release-manifest.json"))["artifact_sha256"])')
[ "$actual" = "$expected" ] || { echo 'NOT VERIFIED: artifact digest mismatch' >&2; exit 2; }
if [ -n "${EXPECTED_ARTIFACT_SHA256:-}" ] && [ "$actual" != "$EXPECTED_ARTIFACT_SHA256" ]; then echo 'NOT VERIFIED: supplied artifact digest does not match' >&2; exit 2; fi
printf '%s\n' "artifact_sha256=$actual" > artifacts/evidence/artifact-integrity.txt
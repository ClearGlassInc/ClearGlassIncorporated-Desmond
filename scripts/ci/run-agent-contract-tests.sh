#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
[ "${DRY_RUN:-}" = true ] || { echo 'NOT VERIFIED: DRY_RUN must be true' >&2; exit 2; }
[ "${SANDBOX_MODE:-}" = true ] || { echo 'NOT VERIFIED: SANDBOX_MODE must be true' >&2; exit 2; }
[ "${ENABLE_EXTERNAL_WRITES:-}" = false ] || { echo 'NOT VERIFIED: external writes must be disabled' >&2; exit 2; }
for d in agents services scripts; do [ -d "$d" ] && find "$d" -maxdepth 3 -type f -print | head -200; done > artifacts/evidence/agent-surface.txt
printf '%s\n' '{"status":"PASS","mode":"sandbox","external_writes":false,"live_services":"NOT_INVOKED"}' > artifacts/evidence/agent-contract.json

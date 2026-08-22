#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
[ "${DRY_RUN:-false}" = true ] || { echo 'agent tests require DRY_RUN=true' >&2; exit 1; }
[ "${SANDBOX_MODE:-false}" = true ] || { echo 'agent tests require SANDBOX_MODE=true' >&2; exit 1; }
[ "${ENABLE_EXTERNAL_WRITES:-true}" = false ] || { echo 'external writes are forbidden in agent tests' >&2; exit 1; }
if [ -d services/clearglass_agent_service ]; then
  python3 -m compileall -q services/clearglass_agent_service
  if [ -f services/clearglass_agent_service/requirements.txt ]; then grep -Eq '^([A-Za-z0-9_.-]+)==[0-9]' services/clearglass_agent_service/requirements.txt || { echo 'agent dependencies must be exact pins' >&2; exit 1; }; fi
  if grep -RInE 'subprocess|os\.system|requests\.(post|put|delete)|httpx\.(post|put|delete)' services/clearglass_agent_service --exclude-dir='__pycache__' > artifacts/evidence/agent-write-surfaces.txt 2>/dev/null; then :; fi
fi
printf '%s\n' 'dry_run=true' 'sandbox=true' 'external_writes=false' 'status=PASS' > artifacts/evidence/agent-contract.txt

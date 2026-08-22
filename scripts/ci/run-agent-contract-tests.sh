#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
[ "${DRY_RUN:-}" = true ] || { echo 'NOT VERIFIED: DRY_RUN=true required' >&2; exit 2; }
[ "${SANDBOX_MODE:-}" = true ] || { echo 'NOT VERIFIED: SANDBOX_MODE=true required' >&2; exit 2; }
[ "${ENABLE_EXTERNAL_WRITES:-}" = false ] || { echo 'NOT VERIFIED: external writes disabled required' >&2; exit 2; }
python_files="$(find agents services -type f -name '*.py' 2>/dev/null | sort || true)"
if [ -n "$python_files" ]; then
  while IFS= read -r f; do python3 -m py_compile "$f"; done <<< "$python_files"
fi
schema_count="$(find agents services -type f \( -iname '*schema*.json' -o -iname '*schema*.yaml' -o -iname '*schema*.yml' \) 2>/dev/null | wc -l | tr -d ' ')"
health="NOT_CONFIGURED"
if [ -n "${AGENT_HEALTH_URL:-}" ]; then
  curl --fail --silent --show-error --max-time 10 "$AGENT_HEALTH_URL" > artifacts/evidence/agent-health.json
  health="PASS"
fi
startup="NOT_CONFIGURED"
if [ -n "${AGENT_STARTUP_COMMAND:-}" ]; then
  timeout 20 bash -c "$AGENT_STARTUP_COMMAND" > artifacts/evidence/agent-startup.log 2>&1
  startup="PASS"
fi
python3 - "$health" "$startup" "$schema_count" <<'PY'
import json,sys
m={'schema_version':'1.0','status':'PASS','dry_run':True,'sandbox_mode':True,'external_writes':False,'startup_check':sys.argv[2],'schema_files':int(sys.argv[3]),'health_check':sys.argv[1]}
json.dump(m,open('artifacts/evidence/agent-contract.json','w'),indent=2); print(json.dumps(m,indent=2))
PY

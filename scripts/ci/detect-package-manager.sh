#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
pm=unknown
if [ -f package-lock.json ]; then pm=npm; elif [ -f pnpm-lock.yaml ]; then pm=pnpm; elif [ -f yarn.lock ]; then pm=yarn; fi
node_v=$(node --version 2>/dev/null || echo unavailable)
npm_v=$(npm --version 2>/dev/null || echo unavailable)
printf 'package_manager=%s\nnode=%s\nnpm=%s\n' "$pm" "$node_v" "$npm_v" | tee artifacts/evidence/toolchain.txt
python3 - "$pm" "$node_v" "$npm_v" <<'PY'
import json,sys
json.dump({'package_manager':sys.argv[1],'node':sys.argv[2],'npm':sys.argv[3]},open('artifacts/evidence/toolchain.json','w'),indent=2)
PY
[ "$pm" != unknown ] || { echo 'NOT VERIFIED: no supported Node lockfile found' >&2; exit 2; }
#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
count=0
for f in package-lock.json pnpm-lock.yaml yarn.lock requirements.txt poetry.lock uv.lock; do
  if [ -f "$f" ]; then echo "present: $f"; sha256sum "$f" >> artifacts/evidence/lockfile.sha256; count=$((count+1)); fi
done
[ "$count" -gt 0 ] || { echo 'NOT VERIFIED: no lockfile detected' >&2; exit 2; }
if [ -f package-lock.json ]; then npm ci --dry-run --ignore-scripts >/dev/null; fi
python3 - <<'PY'
import json,glob
json.dump({'status':'PASS','lockfiles':[x.strip() for x in open('artifacts/evidence/lockfile.sha256') if x.strip()]},open('artifacts/evidence/lockfiles.json','w'),indent=2)
PY
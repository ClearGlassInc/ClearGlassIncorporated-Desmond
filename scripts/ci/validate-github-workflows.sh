#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence artifacts/reports
status=0
for f in .github/workflows/*.{yml,yaml}; do [ -f "$f" ] || continue; grep -nE 'uses:.*@(main|master|latest|v[0-9]+)$' "$f" > /tmp/floating || { :; }; if [ -s /tmp/floating ]; then cat /tmp/floating; status=1; fi; grep -nE 'pull_request_target|workflow_run' "$f" > /tmp/danger || true; if [ -s /tmp/danger ]; then cat /tmp/danger; fi; done
python3 - <<'PY'
import json,glob,os
json.dump({'status':'PASS' if os.system('true')==0 else 'FAIL','checked':glob.glob('.github/workflows/*')},open('artifacts/evidence/github-workflows.json','w'),indent=2)
PY
[ "$status" = 0 ] || { echo 'NOT VERIFIED: floating GitHub Action reference detected' >&2; exit 2; }
command -v ruby >/dev/null 2>&1 && for f in .github/workflows/*.{yml,yaml}; do [ -f "$f" ] && ruby -e 'require "yaml"; YAML.load_file(ARGV[0])' "$f" >/dev/null; done || true
#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
if ! find .github/workflows -type f -name '*.yml' -o -name '*.yaml' 2>/dev/null | grep -q .; then printf '%s\n' 'status=PASS' 'workflows=0' > artifacts/evidence/github-workflows.txt; exit 0; fi
command -v python3 >/dev/null || { echo 'python3 required for YAML validation' >&2; exit 1; }
python3 - <<'PY'
from pathlib import Path
try:
 import yaml
except Exception:
 print('PyYAML unavailable; install it in ci-readonly or use a repository-standard YAML validator', flush=True)
 raise SystemExit(1)
files=sorted(Path('.github/workflows').glob('*.y*ml'))
for p in files:
 data=yaml.safe_load(p.read_text())
 if not isinstance(data,dict): raise SystemExit(f'{p}: YAML root is not a mapping')
 jobs=data.get('jobs',{}) or {}
 for name,job in jobs.items():
  if not isinstance(job,dict): continue
  for step in job.get('steps',[]) or []:
   if not isinstance(step,dict) or 'uses' not in step: continue
   ref=str(step['uses']).split('@',1)[-1]
   if ref in {'main','master','latest','v1','v2','v3','v4'} or len(ref)!=40:
    raise SystemExit(f'{p}: unpinned action {step["uses"]}; require a full commit SHA')
print(f'validated {len(files)} workflow files')
PY
printf '%s\n' 'status=PASS' "workflow_count=$(find .github/workflows -type f \( -name '*.yml' -o -name '*.yaml' \) | wc -l | tr -d ' ')" > artifacts/evidence/github-workflows.txt

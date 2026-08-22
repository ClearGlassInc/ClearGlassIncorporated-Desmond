#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
python3 - <<'PY'
import json,sys
from pathlib import Path
try:
 import yaml
except Exception as e:
 print(f'PyYAML unavailable: {e}',file=sys.stderr); raise SystemExit(2)
files=sorted(Path('.github/workflows').glob('*.y*ml'))
findings=[]
for p in files:
 try:
  data=yaml.safe_load(p.read_text(encoding='utf-8'))
  if not isinstance(data,dict): findings.append({'file':str(p),'type':'invalid_yaml_root'})
  else:
   for job_name,job in (data.get('jobs') or {}).items():
    for step in (job or {}).get('steps',[]) or []:
     if isinstance(step,dict) and 'uses' in step:
      use=str(step['uses']); ref=use.split('@',1)[1] if '@' in use else ''
      if ref in {'main','master','latest','v1','v2','v3','v4'} or len(ref)!=40:
       findings.append({'file':str(p),'job':job_name,'uses':use,'type':'unpinned_action'})
 except Exception as e:
  findings.append({'file':str(p),'type':'yaml_parse_error','error':str(e)})
result={'schema_version':'1.0','status':'PASS' if not findings else 'FAIL','workflow_count':len(files),'findings':findings}
json.dump(result,open('artifacts/evidence/workflow-integrity.json','w'),indent=2); print(json.dumps(result,indent=2))
if findings: raise SystemExit(1)
PY

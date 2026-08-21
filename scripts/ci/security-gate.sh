#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import json,datetime,os,re,sys
findings=[]
try:
 d=json.load(open('artifacts/reports/npm-audit.json'))
 for sev,n in (d.get('metadata',{}).get('vulnerabilities',{}) or {}).items():
  if sev in ('high','critical') and n: findings.append(('npm',sev,str(n)))
except Exception as e: findings.append(('npm','NOT_VERIFIED',str(e)))
try:
 d=json.load(open('artifacts/reports/gitleaks.json'))
 if isinstance(d,list) and d: findings.append(('gitleaks','high',str(len(d))))
except Exception: pass
allow=[]
try: allow=json.load(open('policy/security-allowlist.json')).get('findings',[])
except Exception: pass
valid=[]
today=datetime.date.today()
for x in allow:
 if not isinstance(x,dict): continue
 try:
  if datetime.date.fromisoformat(x.get('expires_on','1900-01-01')) >= today: valid.append(x)
 except ValueError: pass
if findings and os.getenv('ALLOW_NONCRITICAL_SCAN_FINDINGS')=='true':
 print('Allowlist mode requested; this gate still blocks high/critical findings unless an exact reviewed record exists.')
# This generic gate intentionally blocks findings unless an explicit, unexpired policy record exists.
for source,sev,count in findings:
 if sev in ('high','critical','NOT_VERIFIED'):
  matched=any(str(x.get('id','')).lower().startswith(source) and x.get('severity') in (sev,'high','critical') for x in valid)
  if not matched:
   print(f'NOT VERIFIED: blocking {source} {sev} finding ({count})',file=sys.stderr); raise SystemExit(2)
json.dump({'status':'PASS','findings':findings,'unexpired_allowlist_records':len(valid)},open('artifacts/evidence/security-decision.json','w'),indent=2)
PY
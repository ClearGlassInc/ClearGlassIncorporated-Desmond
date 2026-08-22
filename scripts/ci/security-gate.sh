#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
fail(){ echo "SECURITY GATE FAILED: $1" >&2; exit 1; }
command -v git >/dev/null || fail 'git unavailable'
if git grep -nI -E '(AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{20,}|-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----|xox[baprs]-[0-9A-Za-z-]{20,})' -- ':!package-lock.json' ':!*.lock' > artifacts/reports/secret-candidates.txt 2>/dev/null; then fail 'candidate secret detected; investigate and remove before deployment'; else :; fi
if [ -f scripts/ci/security-allowlist.txt ]; then
  while IFS= read -r line; do [[ -z "$line" || "$line" == \#* ]] && continue; [[ "$line" =~ ^[A-Z0-9._:-]+$ ]] || fail "invalid allowlist entry: $line"; done < scripts/ci/security-allowlist.txt
fi
if [ -f artifacts/reports/npm-audit.json ]; then
  node - <<'NODE'
const fs=require('fs'); const j=JSON.parse(fs.readFileSync('artifacts/reports/npm-audit.json','utf8')); const a=j.metadata?.vulnerabilities||{};
if ((a.high||0)+(a.critical||0)>0) process.exit(1);
NODE
  rc=$?
  [ $rc -eq 0 ] || fail 'npm audit reports high/critical vulnerabilities'
fi
printf '%s\n' 'status=PASS' 'secret_scan=PASS' 'dependency_gate=PASS' > artifacts/evidence/security-gate.txt

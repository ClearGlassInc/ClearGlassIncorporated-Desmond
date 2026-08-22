#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
found=0
for f in package-lock.json pnpm-lock.yaml yarn.lock; do if [ -f "$f" ]; then found=1; echo "$f"; fi; done | tee artifacts/evidence/lockfiles-found.txt
[ "$found" -eq 1 ] || { echo 'LOCKFILE FAILED: no supported lockfile found' >&2; exit 1; }
if [ -f package-lock.json ]; then node -e "const p=require('./package-lock.json'); if(![2,3].includes(p.lockfileVersion)) process.exit(1)" || { echo 'LOCKFILE FAILED: invalid npm lockfileVersion' >&2; exit 1; }; npm ci --ignore-scripts --dry-run >/dev/null; fi
printf '%s\n' 'status=PASS' 'lockfile_integrity=checked' > artifacts/evidence/lockfiles.txt

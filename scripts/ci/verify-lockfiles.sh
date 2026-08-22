#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
[ -f package-lock.json ] || { echo 'LOCKFILE FAILED: package-lock.json is required' >&2; exit 1; }
node -e "const p=require('./package-lock.json'); if(p.lockfileVersion!==3) process.exit(1)" || { echo 'LOCKFILE FAILED: expected npm lockfileVersion 3' >&2; exit 1; }
npm ci --ignore-scripts --dry-run >/dev/null
printf '%s\n' 'package_manager=npm' 'install=npm_ci' 'lockfile=package-lock.json' 'status=PASS' > artifacts/evidence/lockfiles.txt

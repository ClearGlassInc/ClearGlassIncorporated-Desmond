#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/release
rm -f release-bundle.tar.gz

git archive --format=tar --prefix=release/ HEAD | gzip -n > release-bundle.tar.gz
artifact_sha256="$(sha256sum release-bundle.tar.gz | awk '{print $1}')"
printf '%s  %s\n' "$artifact_sha256" release-bundle.tar.gz > artifacts/release/artifact.sha256
python3 - "$artifact_sha256" <<'PY'
import json, os, sys
from datetime import datetime, timezone
m={
 'schema_version':'1.0',
 'git_sha':os.getenv('CIRCLE_SHA1',''),
 'circle_pipeline_id':os.getenv('CIRCLE_PIPELINE_ID',''),
 'build_timestamp':datetime.now(timezone.utc).isoformat(),
 'artifact_sha256':sys.argv[1],
 'deployment_target':os.getenv('TARGET_ENVIRONMENT','none')
}
with open('artifacts/release/manifest.json','w',encoding='utf-8') as f: json.dump(m,f,indent=2); f.write('\n')
PY
cat artifacts/release/manifest.json

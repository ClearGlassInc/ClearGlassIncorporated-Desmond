#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/evidence
rm -f release-bundle.tar.gz
# Package only tracked repository content; never include .git metadata or secrets.
git archive --format=tar --prefix=release/ HEAD | gzip -n > release-bundle.tar.gz
sha=$(sha256sum release-bundle.tar.gz | awk '{print $1}')
lock_digest=$(cat artifacts/evidence/lockfile.sha256 2>/dev/null | sha256sum | awk '{print $1}')
python3 - "$sha" "$lock_digest" <<'PY'
import json,os,sys,datetime
manifest={'schema_version':'1.0','git_sha':os.getenv('CIRCLE_SHA1',''),'release_ref':os.getenv('RELEASE_REF',''),'circle_pipeline_id':os.getenv('CIRCLE_PIPELINE_ID',''),'circle_workflow_id':os.getenv('CIRCLE_WORKFLOW_ID',''),'utc_build_timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'artifact_sha256':sys.argv[1],'dependency_lockfile_digest':sys.argv[2],'deployment_target':os.getenv('TARGET_ENVIRONMENT','none')}
json.dump(manifest,open('artifacts/evidence/release-manifest.json','w'),indent=2)
PY
cat artifacts/evidence/release-manifest.json
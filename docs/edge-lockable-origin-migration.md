# Lockable Static-Origin Migration Gate

Status: target decision and credentials required; no hosting migration has been
performed.

## Decision

GitHub Pages cannot require an edge-only header, authenticated origin pull,
mTLS, provider egress ACL, or private-network path. Proxying the custom hostname
reduces ordinary exposure but cannot make the Pages origin non-bypassable.

Keep Pages when that residual risk is accepted. If non-bypassable origin access
is a requirement, select and approve one of these lockable patterns before
changing production DNS:

| Pattern | Required origin lock | Operational trade-off |
|---|---|---|
| Private object storage + CDN origin access identity/control | Bucket denies public access and accepts only the CDN identity | Strong static-origin isolation; adds a second cloud/provider and deployment identity |
| Private object storage + Cloudflare Worker/Pages replacement | Public development endpoint disabled; Worker/service binding is the only object path | Keeps traffic at Cloudflare; requires Worker/R2 lifecycle, quotas, logging, and rollback ownership |
| Application container behind private connectivity or mTLS | Public ingress disabled or rejects clients without provider identity | Flexible headers/routing; higher patching, scaling, and availability burden for a static site |

## Non-negotiable acceptance criteria

1. `tools/build_pages.py` remains the canonical sanitized build and produces an
   immutable artifact digest recorded with the deployment.
2. The origin is private or cryptographically authenticates the edge; a secret
   hostname is not an access control.
3. Direct object/container/origin URLs return deny responses from an external
   network while the proxied hostname serves the identical artifact.
4. Deployment and rollback identities are distinct from the edge-policy token,
   least-privileged, short-lived where supported, and protected by reviewers.
5. Cache invalidation is bounded to the changed release and cannot expose stale
   personalized/dynamic content.
6. Certificate issuance/renewal, DNS, origin denial, security headers, CSP mode,
   and representative assets pass `Edge Assurance` before production traffic.
7. Production DNS has a documented, tested rollback to the prior known-good
   host without deleting the new origin or its evidence.

## Migration sequence

1. Choose the target/provider, region/residency, availability objective, cost
   owner, retention/logging policy, and recovery-time objective in a change
   record.
2. Provision the non-production private origin and deploy the exact Pages build
   artifact without changing the production record.
3. Add a separate proxied staging hostname and validate origin denial from an
   external network plus edge success from multiple resolvers/vantage points.
4. Run a full content/hash comparison, link/assets test, CSP report window,
   accessibility/performance check, and bounded assurance/smoke suite.
5. Lower only the production web-record TTL if useful, obtain approval, cut over
   the web record, and monitor errors/cache/certificates.
6. Keep Pages unchanged for the rollback window. Retire it only after the
   acceptance window and evidence review; do not delete the old origin during
   the cutover.

No repository code can safely choose the cloud account, create billable storage,
or change authoritative DNS without the target decision, approved credentials,
and change window.

# Edge Provider Setup

Reference provider: Cloudflare. Every DNS, zone, certificate, dashboard, list, origin, state-backend, and credential action below is manual. Repository automation does not represent any of them as complete.

## Operator-supplied values

Record these in the approved change ticket; do not commit secret values:

- provider account, zone, subscription/plan, and zone owner
- authoritative DNS provider and registrar owner
- Cloudflare account ID and zone ID
- zone name and public hostname
- exact GitHub Pages target shown in repository Pages settings
- optional API/admin hostnames and their real origin endpoints
- authoritative Terraform state owner and whether `clearglass-commerce/infra/cloudflare` already owns each phase
- remote-state bucket/key/region, encryption, versioning, and lock-file support
- plan/apply token owners and expiry/rotation dates
- log destination, privacy owner, retention, and alert routes
- approved trusted/monitoring/automation CIDRs, ASNs, country exceptions, and list owners
- rollback decision owner, incident channel, and maintenance window

## 1. Resolve Terraform state ownership

Cloudflare ruleset phases are zone-level resources. Before planning:

1. Inventory live zone rulesets and every Terraform state that manages this zone.
2. Compare them with `clearglass-commerce/infra/cloudflare` and `infra/edge`.
3. Treat `infra/edge` as the sole target owner. The historical
   `clearglass-commerce/infra/cloudflare` configuration is frozen by
   `ownership_guard.tf` and must not be independently planned/applied.
4. Pull the legacy state, preserve it in recoverable protected storage, and
   record its serial and SHA-256. Detach only the mapped resources from the
   legacy state without destroying provider objects.
5. Promote the matching `infra/edge` resource flags in a reviewed configuration
   with observation-safe actions and the import change ticket.
6. Complete an external copy of `infra/edge/import-manifest.example.json`, seal
   it as `EDGE_TF_IMPORT_MANIFEST_B64`, and dispatch `Edge State Import` with the
   decoded manifest digest and exact confirmation string. The workflow validates
   allowlisted addresses/import formats, uses locked state, produces a
   post-import plan, and never applies provider changes.
7. Record the import run, manifest digest, legacy snapshot digest, destination
   state serial, and post-import plan decision in the change ticket.
8. Do not proceed if any normal plan proposes an unexplained create/delete or a
   second owner for a zone phase.

## 2. Create the locked remote-state backend

The workflow uses the S3-compatible Terraform backend declared in `backend.tf`. This may be AWS S3 or a compatible provider approved by the platform team.

Manual prerequisites:

1. Create a dedicated state bucket/container with encryption, versioning, restricted public access, recovery controls, and audit logging.
2. Grant plan/apply identities only the minimum object/list/lock permissions for this edge-state prefix.
3. Copy `infra/edge/backend.example.hcl` out of the repository and replace bucket, key, and region. Keep `encrypt = true` and `use_lockfile = true`.
4. Do not put access keys or tokens in the HCL.
5. Base64-encode the completed noncredential backend file as one line and store it in each protected GitHub environment as `EDGE_TF_BACKEND_CONFIG_B64`.
6. Store state credentials as the environment secrets documented in `infra/edge/README.md`.
7. Test recovery of a prior object version before production use.

## 3. Create or select the Cloudflare zone

1. Add or select `clearglassinc.com` in the correct account.
2. Import and compare every current DNS record before changing authority. Preserve MX, SPF, DKIM, DMARC, CAA, verification, and non-HTTP records exactly.
3. If Cloudflare is not authoritative, review the imported zone and then change registrar nameservers in a controlled window.
4. If DNSSEC is active, follow the provider migration sequence. Do not leave stale DS records at the registrar.
5. Wait until the provider reports the zone active; verify independently with multiple resolvers.
6. Do not proxy mail or unsupported non-HTTP services.

## 4. Configure GitHub Pages custom-domain behavior

1. In GitHub repository Pages settings, confirm the deployment source and custom domain are correct.
2. Record the exact DNS target GitHub currently prescribes. Do not infer it from an old example.
3. Keep the root `CNAME` aligned with the public hostname unless the public hostname itself is intentionally changing.
4. Allow GitHub Pages to validate the custom domain and issue/renew its certificate.
5. Enable GitHub Pages HTTPS enforcement only after its certificate is healthy.
6. Confirm the repository/domain-verification controls appropriate to the organization to reduce custom-domain takeover risk.

## 5. Configure the proxied web record

1. Create or update only the public web record using the exact Pages target from the previous section.
2. Start DNS-only while validating the Pages custom domain and certificate.
3. Lower only that record's TTL before the approved cutover if useful.
4. During cutover, switch the web record to proxied.
5. Do not create speculative origin records and do not point API/admin names at Pages.
6. Validate A/AAAA/CNAME answers from multiple networks and confirm edge-specific response evidence.

## 6. Configure TLS

- Visitor TLS: enable modern certificates, TLS 1.3, and a minimum of TLS 1.2 unless a documented compatibility exception exists.
- Redirect HTTP to HTTPS only after representative pages and integrations work over HTTPS.
- Origin TLS: use certificate validation. Select strict mode only after the actual Pages/custom-domain origin certificate and SNI path validate. Do not downgrade verification to conceal a hostname/certificate mismatch.
- HSTS: begin without `includeSubDomains` or `preload`. Promote only after every affected hostname is permanently HTTPS-ready.
- Dynamic origins: install provider/origin certificates or mTLS as required, rotate before expiry, and alert on issuance/expiry failures.

## 7. Configure WAF, DDoS, bots, lists, and caching

1. Confirm the subscription exposes each Terraform field/action before enabling it.
2. Keep provider-managed DDoS protection enabled; do not generate DDoS test traffic.
3. Apply managed WAF and custom detections in staging/log mode first.
4. Keep geo/ASN rules disabled until an approved use case and exceptions exist.
5. Keep Super Bot Fight Mode disabled by default. With API/admin hostnames, do not use zone-wide browser challenges for automation; use hostname-scoped bot-score rules.
6. Preserve provider-verified crawlers. Add monitoring/internal automation exceptions only from provider-published or organization-controlled CIDRs.
7. If using named lists for anonymous networks or Tor, create and steward them manually. Start with log/managed challenge; reputation alone cannot justify a permanent block.
8. Configure static/HTML cache behavior from `cache-policy.example.json`. Explicitly bypass sensitive dynamic routes and responses.
9. Enable tiered cache/origin shield only after plan availability and origin behavior are confirmed. For Pages this improves cache hierarchy but does not make the origin private.
10. Use high-security/emergency mode only through the time-bounded runbook or record equivalent dashboard changes with owner, ticket, expiry, and later state reconciliation.

## 8. Configure dynamic origin access

GitHub Pages cannot consume `origin.tf` authentication. For API/admin hosts:

1. Prefer private networking, provider authenticated origin pull/mTLS, and provider egress ACLs.
2. If using the shared-header template, generate at least 256 bits of random secret material.
3. Store the value in `EDGE_ORIGIN_AUTH_HEADER_VALUE`; never commit it.
4. Configure the edge to overwrite the header for dynamic hostnames only.
5. Configure the load balancer/origin to reject missing or invalid values before application routing. The FastAPI control plane now enforces
   `EDGE_ORIGIN_AUTH_REQUIRED`, `EDGE_ORIGIN_AUTH_HEADER_NAME`, and
   `EDGE_ORIGIN_AUTH_SECRETS`; the Next.js admin middleware enforces the same
   variables before public/session routing. Both accept current + previous
   secrets and fail closed on invalid production configuration.
6. Remove public ingress where the platform permits it.
7. Test direct-origin denial and edge-origin success before production cutover.
8. Rotate the secret after suspected disclosure, origin compromise,
   personnel/provider change, and on the approved schedule:
   - add the new value before the current value in each origin's accepted-secret list;
   - deploy and verify both values are accepted at the origin through a private test path;
   - update `EDGE_ORIGIN_AUTH_HEADER_VALUE` at the edge and apply the reviewed transform;
   - prove proxied requests succeed and direct-origin/missing/old-only requests fail;
   - remove the previous value from origins after the overlap window and record
     both deployments in the change ticket.

## 8A. Move forms and CSP reports behind the API hostname

The control plane exposes two disabled-by-default public surfaces:

- `/api/forms/submit`: schema-bounded JSON, consent required, honeypot handling,
  per-client throttle, no redirect following, and an HTTPS relay host allowlist.
- `/api/security/csp-report`: 16 KiB maximum, CSP/Reporting API content types,
  normalized origins/directives only, with paths, queries, snippets, and client
  IPs omitted from application logs.

For form rollout, set `PUBLIC_FORMS_ENABLED=true`, an HTTPS
`PUBLIC_FORM_RELAY_URL`, `PUBLIC_FORM_RELAY_ALLOWED_HOSTS`, and optional relay
bearer token only on an origin that also has edge-origin authentication enabled.
The static pages contain an empty `clearglass-api-base` migration switch; set it
first in the non-production artifact only after the API hostname passes edge
success and direct-origin denial. Remove FormSubmit/Formspree actions and CSP
sources only after every supported form succeeds through the first-party API.

Set `EDGE_CSP_REPORT_URI` to the protected API collector and keep
`csp_mode=report-only`. Export normalized logs to
`analyze_csp_reports.py`; reported sources are never automatically added to CSP.
Enforcement requires a reviewed report, no unresolved source classes, completion
of the inventory's manual-review items, a seven-day evidence window, and an
enforce-stage configuration.

## 9. Configure logging, dashboards, and alerts

1. Create an encrypted, access-controlled log destination compatible with the selected plan.
2. Configure `EDGE_LOGPUSH_DESTINATION` only after the destination exists.
3. Exclude cookies, authorization headers, bodies, passwords, and complete sensitive query values.
4. Leave full client-IP export off. Where feasible, omit/truncate IPs at source or keyed-hash them in a controlled downstream processor.
5. Implement the three exact dashboard specifications in
   `observability.example.json`: Cloudflare security operations, CSP readiness,
   and edge availability/drift. Its `deployment_status=not-applied` must change
   only after provider/dashboard owners verify the live objects and alert routes.
6. Route critical alerts to an owned on-call destination and warning alerts to the operational queue. Test delivery without fabricating an attack.
7. Recommended defaults: raw events 14–30 days, normalized metrics 90 days, configuration audit 365 days. Apply legal/privacy requirements and make retention configurable.
8. Set `EDGE_ASSURANCE_ENABLED=true` only after an approved staging hostname is
   live and configure `EDGE_STAGING_BASE_URL`, allowed hosts, and expected CSP
   mode. Set `EDGE_DRIFT_ENABLED=true` only after remote state/import is complete.
   The weekly workflow uploads certificate/DNS/header/smoke and Terraform plan
   evidence; drift exit code 2 fails after artifact upload.

## 10. Configure GitHub environments and credentials

Create:

- `edge-staging-plan`
- `edge-staging`
- `edge-production-plan`
- `edge-production` with required reviewers and restricted deployment branches

Use different plan/read and apply/write Cloudflare tokens, scoped to the exact account/zone and enabled resource types. Do not grant DNS write: this module contains no DNS resources. Configure environment secrets/variables from `infra/edge/README.md`. Apply/rollback must require the protected environment; production apply is dispatched from `main` only.

## 11. First deployment sequence

1. Merge only safe, disabled environment configuration.
2. Dispatch `operation=plan`, `environment=staging`; verify no unexpected imports/deletes/replacements.
3. Import any existing zone-phase resources through the protected state workflow
   before the first destination apply.
4. In staging, set `rollout_stage=observe` plus owner/ticket/rationale and enable logging only in a reviewed PR; plan, approve, and apply.
5. Enable managed/custom WAF in log mode in a reviewed PR while remaining at `observe`; plan, approve, and apply.
6. Validate a proxied staging hostname using the full test matrix.
7. Run `analyze_security_events.py` on reviewer-labeled evidence. Move staging to
   `challenge` and promote only selected rule classes whose gates pass.
8. Move selected high-confidence rules to `block` only with zero-FP evidence,
   adequate malicious samples, low unknown rate, low challenge solve rate, and
   an enforce-stage PR carrying the evidence SHA/window.
9. Complete the manual DNS cutover runbook for production.

## Alternative provider mapping

Use `infra/edge/providers/provider-mapping.example.json` as the implementation checklist:

- Fastly: Next-Gen WAF/VCL, ACLs, rate counters, shielding, header transforms, and log streaming.
- AWS: CloudFront, AWS WAF, Shield, cache/origin request policies, Origin Access Control for S3, protected ALB/API origins, and logs/alarms.
- Azure: Front Door Premium WAF, bot/managed rules, Rules Engine, Private Link where supported, diagnostics, and Monitor alerts.

Provider migration must preserve rule intent and safety state; Cloudflare expressions and managed-rule IDs are not portable.

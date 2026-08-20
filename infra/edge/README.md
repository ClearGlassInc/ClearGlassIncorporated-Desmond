# ClearGlass Edge Security

Provider-neutral perimeter policy with a Cloudflare Terraform reference adapter.

This directory contains no DNS resource and does not prove provider activation. DNS, nameservers, certificates, proxied records, named IP lists, log destinations, origin controls, plan features, GitHub environments, and provider credentials are manual prerequisites.

## Layout

| Path | Purpose |
|---|---|
| `policy.schema.json` | Strict neutral-policy JSON Schema |
| `policies/baseline.json` | Versioned DDoS/WAF/bot/reputation/rate/geo/header/cache/origin/logging intent |
| `environments/*.tfvars.json` | Reviewed staging/production feature/action promotions; all disabled/log-only initially |
| `providers/` | Provider-neutral mapping template for Cloudflare/Fastly/AWS/Azure |
| `main.tf`, `variables.tf`, `advanced_variables.tf` | Provider pin, host/route scopes, safe typed inputs and cross-variable checks |
| `waf.tf` | Custom, managed, bot-score, reputation, IP, geo/ASN, and emergency rules |
| `rate_limits.tf` | Independent asset/HTML/auth/reset/search/form/API/admin/webhook policies |
| `bot.tf` | Optional zone-wide provider bot settings, disabled by default |
| `headers.tf` | Public CSP Report-Only/security transforms and dynamic baseline transforms |
| `origin.tf` | Optional edge-overwritten dynamic-origin identity header; never Pages |
| `logging.tf` | Optional privacy-minimized firewall-event Logpush |
| `backend.tf`, `backend.example.hcl` | Locked S3-compatible remote-state declaration/template |
| `csp-inventory.json` | Built-artifact CSP report-only candidate and review warnings |
| `cache-policy.example.json` | Provider-neutral cache/shield/bypass and poisoning controls |
| `origin-access.example.json` | Pages limitation and dynamic-origin requirements |
| `observability.example.json` | Dashboards, alerts, retention and privacy |
| `tests/test-matrix.json` | Functional/negative/provider/manual test coverage |
| `scripts/validate_policy.py` | Dependency-free schema plus policy invariants |
| `scripts/validate_terraform_safety.py` | State, DNS, phase ownership, workflow and safe-environment guard |
| `scripts/render_runtime_config.py` | Protected environment inputs to ephemeral mode-0600 tfvars |
| `scripts/audit_csp_sources.py` | Compares exact built artifact with CSP inventory |
| `scripts/analyze_csp_reports.py` | Aggregates privacy-minimized reports without auto-widening policy |
| `scripts/analyze_security_events.py` | Reviewer-labeled false-positive analysis and non-mutating action recommendations |
| `scripts/import_state.py` | Allowlisted single-owner state import with manifest/change-control validation |
| `scripts/assurance_check.py` | Bounded DNS, TLS/certificate, proxy, CSP and header checks |
| `scripts/smoke_test.py` | Navigation, assets, headers, HTTPS, cache, API/CORS checks |
| `scripts/negative_security_test.py` | Dry-run by default; bounded WAF/rate/size/origin/cache probes |

## Critical state-ownership rule

Cloudflare ruleset phases are zone-level entry points. The historical
`clearglass-commerce/infra/cloudflare` stack contains custom WAF, managed WAF,
rate-limit, bot, and Logpush resources for the same zone. It is now frozen by a
default-deny Terraform precondition; `infra/edge` is the sole target owner.

Do not enable the same phase in two Terraform states. Capture and hash the
legacy state, detach the exact resources from that state without destroying
them, enable their reviewed destination resources, and use the protected
`Edge State Import` workflow. The sealed manifest is checked against the zone,
change ticket, legacy snapshot metadata, allowlisted resource address/import
format, and destination feature flags. The workflow imports into locked state,
uploads a post-import plan, and never runs provider apply.

## Safe defaults

- all provider-mutating feature groups false in staging and production
- all custom/managed/rate/reputation actions `log`
- geo/ASN, emergency, bot score, zone-wide bot mode, body-size fields, Logpush, security headers, and origin authentication disabled
- verified bots and trusted operations protected from generic challenges, without skipping managed WAF
- no broad automation deny or reputation-only permanent block
- no browser challenge on webhooks
- CSP Report-Only; HSTS includeSubDomains/preload false
- no full client-IP export or sensitive request fields
- emergency mode requires reviewed custom-WAF ownership, operator, ticket, and expiry within 24 hours
- challenge/enforce requires a reviewed evidence SHA and completed observation window of at least seven days

## Reviewed promotion model

Each environment file carries `policy_version`, `rollout_stage`, `deployment_owner`, `deployment_change_ticket`, and `configuration_rationale`. The stages are:

- `disabled`: every provider feature false; staged action values remain log-only
- `observe`: enabled WAF/rate/reputation controls must be nonterminating log actions
- `challenge`: managed challenges may be introduced, but active block actions are rejected
- `enforce`: reviewed terminal actions, origin authentication, full-IP export, or expanded HSTS may be considered

Enabled features require owner/ticket/rationale. Production cannot be ahead of staging, and a production feature must also be enabled in staging. Terraform repeats these invariants using cross-variable checks, including protected runtime deny lists and emergency inputs.

## Tool requirements

- Python 3.11+
- Terraform 1.10+ and below 2.0; CI installs digest-pinned Terraform 1.14.6
- Cloudflare provider exactly `4.40.0`, matching the repository's existing adapter contract
- Cloudflare plan/API fields required by each enabled feature
- encrypted/versioned S3-compatible remote state with `use_lockfile = true`

## Protected GitHub environments

Create:

- `edge-staging-plan`: read/plan identities
- `edge-staging`: write/apply identities; recommended reviewers
- `edge-production-plan`: read/plan identities
- `edge-production`: write/apply identities, required reviewers, protected branch restriction

Pull requests and pushes run validation only. `plan`, `apply`, `rollback`, and `smoke` are manual dispatch operations. Production apply must be dispatched from `main`; rollback requires a full commit SHA reachable from `main` and a change/incident ticket.

## Required secrets

Configure in the appropriate protected environments; never commit values.

| Secret | Environments | Purpose |
|---|---|---|
| `EDGE_TF_BACKEND_CONFIG_B64` | plan + apply | Base64 noncredential backend HCL with bucket/key/region/encrypt/use_lockfile |
| `EDGE_TF_STATE_ACCESS_KEY_ID` | plan + apply | Least-privilege state access identity |
| `EDGE_TF_STATE_SECRET_ACCESS_KEY` | plan + apply | State access credential |
| `EDGE_TF_STATE_SESSION_TOKEN` | plan + apply, optional | Short-lived session credential where used |
| `CLOUDFLARE_EDGE_PLAN_TOKEN` | plan only | Read/refresh plus minimum plan permissions |
| `CLOUDFLARE_EDGE_APPLY_TOKEN` | apply only | Minimum writes for enabled resources; no DNS write |
| `EDGE_LOGPUSH_DESTINATION` | plan + apply when enabled | Pre-created destination, treated as secret when it embeds credentials |
| `EDGE_ORIGIN_AUTH_HEADER_VALUE` | plan + apply when enabled | 32+ character high-entropy dynamic-origin identity |
| `EDGE_TF_IMPORT_MANIFEST_B64` | apply environment, import only | Sealed single-owner import manifest; decoded digest must match the dispatch input |

## Required and optional variables

Required in every plan/apply environment:

- `EDGE_CLOUDFLARE_ACCOUNT_ID`
- `EDGE_CLOUDFLARE_ZONE_ID`
- `EDGE_ZONE_NAME`
- `EDGE_PUBLIC_HOSTNAME`

Optional host and allow/reputation inputs:

- `EDGE_API_HOSTNAME`, `EDGE_ADMIN_HOSTNAME`
- `EDGE_TRUSTED_IPV4_CIDRS_JSON`, `EDGE_TRUSTED_IPV6_CIDRS_JSON`
- `EDGE_MONITORING_IPV4_CIDRS_JSON`, `EDGE_MONITORING_IPV6_CIDRS_JSON`
- `EDGE_AUTOMATION_IPV4_CIDRS_JSON`, `EDGE_AUTOMATION_IPV6_CIDRS_JSON`
- `EDGE_DENY_IPV4_CIDRS_JSON`, `EDGE_DENY_IPV6_CIDRS_JSON`
- `EDGE_QUARANTINE_IPV4_CIDRS_JSON`, `EDGE_QUARANTINE_IPV6_CIDRS_JSON`, `EDGE_QUARANTINE_EXPIRES_AT`
- `EDGE_TRUSTED_ASNS_JSON`, `EDGE_DENIED_ASNS_JSON`, `EDGE_CHALLENGE_ASNS_JSON`
- `EDGE_ALLOWED_COUNTRIES_JSON`, `EDGE_DENIED_COUNTRIES_JSON`, `EDGE_CHALLENGE_COUNTRIES_JSON`, `EDGE_GEO_EXCEPTION_COUNTRIES_JSON`
- `EDGE_ANONYMOUS_NETWORK_IP_LIST_NAME`, `EDGE_TOR_EXIT_IP_LIST_NAME`
- `EDGE_ORIGIN_AUTH_HEADER_NAME`
- `EDGE_CSP_REPORT_URI` (must be the protected API `/api/security/csp-report` URL)
- `EDGE_SMOKE_ALLOWED_HOSTS_JSON` for additional approved smoke targets

Every `*_JSON` variable must be a JSON array. Country codes are two letters; ASNs are JSON integers; network values are CIDRs. Runtime rendering validates types, hosts, CIDRs, time bounds, and feature prerequisites without printing values.

## Cloudflare token scope

Scope tokens to the exact account and zone and only the enabled resources: zone read, WAF/rulesets, transform rules, bot settings, and logs as needed. Planning uses a separate read-oriented token; apply uses a write token held only by the protected apply environment.

This module has no DNS resource, so it does not need DNS write permission. Do not grant it for convenience.

## Local validation

```bash
python3 infra/edge/scripts/validate_policy.py
python3 infra/edge/scripts/validate_terraform_safety.py
python3 tests/test_edge_security_policy.py -v
python3 -m py_compile infra/edge/scripts/*.py tests/test_edge_security_policy.py
python3 tools/build_pages.py /tmp/clearglass-pages-edge-audit
python3 infra/edge/scripts/audit_csp_sources.py \
  --root /tmp/clearglass-pages-edge-audit \
  --check
python3 infra/edge/scripts/negative_security_test.py \
  --base-url https://www.clearglassinc.com \
  --dry-run
terraform -chdir=infra/edge fmt -check -diff -recursive
terraform -chdir=infra/edge init -backend=false -input=false
terraform -chdir=infra/edge validate
```

`init -backend=false` validates the module only. A real plan must use the approved locked remote backend.

## Prepare backend and runtime inputs locally

Copy templates outside the repository:

```bash
cp infra/edge/backend.example.hcl /secure/path/edge-backend.hcl
cp infra/edge/variables.example /secure/path/edge-runtime.tfvars
```

Replace placeholders and export `CLOUDFLARE_API_TOKEN` through the operator's secret manager/session. Do not commit either file.

## Reviewable local plan

```bash
terraform -chdir=infra/edge init \
  -reconfigure \
  -input=false \
  -backend-config=/secure/path/edge-backend.hcl
terraform -chdir=infra/edge plan \
  -input=false \
  -lock-timeout=5m \
  -var-file=environments/staging.tfvars.json \
  -var-file=/secure/path/edge-runtime.tfvars \
  -out=/secure/path/edge.tfplan
terraform -chdir=infra/edge show -no-color /secure/path/edge.tfplan
```

The first plan should show no provider mutation because all feature groups are false. Unexpected imports/deletes/replacements indicate unresolved state ownership.

## Protected state import

The import workflow is intentionally unusable while the committed destination
feature remains false. That prevents importing a resource only to have the next
normal plan propose its destruction.

1. Pull the legacy state through its approved backend, preserve a recoverable
   copy outside the repository, and record its serial and SHA-256.
2. Freeze the legacy stack and detach only the mapped live resources from its
   state; do not destroy provider objects.
3. Copy `import-manifest.example.json` outside the repository and replace every
   placeholder with reviewed values and Cloudflare import IDs.
4. Promote the destination environment in a PR with the same change ticket and
   observation-safe actions.
5. Store the base64 manifest as `EDGE_TF_IMPORT_MANIFEST_B64`, dispatch
   `Edge State Import` with its decoded SHA-256 and the exact confirmation
   `<environment>:<ticket>:IMPORT`, then review the post-import plan artifact.

Partial import failure is recoverable but requires inspecting destination state
before retry. The workflow serializes state operations and retains import
evidence for 365 days.

## Controlled deployment

Preferred path: GitHub Actions `Edge Security` manual dispatch.

```bash
gh workflow run edge-security.yml \
  --ref main \
  -f operation=plan \
  -f environment=staging \
  -f base_url=https://STAGING_HOSTNAME \
  -f emergency_mode=false \
  -f execute_negative_tests=false \
  -f expect_enforcement=false
```

After reviewing and merging a configuration promotion:

```bash
gh workflow run edge-security.yml \
  --ref main \
  -f operation=apply \
  -f environment=staging \
  -f change_ticket=CHANGE_ID \
  -f base_url=https://STAGING_HOSTNAME \
  -f emergency_mode=false \
  -f execute_negative_tests=false \
  -f expect_enforcement=false
```

The workflow uses locked state, uploads a reviewable plan, records version/SHA/operator/timestamp, waits at the protected apply environment, rebuilds configuration, recomputes the plan, and refuses a changed digest. A successful apply still does not prove DNS is proxied or manual provider prerequisites are complete.

## Periodic assurance and drift

`Edge Assurance` is scheduled weekly but remains inert until the protected plan
environment sets `EDGE_ASSURANCE_ENABLED=true`. Set `EDGE_STAGING_BASE_URL`, the
approved hostname variables, and `EDGE_EXPECTED_CSP_MODE` only after the
non-production hostname exists. `EDGE_DRIFT_ENABLED=true` additionally enables
a locked read-token Terraform plan; detailed exit code 2 fails the job after a
reviewable plan artifact is uploaded. Scheduled negative security probes remain
dry-run only.

The live probe performs one bounded DNS/TLS/HTTP sequence, verifies certificate
expiry, same-host redirects, Cloudflare evidence, CSP mode, and security
headers, then exercises the existing low-volume smoke suite. It does not mutate
DNS, provider configuration, origins, or state.

## Emergency mode

Emergency is managed challenge only and requires `enable_custom_waf=true` already committed/reviewed:

```bash
gh workflow run edge-security.yml \
  --ref main \
  -f operation=apply \
  -f environment=production \
  -f change_ticket=INCIDENT_ID \
  -f base_url=https://www.clearglassinc.com \
  -f emergency_mode=true \
  -f emergency_expires_at=RFC3339_UTC_WITHIN_24_HOURS \
  -f execute_negative_tests=false \
  -f expect_enforcement=false
```

Disable it through a reviewed apply as soon as containment ends; do not wait for documentation alone to expire a live provider rule.

## Rollback

Dispatch `operation=rollback` with a full known-good SHA, target environment, and ticket. The same protected plan/apply controls apply. For a false positive, revert the narrow rule to log/disabled. Use DNS-only rollback only for provider/routing failure with explicit acceptance that the perimeter is bypassed. See `docs/rollback-and-recovery.md`.

## GitHub Pages limitation

The proxy protects ordinary traffic to the custom hostname, but Pages cannot validate the edge identity or reject GitHub-controlled direct access. `origin.tf` therefore targets API/admin hosts only. Migrate the static artifact to a private/authenticated object or application origin if non-bypassable origin security is required.

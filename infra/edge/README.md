# ClearGlass Edge Security

Provider-neutral perimeter policy with a Cloudflare Terraform reference implementation.

**This directory does not change DNS by itself.** Terraform manages supported edge resources only after an operator supplies the zone/account IDs and a least-privilege provider token. DNS cutover remains the manual procedure in `docs/dns-cutover-runbook.md`.

## Layout

- `policy.schema.json` - JSON Schema for neutral policies
- `policies/baseline.json` - baseline WAF/bot/reputation/rate/geo/header intent
- `main.tf` - provider and shared locals
- `variables.tf` - typed configuration and safe defaults
- `waf.tf` - custom WAF and managed-WAF entry point
- `rate_limits.tf` - route-specific rate limits
- `headers.tf` - edge response-header transforms
- `logging.tf` - optional Logpush configuration
- `variables.example` - operator input template; never put secrets here
- `scripts/validate_policy.py` - schema/safety validation without external dependencies
- `scripts/smoke_test.py` - ordinary functional checks
- `scripts/negative_security_test.py` - dry-run by default; low-volume security probes only

## Safe defaults

- geo/ASN enforcement disabled
- broad blocking disabled
- suspicious automation uses observe/challenge before block
- verified search crawlers are exempted from generic automation handling
- managed WAF is optional until the account plan/resources are confirmed
- CSP is Report-Only
- Logpush is optional and requires an operator-created destination
- all emergency lists/rules must be short-lived and documented

## Requirements

- Terraform >= 1.6
- Cloudflare provider ~> 4.40 to remain consistent with existing repository Cloudflare IaC
- Python >= 3.11 for validation/test scripts
- an edge-provider account/zone with the features required by the selected variables

## Required secret names

Never commit values.

- `CLOUDFLARE_API_TOKEN` - least privilege for the exact zone/resources being managed
- optionally `TF_VAR_logpush_ownership_challenge` if the selected log destination requires it

Repository/environment variables (non-secret where appropriate):

- `EDGE_CLOUDFLARE_ACCOUNT_ID`
- `EDGE_CLOUDFLARE_ZONE_ID`
- `EDGE_ZONE_NAME`
- `EDGE_PUBLIC_HOSTNAME`
- `EDGE_LOGPUSH_DESTINATION` (may be a secret depending on destination credentials)

## Minimum Cloudflare token permissions

Scope to one account/zone wherever possible. Typical resources require some combination of:

- Zone / Zone / Read
- Zone / Firewall Services / Edit
- Zone / Transform Rules / Edit
- Zone / Logs / Edit if Logpush is enabled
- Zone / DNS / Edit only if you intentionally extend this module to manage DNS; this reference module does not require DNS mutation

Exact permission names vary by Cloudflare API/provider version. Grant only what `terraform plan/apply` proves necessary.

## Local validation

```bash
python3 infra/edge/scripts/validate_policy.py
terraform -chdir=infra/edge fmt -check -recursive
terraform -chdir=infra/edge init -backend=false
terraform -chdir=infra/edge validate
```

## Plan

```bash
cd infra/edge
cp variables.example terraform.tfvars
# fill identifiers and reviewed, non-secret policy inputs
export CLOUDFLARE_API_TOKEN='...'
terraform init
terraform plan -var-file=terraform.tfvars -out=edge.tfplan
terraform show edge.tfplan
```

Do not apply a plan you have not reviewed.

## Apply

```bash
terraform apply edge.tfplan
```

Provider-side prerequisites, DNS and TLS configuration must already be correct. A successful Terraform apply does not prove DNS traffic is proxied through the edge.

## Rollback

Restore the last reviewed variable/policy version, plan and apply it. For an acute false positive, disable or return only the offending rule to observe/challenge. See `docs/rollback-and-recovery.md`.

## GitHub Pages constraint

The current static origin cannot validate a secret edge header or restrict source IPs. The proxy protects traffic sent to `www.clearglassinc.com`, but the Pages origin cannot be made truly private. For non-bypassable origin security, move the built static artifact to an origin supporting authenticated/private edge access.

## Provider mapping

The JSON policy is intentionally not Cloudflare expression syntax. For another provider, implement a renderer/adapter that preserves:

- rule IDs and descriptions
- scope/priority
- action and rollout mode
- exceptions
- owner/rationale
- expiry for temporary controls
- logging requirements

Do not port vendor-specific bot scores or managed-rule IDs as if they were portable semantics.

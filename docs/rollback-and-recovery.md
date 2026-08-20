# Edge Rollback and Recovery

## Principles

- Roll back the smallest changed layer first: rule, action, feature group, provider policy, then DNS.
- Prefer block/challenge to log/disabled over a broad skip or removal of the entire perimeter.
- Never combine DNS, TLS, WAF, and origin changes unless evidence proves they must move together.
- Preserve event logs, remote-state versions, plan digest/output, policy/config version, commit SHA, workflow run, operator, and ticket.
- A repository revert changes code only. Provider state changes only after an authorized apply.

## Normal rule rollback

1. Identify the matching rule ID and deployed configuration commit.
2. Change only its action/feature in `infra/edge/environments/<environment>.tfvars.json` or the relevant rule definition.
3. Return uncertain behavior to `log`; use `disabled` if the provider plan lacks nonterminating log.
4. Open a protected PR with false-positive evidence and a regression test.
5. Dispatch a plan, review the remote-state diff/digest, approve the protected apply, and smoke test.
6. Confirm event export and unrelated managed WAF coverage remain.

Do not add a broad `allow` to compensate for a narrow false positive.

## Workflow configuration rollback

Choose a full 40-character known-good commit SHA reachable from `main`:

```bash
git log --oneline -- infra/edge .github/workflows/edge-security.yml
git show --stat KNOWN_GOOD_40_CHAR_SHA
```

Preferred workflow dispatch:

```bash
gh workflow run edge-security.yml \
  --ref main \
  -f operation=rollback \
  -f environment=production \
  -f config_ref=KNOWN_GOOD_40_CHAR_SHA \
  -f change_ticket=INCIDENT_OR_CHANGE_ID \
  -f base_url=https://www.clearglassinc.com \
  -f emergency_mode=false \
  -f execute_negative_tests=false \
  -f expect_enforcement=false
```

The guard verifies ancestry, creates a locked remote-state plan at the old commit, and requires the protected apply environment. Review the plan artifact before approval. The apply rebuilds inputs and refuses a different plan digest.

After stabilization, create a normal revert/correction PR so `main` again matches provider intent:

```bash
git revert BAD_EDGE_COMMIT
```

Do not push directly to protected `main`.

## Authorized local recovery

Use only if GitHub Actions is unavailable and the operator is authorized. Never store credentials/backend config in the repository.

```bash
terraform -chdir=infra/edge init \
  -reconfigure \
  -input=false \
  -backend-config=/secure/path/edge-backend.hcl
terraform -chdir=infra/edge validate
terraform -chdir=infra/edge plan \
  -input=false \
  -lock-timeout=5m \
  -var-file=environments/production.tfvars.json \
  -var-file=/secure/path/edge-runtime.tfvars.json \
  -out=/secure/path/edge-rollback.tfplan
terraform -chdir=infra/edge show -no-color /secure/path/edge-rollback.tfplan
terraform -chdir=infra/edge apply \
  -input=false \
  -lock-timeout=5m \
  /secure/path/edge-rollback.tfplan
```

Review the plan and remote-state target before apply. Do not use `terraform destroy`, force-unlock without proving a stale lock, or an ephemeral local state.

## Emergency provider-dashboard recovery

If the provider API/CI control plane is unavailable but the data plane works, an authorized operator may:

1. disable the specific offending rule/rate/header transform
2. disable expired emergency mode
3. restore a known-good provider rule version
4. record exact before/after values, operator, UTC time, ticket, and expiry
5. preserve provider audit/security logs
6. run a refresh/plan and codify or revert drift before the next apply

Do not create a broad allow, disable managed DDoS, or erase evidence.

## DNS rollback

Use the recorded pre-cutover zone snapshot and `docs/dns-cutover-runbook.md`. For Pages, the likely bypass is the correct existing Pages web target changed from proxied to DNS-only. This restores direct availability but removes edge DDoS, WAF, bot, rate, header, cache, and centralized logging controls.

Never improvise an origin target, alter mail, delete the zone, or change nameservers/DNSSEC as a first response.

## TLS recovery

- Visitor-to-edge failure: check DNS, edge certificate/hostname, CAA, issuance, redirect, and protocol settings.
- Edge-to-origin failure: check Pages certificate/custom-domain state, origin hostname/SNI, chain, and strict validation.
- Roll back the recent TLS/DNS change; never make insecure origin TLS permanent.
- Reintroduce redirect, strict origin validation, HSTS, includeSubDomains, and preload only in that safe order with validation at each step.

## Static Pages recovery

Pages artifact recovery remains Git/Pages based and should follow branch protection:

```bash
git revert BAD_SITE_COMMIT
python3 tools/build_pages.py /tmp/clearglass-pages-recovery
```

Open/merge the revert PR, wait for the Pages workflow, validate the public artifact, and purge only affected cached URLs if the edge retained broken HTML.

## Dynamic-origin recovery

- isolate the compromised/unhealthy origin
- fail over only to a preconfigured trusted origin
- preserve application auth/signature/rate controls
- rotate mTLS/origin-header credentials after compromise
- verify direct ingress denial and edge-authenticated health before reopening
- purge sensitive cached responses after any cache-control mistake
- validate CORS, auth, admin, forms, API, and signed webhooks

## Recovery verification

```bash
python3 infra/edge/scripts/validate_policy.py
python3 infra/edge/scripts/validate_terraform_safety.py
python3 tests/test_edge_security_policy.py -v
python3 infra/edge/scripts/smoke_test.py \
  --base-url https://www.clearglassinc.com \
  --require-edge
python3 infra/edge/scripts/negative_security_test.py \
  --base-url https://www.clearglassinc.com \
  --dry-run
```

Then verify event ingestion, action/rule dashboards, origin error/latency, cache status, certificate/DNS health, configuration drift, representative users, verified crawlers, monitoring, forms, CORS, APIs, auth, and webhooks.

# DNS / Edge Cutover Runbook

No DNS, nameserver, certificate, Pages setting, or provider proxy change is performed by repository automation. An authorized operator must execute and record this runbook.

## Required operator values

- change ticket and cutover/rollback decision owners
- zone and registrar owners
- public hostname
- exact current Pages DNS target and GitHub Pages custom-domain status
- current and proposed records, TTLs, nameservers, DNSSEC/DS, and CAA state
- current and proposed visitor/origin TLS modes
- staging and production edge-policy versions/commit SHAs
- log/alert destination and on-call channel
- rollback deadline and prior DNS snapshot location

## Pre-cutover checklist

- [ ] Export the complete zone and record registrar nameservers, DS records, TTLs, CAA, and current resolver answers.
- [ ] Preserve MX, SPF, DKIM, DMARC, verification, and non-HTTP records exactly.
- [ ] Confirm the root `CNAME`, repository Pages settings, and actual Pages target agree.
- [ ] Confirm GitHub Pages serves the intended artifact and its custom-domain certificate is healthy.
- [ ] Confirm the edge zone/account/plan, certificate, state owner, and least-privilege tokens.
- [ ] Confirm remote state encryption, versioning, locking, backup/recovery, and clean Terraform plan.
- [ ] Confirm no second Terraform state owns the same Cloudflare ruleset phases.
- [ ] Apply logging first and verify security events reach the approved destination without sensitive fields.
- [ ] Keep custom WAF, managed WAF, rate limits, and reputation in log/observe mode.
- [ ] Keep geo/ASN disabled and emergency mode off.
- [ ] Confirm verified crawler and monitoring/internal automation behavior on staging.
- [ ] Build the exact Pages artifact and pass CSP inventory audit.
- [ ] Complete browser, asset, form, API/CORS, crawler, challenge, header, cache, and low-volume negative tests on staging.
- [ ] Confirm API/admin origins, if any, reject direct ingress and validate edge identity.
- [ ] Confirm dashboard/alert ownership, incident channel, rollback authority, and provider outage risk acceptance.
- [ ] Lower only the web-record TTL in advance if operationally useful.

Pre-cutover validation:

```bash
python3 infra/edge/scripts/validate_policy.py
python3 infra/edge/scripts/validate_terraform_safety.py
python3 tests/test_edge_security_policy.py -v
python3 tools/build_pages.py /tmp/clearglass-pages-edge-audit
python3 infra/edge/scripts/audit_csp_sources.py --root /tmp/clearglass-pages-edge-audit --check
python3 infra/edge/scripts/smoke_test.py --base-url https://STAGING_HOSTNAME
python3 infra/edge/scripts/negative_security_test.py --base-url https://STAGING_HOSTNAME --dry-run
```

## Cutover checklist

1. Announce the change window and freeze unrelated DNS/TLS/WAF mutations.
2. Confirm the provider zone is active and the edge certificate covers the public hostname.
3. Reconfirm the web record points to the exact Pages target prescribed by GitHub.
4. Change only the public web record to proxied/edge-enabled status.
5. Do not change the repository `CNAME` unless the public hostname itself is intentionally changing.
6. Do not point API/admin hostnames to Pages; route them only to their reviewed origins.
7. Keep uncertain rules in log or managed-challenge mode.
8. Verify HTTP redirects to HTTPS without a loop.
9. Verify the visitor certificate hostname, issuer/chain, validity, and modern TLS negotiation.
10. Verify edge-to-Pages TLS with origin certificate validation; do not disable validation to conceal a mismatch.
11. Verify HTML, CSS, JavaScript, images, fonts, forms, frames, analytics, and client-side API calls.
12. Verify edge headers, cache status, WAF events, challenge telemetry, and origin metrics.
13. Ask the rollback owner for an explicit continue/rollback decision before the window closes.

## Post-cutover automated checks

```bash
curl -fsSIL http://www.clearglassinc.com/
curl -fsSIL https://www.clearglassinc.com/
python3 infra/edge/scripts/smoke_test.py \
  --base-url https://www.clearglassinc.com \
  --require-edge
python3 infra/edge/scripts/negative_security_test.py \
  --base-url https://www.clearglassinc.com \
  --dry-run
```

Run bounded negative tests only after the target is explicitly approved and only with the script's safe maximums:

```bash
python3 infra/edge/scripts/negative_security_test.py \
  --base-url https://STAGING_HOSTNAME \
  --execute \
  --rate-probe-count 10
```

Do not use `--expect-enforcement` until the corresponding rules have been deliberately promoted. Never run a DDoS, brute-force, credential-stuffing, uncontrolled scan, or destructive payload test.

## Post-cutover manual checks

- [ ] representative homepage, internal pages, and legal pages load
- [ ] static assets return correct content types and no mixed content
- [ ] cache miss/hit behavior matches `cache-policy.example.json`
- [ ] untrusted forwarding headers do not poison a subsequent clean response
- [ ] supported FormSubmit/Formspree behavior is confirmed by the owner
- [ ] required public data APIs, embeds, fonts, and optional analytics still work
- [ ] API CORS preflight and normal requests work without exposing unauthorized origins
- [ ] valid signed webhooks are never presented with a browser challenge
- [ ] provider-verified crawlers and approved monitoring remain functional
- [ ] normal users do not show an unexpected 403/429 or challenge-failure spike
- [ ] CSP Report-Only events are reviewed; the edge has not added an enforcing CSP
- [ ] HSTS scope does not include unverified subdomains and preload remains off
- [ ] edge logs exclude cookies, authorization, passwords, bodies, and sensitive query values
- [ ] origin errors/latency and cache ratio remain within the recorded baseline
- [ ] security events include rule/action/policy version and alerts are delivered
- [ ] Pages direct-origin exposure is recorded as residual risk, or private-origin denial is proven for a migrated origin

## DNS propagation validation

Use multiple resolvers and at least two networks/vantage points. Do not treat one cached answer as global propagation.

```bash
dig +short www.clearglassinc.com A
dig +short www.clearglassinc.com AAAA
dig +trace www.clearglassinc.com
nslookup www.clearglassinc.com 1.1.1.1
nslookup www.clearglassinc.com 8.8.8.8
```

Also verify nameservers, DNSSEC validation, CAA, certificate transparency/issuance, and the provider dashboard's DNS/certificate health.

## Rollback triggers

Rollback if a narrow rule disable cannot promptly correct:

- visitor or origin certificate/handshake failure
- redirect loops or inconsistent DNS answers
- broken primary navigation or assets
- material form/API/auth/webhook/CORS regression
- broad legitimate 403/429/challenge impact
- origin errors/latency materially above baseline
- security-log leakage of sensitive fields
- provider routing outage expected to exceed the accepted recovery objective

## DNS/proxy rollback

1. Announce rollback and preserve edge event/config evidence.
2. Return the offending WAF/rate/header rule to observe first if the edge data plane is healthy.
3. If the proxy itself must be bypassed, restore the exact recorded web record/target/proxy state. For Pages this is normally the same correct Pages target changed to DNS-only.
4. Do not alter mail, unrelated records, nameservers, DNSSEC, or delete the provider zone as a first response.
5. Confirm the Pages custom domain and certificate remain valid.
6. Validate direct HTML/assets/forms and HTTPS from multiple networks.
7. Record the time, operator, DNS before/after values, edge policy version, reason, and resulting loss of WAF/CDN protection.
8. Restore normal TTL only after stability.
9. Reconcile manual provider drift and open a corrective PR before another apply.

DNS rollback restores availability by bypassing the perimeter; it does not preserve edge DDoS, WAF, bot, rate, header, or logging protections. The incident commander must explicitly accept that tradeoff.

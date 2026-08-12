# Edge Incident Response Runbooks

These runbooks cover the managed edge/CDN/WAF layer. Assign an incident commander, preserve UTC evidence, make one reversible change at a time, and record every dashboard mutation for Terraform reconciliation.

## 1. Suspected DDoS attack

- **Detection:** provider DDoS alert; abrupt request/connection surge; origin saturation; rising edge/origin 5xx or latency; cache-ratio collapse.
- **Immediate containment:** confirm provider-managed mitigation is active; cache only demonstrably safe static objects; tighten the attacked route, not the whole site; activate time-bounded emergency managed challenge if normal controls are insufficient; protect API/admin independently.
- **Verification:** edge absorbs the surge, origin load/latency recover, legitimate success rate remains acceptable, and challenge success/failure is not showing broad user impact.
- **Recovery:** remove temporary controls in reverse order, restore reviewed thresholds, purge only necessary objects, and retain attack/event timelines.
- **Post-incident review:** attack vectors, provider response, origin bottlenecks, cache effectiveness, thresholds, capacity, detection/alert timing, and secondary-provider needs.

## 2. Credential stuffing

- **Detection:** distributed login failures, password-reset surge, repeated accounts across sources, impossible velocity, breached-credential or bot/reputation signals.
- **Immediate containment:** apply login/reset route limits; managed-challenge suspicious browser automation; enable application account/device/risk controls and MFA; block only confirmed malicious indicators; do not challenge signed webhooks or trusted monitors.
- **Verification:** abusive attempts and account compromise indicators decline while valid login/reset flows and support access continue.
- **Recovery:** expire temporary IP/risk rules; keep sustainable app/edge limits; rotate/reset credentials only for affected accounts based on evidence.
- **Post-incident review:** affected accounts, data exposure, MFA coverage, breached-password detection, response enumeration, session revocation, false positives, and notification obligations.

## 3. Malicious scraping

- **Detection:** high-volume sequential crawling, low content diversity, headless fingerprints, datacenter ASN concentration, challenge failures, or unusual expensive-route/cache behavior.
- **Immediate containment:** rate-limit expensive route classes; managed-challenge corroborated automation; temporary quarantine confirmed sources with expiry; preserve verified crawler and approved monitoring treatment.
- **Verification:** scraper throughput/origin cost declines without search indexing, accessibility, customer, partner, or monitoring regression.
- **Recovery:** remove temporary lists, retain measured route limits, and restore ordinary challenge sensitivity.
- **Post-incident review:** exposed content/value, API/data minimization, pagination/export limits, cache strategy, bot telemetry quality, and legal/business handling.

## 4. WAF false positive

- **Detection:** support report, legitimate 403/challenge, conversion drop, high challenge solve rate, or a known-good request matching one rule ID.
- **Immediate containment:** return only that rule/managed signature to log or add the narrowest route/source exception; keep unrelated managed WAF coverage active.
- **Verification:** reproduce the formerly blocked request, confirm adjacent legitimate flows, and confirm attack test cases still generate the expected event/action.
- **Recovery:** tune expression/threshold/managed override, stage observe then challenge, assign exception owner/expiry, and apply through reviewed IaC.
- **Post-incident review:** add the request as a regression case, quantify impact/detection delay, improve promotion criteria, and reconcile dashboard drift.

## 5. Accidental blocking of legitimate users

- **Detection:** geographic/ASN/customer cluster reports, abrupt regional traffic loss, 403/429 increase, or elevated challenge failures after a change.
- **Immediate containment:** disable the narrow geo/ASN/IP/rate/emergency rule first; use challenge/log instead of deny for uncertain signals; keep exploit inspection active.
- **Verification:** representative affected networks/users regain access and unaffected protections/logging remain operational.
- **Recovery:** correct lists/exceptions/thresholds in code, expire temporary workarounds, approve and apply the corrected plan.
- **Post-incident review:** signal source, list provenance, testing gap, customer impact, approval quality, and whether synthetic regional monitoring is needed.

## 6. Origin compromise

- **Detection:** unexpected content, unauthorized deployment/config, integrity/provenance failure, origin audit events, credential misuse, or suspicious direct-origin traffic.
- **Immediate containment:** freeze deploys; revoke compromised credentials; isolate dynamic origin; use a trusted maintenance/static response at the edge if available; preserve disk/cloud/CI evidence. A WAF is not remediation.
- **Verification:** compromised ingress and credentials are unusable, trusted artifact hashes/provenance are established, and edge/origin routes point only to known-good infrastructure.
- **Recovery:** rebuild from a trusted commit, rotate provider/state/origin/app secrets, repair origin ACL/mTLS/header controls, purge affected cache, and restore traffic gradually.
- **Post-incident review:** root cause, dwell time, direct-origin path, CI/supply-chain integrity, data/customer impact, credential inventory, and migration from Pages if origin privacy is required.

## 7. Provider outage

- **Detection:** provider status and telemetry plus multi-vantage DNS/TLS/HTTP failures while the origin and authoritative dependencies are independently healthy.
- **Immediate containment:** pause provider mutations; determine control-plane versus data-plane scope; if prolonged and risk-approved, execute the recorded DNS-only rollback to the exact known origin.
- **Verification:** external resolvers, certificates, HTML/assets, forms/APIs, and origin health succeed; communicate that bypass removes WAF/CDN protections.
- **Recovery:** return to proxy only after provider stability, edge certificate, policies, logs, and smoke tests are healthy; re-enable gradually.
- **Post-incident review:** RTO/RPO, secondary provider/traffic manager, DNS TTL, monitoring blind spots, support response, and bypass exposure.

## 8. Emergency lockdown

- **Detection:** active exploit or abuse overwhelms normal rule/route controls and has a clear affected scope.
- **Immediate containment:** dispatch emergency plan/apply with incident ticket and expiry within 24 hours; managed-challenge uncertain traffic; narrow by host/route/region/ASN; block only confirmed abuse; preserve verified/trusted/webhook traffic.
- **Verification:** attack success/origin impact declines, critical customer/API/admin paths remain usable, and the emergency rule description shows owner/ticket/expiry.
- **Recovery:** return the temporary policy to disabled before expiry or immediately after containment; restore the staged baseline and reconcile manual changes.
- **Post-incident review:** authorization, scope, duration, false positives, controls that should become normal policy, and proof that no emergency rule remains.

## 9. DNS rollback

- **Detection:** persistent proxy routing, certificate, DNSSEC, resolution, primary-content, or provider outage failure that a narrow policy rollback does not fix.
- **Immediate containment:** preserve the zone snapshot/events; restore only the web record's exact prior target/proxy state; do not alter mail, unrelated records, nameservers, or delete the zone.
- **Verification:** multiple resolvers/networks reach the correct Pages/origin content over valid HTTPS and critical flows succeed.
- **Recovery:** stabilize TTL, correct the edge problem in staging, then recut only after provider/certificate/policy readiness is re-established.
- **Post-incident review:** before/after DNS values, operator/timestamps, propagation, lost perimeter controls, customer impact, and runbook accuracy. Follow `docs/dns-cutover-runbook.md`.

## 10. Certificate or TLS failure

- **Detection:** browser/curl errors, expiry/issuance alert, hostname mismatch, edge-origin handshake/SNI failure, or redirect loop.
- **Immediate containment:** identify visitor-to-edge versus edge-to-origin; roll back the recent TLS/DNS change; never disable certificate validation as a shortcut.
- **Verification:** hostname, chain, validity, modern protocols, redirect behavior, origin SNI, OCSP/revocation expectations, and multiple-vantage HTTPS checks pass.
- **Recovery:** renew/reissue through the provider/GitHub process, restore strict origin validation, and re-enable proxy/redirect/HSTS only in safe order.
- **Post-incident review:** renewal ownership, alerts, CAA/DNS validation, HSTS impact, certificate inventory, and expiry lead time.

## 11. Revert a bad WAF policy

- **Detection:** policy-version-correlated availability/conversion/API regression, unexpected action volume, changed Terraform plan, or confirmed unsafe rule behavior.
- **Immediate containment:** set the offending rule/action to log/disabled or dispatch rollback to a full known-good commit reachable from `main`; do not destroy the whole perimeter.
- **Verification:** recomputed reviewed plan matches, apply audit evidence is present, smoke/security-header checks pass, and security-event delivery continues.
- **Recovery:** open a corrective PR, add a regression test, remove provider dashboard drift, and re-stage any future promotion.
- **Post-incident review:** review/CI gap, plan evidence, operator/ticket/timestamps, affected traffic, rollback time, and branch/environment protection.

## 12. Rotate credentials and allow lists

- **Detection:** suspected exposure, personnel/provider change, origin compromise, stale CIDR ownership, periodic access review, or provider token expiry.
- **Immediate containment:** revoke compromised tokens; remove no-longer-trusted entries; issue separate least-privilege plan/apply credentials; rotate origin identity at edge and origin without opening direct ingress.
- **Verification:** new credentials can perform only intended plan/apply operations, old credentials fail, backend locking works, origin rejects the old identity, and approved integrations still function.
- **Recovery:** update protected secret metadata, owners, expiry/review dates, and IaC list entries; reconcile state without printing or committing values.
- **Post-incident review:** access grants, token scope, usage audit, rotation overlap, stale allow-list sources, automation opportunities, and evidence retention.

## Post-incident minimum record

- incident/change ID, UTC timeline, severity, commander, and operators
- policy version, configuration commit, plan digest, workflow run, and provider audit IDs
- affected host/routes, geography/ASN, edge actions/rule IDs, and origin impact
- temporary rules/lists with owner and expiry
- DNS/TLS/provider changes and before/after values
- evidence location and privacy/retention handling
- customer/security/data impact and notifications
- root cause, corrective actions, owners, and due dates

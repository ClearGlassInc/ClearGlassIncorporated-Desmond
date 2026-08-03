# ClearGlassInc Artemis Website Security and Privacy Assurance Plan

**Status:** implemented controls and deployment requirements, not a certification  
**System assessed:** public GitHub Pages site and repository-hosted application sources  
**Assessment date:** 2026-08-03  
**Owner to confirm:** `[SECURITY_OWNER]`

This document distinguishes controls present in this repository from controls that require
hosting, identity-provider, Palantir, CDN, or legal authority. Target-state documents and code
skeletons are not evidence that a service is deployed.

## 1. Prioritized threat model

### Assets and trust boundaries

Assets include brand and copyrighted content, policy records, source and release artifacts,
visitor contact data, commerce/customer records in separately deployed services, administrator
identities, API credentials, agent prompts, ontology data, audit evidence, and backups. Boundaries
exist between browsers and the public CDN; GitHub Actions and pull-request code; GitHub Pages and
independent backends; backend services and identity/data/model providers; and operator approval
and consequential action execution.

| Rank | Threat / abuse case | Likelihood | Impact | Repository control | Residual treatment |
|---:|---|---|---|---|---|
| 1 | Secret, source map, internal file, or unpublished content included in the Pages artifact | Medium | Critical | Pages excludes Git metadata/workflows; security CI scans secrets and production artifacts | Add host-side egress allowlist; rotate any exposed credential immediately |
| 2 | Authorization bypass or AI/tool action crosses tenant, compartment, or approval boundary | Medium | Critical | Commerce governance remains analysis → draft → approval → execution; design requires server-side deny-by-default policy | Requires IdP MFA, entity-level policy tests, Palantir enrollment, and independent review |
| 3 | Supply-chain compromise in Actions or dependencies | Medium | High | Read-only default permissions, SHA-pinned actions, checkout credential persistence disabled, dependency/secret/workflow checks | Enable GitHub dependency graph, branch protection, signed releases, and protected environments |
| 4 | Script/content injection or clickjacking | Medium | High | CSP, `frame-ancestors`, MIME sniffing prevention, referrer and cross-origin headers | Current static pages need inline script/style allowances; migrate incrementally to hashes/nonces at an edge capable of nonce injection |
| 5 | Bulk scraping, content resale, model training, or account sharing | High | Medium–High | Express licence restrictions, page-specific watermark metadata, provenance hashes | Public content remains copyable; CDN rate limits and authenticated premium delivery require hosting access |
| 6 | Personal information overcollection, indefinite retention, or leakage through logs | Medium | High | Data-minimization and retention template; no fingerprinting added; static watermark token is random and session-only | Complete data inventory/DPIA and configure deletion jobs with evidence |
| 7 | Credential stuffing, enumeration, token replay, or automated download | Medium | High | Backend requirements specify MFA, rotating sessions, short-lived audience-bound tokens, quotas, sanitized events | Configure IdP/CDN/API gateway and alert destinations; test without invasive fingerprinting |
| 8 | Malicious upload, webhook forgery, or SSRF | Medium | High | Existing commerce webhook signature/idempotency controls are preserved; blueprint mandates type/size validation and egress allowlists | Validate each independently deployed backend and object store before enablement |
| 9 | Evidence deletion or unreviewed self-improvement | Low–Medium | Critical | Append-only audit and human approval invariant; model output cannot approve its own change | Use externally retained, tamper-evident logs and two-person release approval |
| 10 | Screenshot/photography/casual copying | High | Medium | Visible copyright, unobtrusive opt-in page watermark, export watermark requirement | A public webpage cannot prevent screenshots, photography, copying, or determined extraction; do not promise DRM |

Abuse responses must be proportionate and reversible: record a sanitized event, throttle, present
an accessible challenge, temporarily block a narrow source/account, then alert a human. No hacking
back, destructive retaliation, device interference, covert tracking, or manufactured authority.

## 2. Completed repository protections

- `_headers` defines CSP and HSTS plus permissions, referrer, content-type, framing, and
  cross-origin policy. This file is effective only on hosts that honor Netlify-style headers;
  GitHub Pages does **not** guarantee that it will.
- `asset-protection.js` publishes copyright, licence, provenance, and opt-in page watermark
  metadata. It deliberately does not block keyboard shortcuts or text selection. Client-side
  deterrence is not authorization or DRM.
- `.well-known/security.txt` provides RFC 9116-style contacts and a responsible-disclosure route.
- `tools/security_release_manifest.py` creates a deterministic SHA-256 inventory of important
  public policies and controls; CI verifies it is current.
- Existing governed commerce approval and audit controls remain unchanged.

## 3. Security header deployment

The committed CSP is a compatibility baseline. It uses `'unsafe-inline'` because many legacy pages
contain inline scripts and styles. It materially limits object, base, framing, form, and connection
destinations, but it is not the requested strict nonce/hash end state.

At the production CDN or reverse proxy:

1. Deploy the baseline as `Content-Security-Policy-Report-Only`; collect sanitized violation
   samples for at least one normal traffic cycle.
2. Inventory every required script/style origin. Remove unused third-party dependencies.
3. Extract inline code or generate a fresh cryptographic nonce per response. Never use a static
   nonce. Remove `'unsafe-inline'`, then enforce the policy.
4. Preserve search-crawler access to public HTML. Challenge only abusive behavior; make challenges
   keyboard/screen-reader operable and provide a support bypass.
5. Verify HSTS on every subdomain before requesting/retaining preload status.

Sensitive API responses must additionally send `Cache-Control: no-store, private`, `Pragma:
no-cache`, and `Vary: Authorization, Cookie`. Public Pages content must never contain sensitive
records.

## 4. Server-side protected-resource contract

Static GitHub Pages cannot safely implement accounts, signed URLs, RBAC, MFA, CSRF, protected
downloads, dynamic user watermarks, WAF enforcement, database queries, or log retention. Implement
these at an independently deployed backend/API gateway:

- **Environment variables:** `APP_ENV`, `OIDC_ISSUER`, `OIDC_AUDIENCE`, `OIDC_JWKS_URL`,
  `SESSION_SIGNING_KEY`, `CSRF_SIGNING_KEY`, `SIGNED_URL_HMAC_KEY`, `AUDIT_LOG_SINK`,
  `DATABASE_URL`, `REDIS_URL`, `WAF_MODE`, `RATE_LIMIT_PER_MINUTE`,
  `DOWNLOAD_TOKEN_TTL_SECONDS`, and `BACKUP_KMS_KEY_ID`. Values belong in a secret manager, never
  `.env` files committed to Git.
- Require phishing-resistant MFA for administrators. Rotate the session identifier after login,
  privilege change, recovery, and reauthentication. Cookies: `Secure`, `HttpOnly`, `SameSite=Lax`
  (or `Strict` where workflows permit), narrow `Path`, no broad `Domain`, bounded expiry.
- Authorize server-side on every object using subject, tenant, coalition, compartment, purpose,
  action, and resource. UI hiding is not authorization. Parameterize all database statements.
- Signed download tokens must bind resource, subject/account pseudonym, audience, expiry (normally
  1–5 minutes), and a single-use nonce. Reject replay atomically. Confirm authorization before
  returning bytes; never place the asset URL in unauthorized HTML.
- Render a user-specific, server-side watermark into restricted images/PDFs using a non-email
  account identifier, UTC timestamp, and document identifier. Do not put direct personal data into
  public caches, filenames, telemetry, or browser analytics.
- Uploads: authenticate, authorize, cap size/count, verify magic bytes, rename server-side, store
  outside the web root, malware scan in quarantine, disallow active formats by default, and use
  separate download origins.
- Webhooks: authenticate signatures over raw bodies, enforce timestamp windows, store idempotency
  keys, rate limit, and acknowledge only after durable validation.
- Model/agent tools use typed allowlisted calls, budgets, timeouts, output validation, scoped
  workload identity, and an immutable proposal → review → approval → deploy record. Agents cannot
  change goals, policy, privileges, or approve their own upgrades.

## 5. Privacy, legal, and retention assessment

Qualified counsel must determine actual applicability based on incorporation, visitor/customer
location, services, contracts, processing roles, and data flows. Candidate regimes include PIPEDA
and applicable Canadian provincial privacy law; CASL for commercial electronic messages; consumer
protection and competition/advertising rules; copyright and trademark law; breach record/reporting
obligations; the Accessibility for Ontarians with Disabilities Act and contractual/WCAG duties;
and, when targeting/monitoring those residents, GDPR/UK GDPR, ePrivacy rules, CCPA/CPRA and other
US state privacy laws, COPPA/age rules, and sectoral/contractual requirements. This is an issue
list—not a legal conclusion, compliance claim, or certification.

Before deploying non-essential analytics, obtain counsel-approved regional consent behavior.
Default to essential storage only. A consent manager must withhold non-essential tags until the
required opt-in, record policy/vendor/purpose/version/time without sensitive data, permit granular
withdrawal as easily as consent, and honor applicable browser signals. Do not display a cosmetic
banner while loading tags first.

The proposed schedule below requires owner and counsel approval plus automated deletion evidence:

| Data class | Default | Disposal / exception |
|---|---:|---|
| Unsubmitted form fields | Do not collect | Browser only; never log |
| Contact inquiry | 24 months after closure | Delete/anonymize; preserve only documented legal hold |
| Consent evidence | Consent lifetime + 3 years | Delete securely after disputes/statutory needs expire |
| Raw web/security access events | 30 days | Aggregate or delete; 90 days only for documented investigation |
| Authentication/audit events | 1 year | Longer only for contract, law, or active investigation |
| Client operational data | Contract schedule | Tenant deletion workflow and certificate/evidence |
| Financial/tax records | Counsel/accountant-defined statutory term | Access restricted; documented destruction |
| Backups | 35-day rolling window | Cryptographic expiry; deletions age out and are not restored silently |

Legal holds suspend only relevant deletion and must record authority, scope, custodian, start,
review, and release. Do not obstruct lawful orders or investigations.

## 6. Event logging, alerts, and evidence

Use structured events with UTC time, event type, pseudonymous subject, tenant, resource identifier,
decision, policy/version, correlation ID, source class, and result. Redact credentials, cookies,
tokens, request bodies, personal content, query strings, and sensitive model context. Hash-chain or
WORM-retain material audit events outside the application account.

Initial alert candidates (tune using measured baselines): 10 failed logins/account/10 minutes; 50
resource misses/account/5 minutes; 3 signed-token replays/10 minutes; download volume above an
approved tier quota; any administrator MFA bypass, policy fail-open, audit sink failure, secret
exposure, or cross-tenant denial. Audit failures must fail closed for consequential actions.

## 7. Incident response and key revocation

1. **Declare and preserve:** name commander/scribe, start an append-only timeline, preserve logs,
   affected artifacts and hashes under access-controlled legal-hold procedure.
2. **Contain:** disable affected route/account/release; revoke sessions and scoped credentials;
   block narrow indicators without destructive retaliation.
3. **Eradicate:** fix root cause, scan dependencies and history, rotate secrets from a clean
   workstation in dependency order (root identity/KMS → workload identity → applications).
4. **Assess notification:** privacy officer and qualified counsel determine record, regulator,
   individual, contractual, insurer, and law-enforcement duties. Do not conceal or overstate.
5. **Recover:** restore a verified immutable artifact/backup, validate authorization and audit
   paths, monitor an approved observation window, and retain evidence.
6. **Learn:** blameless review, tracked corrective actions, control/eval regression tests, and
   explicit closure owner.

Quarterly restore exercises must record backup digest, isolated target, RPO/RTO result, data and
authorization integrity checks, operator, and cleanup. Annual tabletop exercises should cover
credential compromise, privacy breach, dependency compromise, and unavailable audit storage.

## 8. Deployment, verification, and rollback

### Deployment gates

1. Counsel approves bracketed policy fields and actual data/consent representations.
2. Security owner reviews the CSP report and CDN/WAF rules; accessibility owner tests challenges.
3. Generate provenance: `python3 tools/security_release_manifest.py`.
4. Run tests/scans/builds and review the Pages artifact for secrets, source maps, `.env`, backups,
   databases, internal docs, and VCS metadata.
5. Require protected-environment approval and deploy the immutable artifact. Record commit, actor,
   workflow/ref, run URL, artifact digest, environment decision, and rollback owner.
6. Verify the live canonical host, redirect/HTTPS, headers, policy pages, `security.txt`, broken
   links, console/CSP errors, keyboard navigation, screen-reader landmarks, responsive rendering,
   search-crawler access, and that protected API responses never cache.

### Rollback

Re-deploy the last known-good Pages artifact/commit; revert the header/CDN policy independently if
it blocks legitimate functionality; revoke newly introduced keys/tokens; preserve the failed
artifact and logs; and re-run live verification. Do not roll back a security control without a
documented compensating control and owner.

## 9. Residual risk and external actions

| Owner | Required action / limitation |
|---|---|
| Legal/privacy counsel | Confirm entity/contact placeholders, governing terms, consumer clauses, accessibility statement, consent basis, retention periods, cross-border terms, copyright/takedown process, and jurisdiction-specific rights |
| GitHub administrator | Enable branch/ruleset review, private vulnerability reporting, dependency graph/Dependabot, secret scanning/push protection, signed releases, CODEOWNERS, and protected Pages environment; evidence not available locally |
| DNS/CDN owner | Enforce HTTPS/headers, strict nonce/hash CSP, accessible bot management, WAF/rate rules, origin protection, logs, and rollback; `_headers` alone may be inert on GitHub Pages |
| Identity owner | Configure admin MFA, recovery controls, short sessions, workload identity, RBAC/ABAC, access reviews, and break-glass evidence |
| Backend/data owner | Implement signed URLs, authorization, CSRF, quotas, replay protection, encrypted backups, deletion jobs, log sanitation, and restore tests |
| Palantir owner | Confirm Gotham/Foundry/AIP/Apollo availability and configure markings, ontology permissions, action approvals, model/prompt governance, release rings, and rollback; no provisioning is claimed here |
| Security operations | Provide SIEM/WORM retention, on-call routing, threshold tuning, incident exercises, DAST against an authorized staging target, and post-release monitoring |

No technical control creates legal immunity or absolute prevention. Public content can be recorded;
watermarks, copyright metadata, contractual restrictions, rate controls, and evidence improve
deterrence and response rather than making extraction impossible.

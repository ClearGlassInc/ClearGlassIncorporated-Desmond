# WAF Policy Reference

Provider-neutral source of truth: `infra/edge/policies/baseline.json`, validated against `infra/edge/policy.schema.json`. Cloudflare mapping: `infra/edge/*.tf`. Both committed environments disable all provider mutations and retain log-only actions.

## Rule record

Every neutral rule carries:

- stable identifier, description, category, match intent, and scope
- priority, enabled state, action, rollout mode, and log level
- exception list and optional threshold
- expiry, owner, rationale, and change ticket

The validator rejects unknown fields, missing route classes, duplicate IDs/priorities, enabled broad allow/block rules, default geo enforcement, sensitive logging, permanent reputation-only blocks, indefinite bot/emergency blocks, enabled disabled-rollout templates, and terminal actions without review metadata.

## Rollout semantics

| Neutral state | Provider behavior | Promotion requirement |
|---|---|---|
| `disabled` | No provider resource/rule | Phase ownership and plan support confirmed |
| `observe` | Log/nonterminating override where supported | Event delivery and baseline measured |
| `challenge` | Managed challenge for uncertain browser traffic | False-positive and challenge-success review |
| `enforce` | Rate limit/block only reviewed high-confidence behavior | Owner, ticket, telemetry, tests, rollback |

If the selected plan cannot log a rule nonterminatingly, leave that rule disabled or use a narrow staging-only managed challenge. Do not silently turn an intended observation rule into block.

## WAF detection coverage

| Threat category | Implementation | Initial treatment |
|---|---|---|
| SQL injection | Provider managed + OWASP rulesets | managed override `log` |
| XSS | Provider managed + OWASP rulesets | managed override `log` |
| local/remote file inclusion | Provider managed signatures | `log`, then high-confidence block |
| command injection | Provider managed signatures | `log`, then high-confidence block |
| path traversal | Managed rules plus `../`, encoded traversal, secret-file and common admin-probe paths | `log`, then challenge |
| protocol anomalies/malformed requests | Provider managed rules; provider L7 protections | observe/challenge by confidence |
| known exploit signatures | Provider managed rules | block only validated high-confidence signatures |
| scanner/probing | Path probes plus `sqlmap`, `nikto`, `nuclei`, `masscan` and scripted-agent signals | `log`, then challenge/rate limit |
| unexpected methods | Public static hostname accepts GET/HEAD/OPTIONS | `log`; dynamic routes keep route methods |
| oversized URL/query/header | 16 KiB URI, 8 KiB query, 8 KiB individual header, truncated-header signal | `log`, tune from real traffic |
| oversized body | Optional plan-specific 1 MiB/truncation rule | disabled until plan/route review |

The suspicious-user-agent rule does not assert that `curl`, headless Chrome, Python, Go, or an empty user agent is malicious. It is an observe/challenge signal, excludes verified bots and trusted operations, and is never a blanket non-browser deny.

## Bot decision model

| Class | Identification | Baseline action |
|---|---|---|
| Provider-verified crawler | Native verified-bot identity | allowed within bot layer; managed WAF retained |
| Approved monitoring | Explicit reviewed CIDR | exempt generic bot/rate challenges; managed WAF retained |
| Internal automation | Explicit controlled CIDR | same narrow exemption |
| Normal browser | No adverse corroborating signal | allow/log normal telemetry |
| Headless/automation | UA/fingerprint/behavior/bot score | log or managed challenge |
| Suspicious automation | Low bot score plus behavior/reputation | managed challenge, route rate limit |
| Credential stuffing | Login velocity plus account/app signals | login rate limit, challenge, application controls |
| High-volume scraping | Route velocity, traversal pattern, headless/reputation signals | rate limit/challenge, temporary quarantine |
| Repeated challenge failure | Provider challenge telemetry | short-lived escalation template after review |

Actions supported by the neutral model are allow, log, managed challenge, interactive challenge, rate limit, and block. Interactive challenge is not used for APIs, webhooks, monitoring, or internal automation. Zone-wide bot mode remains disabled by default because it can affect non-browser clients.

## IP reputation and lists

- `trusted_*`: explicit minimal CIDRs with owner/review record; never a broad managed-WAF bypass.
- `monitoring_*` and `internal_automation_*`: separate narrow exemptions for generic bot/rate handling.
- `deny_*`: confirmed abusive CIDRs only, not an unverified feed entry.
- `quarantine_*`: managed challenge plus future `quarantine_expires_at`.
- provider threat score: optional log/managed challenge; `block` is not a valid configuration.
- anonymous proxy/VPN and Tor: optional pre-existing provider IP lists, off by default, log/challenge only.
- trusted ASN/country exceptions: evaluated before explicitly enabled geo/ASN actions.

Named IP-list creation, feed quality, expiry, and stewardship remain provider-side/operator responsibilities.

## Rate limits

Thresholds are deliberately generous starting points and all committed actions are `log`:

| Route class | Match | Default threshold | Notes |
|---|---|---:|---|
| static assets | public GET/HEAD with static extension | 600/min | verified bots/trusted operations exempt |
| HTML/documents | remaining public GET/HEAD | 120/min | tune from legitimate navigation |
| login/auth | API `/login`, `/api/login*`, `/api/auth/*`; POST/PUT | 20/min | application account/risk controls remain |
| password reset | API path containing reset; POST/PUT | 8/10 min | avoid account-discovery responses |
| search | API `/search`/`/api/search*`; GET/POST | 60/min | consider cost-weighted app quota |
| contact/form | API `/contact`/`/api/contact*`; POST | 10/10 min | third-party static forms are separately governed |
| API | other `/api/*` | 120/min | excludes sensitive route classes/webhooks |
| admin | configured admin hostname | 60/min | pair with strong auth and optional approved geo/ASN |
| webhook | `/webhooks*` or `/api/webhook*`; POST | 300/min | default `log`; managed browser challenge is forbidden |

The default characteristic is source IP plus provider colocation. `rate_limit_characteristics` is a per-route map so supported providers/plans can key by session/token, authenticated identity, route, method, country, ASN, bot score, or reputation. Edge expressions cannot safely trust a client-supplied identity header unless the origin/edge authentication design makes it authoritative.

When provider rate-limit storage/data plane is unavailable, retain the last successful policy and application-side authentication, authorization, account-risk, signature, and local route limits. Control-plane failure blocks a new apply; it does not install a broad allow or default-deny rule.

## Geographic and ASN policy

All geo/ASN features and lists are disabled/empty by default. When explicitly enabled:

- denied countries/confirmed-abuse ASNs block only after exception/trusted evaluation
- challenge countries/ASNs use managed challenge
- allowed-country boundaries affect configured API/admin hostnames only and challenge outside traffic; they do not default-deny the public site
- exception countries, trusted IPs, and trusted ASNs remain explicit
- emergency regional policy requires the same short expiry/review discipline as other emergency controls

## Headers and CSP

`csp-inventory.json` is generated from/checked against the sanitized Pages build and rendered as `Content-Security-Policy-Report-Only`. It covers the observed script, style, font, image, media, form, connect, frame, manifest, and worker sources. No WebSocket source was detected.

Before enforcement:

1. collect report-only events across every supported page
2. resolve direct browser Anthropic and third-party CORS-proxy use
3. decide whether disabled analytics sources should remain
4. migrate inline scripts/styles to nonces/hashes before removing `unsafe-inline`
5. narrow broad HTTPS image/media schemes
6. reconcile the build-time enforcing CSP meta and `_headers` intent with the edge header
7. validate form, frame, API, analytics, WebSocket, COOP, CORP, and frame-ancestor behavior

The edge also adds HSTS (without subdomain/preload by default), nosniff, referrer, permissions, compatible COOP/CORP, CSP frame protection, and identifying-header removal. The application owns CORS and sensitive route cache semantics.

## DDoS, caching, and origin shielding

Managed DDoS is a provider/account capability and is not represented as successfully enabled by Terraform. `cache-policy.example.json` defines aggressive versioned-asset caching, short HTML caching, and sensitive/API bypass. Provider tiered cache/origin shield is a manual/adapter-specific mapping. Pages remains bypassable; dynamic origins must validate edge identity and reject direct ingress.

## Change-control evidence

Every promotion to challenge/block records rule/version, owner, rationale/ticket, match volume, false-positive analysis, exceptions, test results, rollback, operator, and timestamp. CI creates a reviewable plan digest. Apply reconstructs the same inputs, locks remote state, recomputes the plan, and refuses a changed digest.

Emergency mode is managed challenge only, excludes verified/trusted/webhook traffic, requires custom-WAF ownership, and expires within 24 hours.

# Edge Security Assessment

Status: repository implementation prepared; no DNS, CDN, TLS, WAF, logging destination, or provider configuration was applied.

## Scope and method

The assessment covered the repository tree, Pages build artifact, deployment workflows, Terraform, application routes, forms/webhooks, CSP and header declarations, environment-variable names, and reverse-proxy indicators. Secret values were neither read nor recorded. The exact CSP inventory is machine-readable in `infra/edge/csp-inventory.json` and is checked against a fresh Pages build in CI.

## Hosting and deployment findings

| Area | Finding | Edge implication |
|---|---|---|
| Public frontend | Repository-root HTML, CSS, JavaScript, images, fonts, JSON, and other static assets | Treat as a static hostname and cache only safe GET/HEAD responses |
| Build | `tools/build_pages.py` produces the Pages artifact | CSP source discovery must inspect the built output, not just source files |
| Deployment | `.github/workflows/pages.yml` uses the official GitHub Pages artifact/deploy flow | Preserve this workflow; the edge is an independent perimeter in front of its custom hostname |
| Hosting | GitHub Pages is the current supported model | Pages cannot validate a secret origin header, mTLS identity, or provider egress ACL |
| Custom domain | Root `CNAME` contains `www.clearglassinc.com` | DNS target and proxy status require operator confirmation in GitHub and the DNS provider |
| Reverse proxy | No existing repository-managed reverse proxy was found for the root site | Do not assume requests already traverse a WAF/CDN |
| Existing edge IaC | `clearglass-commerce/infra/cloudflare/` also contains zone-phase resources | A single Terraform state must own each Cloudflare zone ruleset phase; import/consolidate before enablement |

## Runtime and route inventory

The Pages site is static: there is no root server-side session, login handler, webhook receiver, or API origin. It does make client-side requests and submits forms to third parties.

Dynamic applications exist elsewhere in the monorepo and must be treated as independent origins if exposed:

- `clearglass-commerce`: FastAPI services plus Next.js admin/storefront applications.
- Commerce routes include authentication/login surfaces, checkout/refund/inventory/approval APIs, Stripe webhook handling, and administrative paths.
- Other applications expose `/api/v1/*` routes, ingestion/procurement webhooks, and login/admin surfaces.
- Existing application authentication, authorization, signature verification, CORS, and local rate limiting remain mandatory. Edge controls are defense in depth and do not replace them.

The provider adapter therefore models three independent host scopes:

- public static hostname: `EDGE_PUBLIC_HOSTNAME`
- optional API hostname: `EDGE_API_HOSTNAME`
- optional administrative hostname: `EDGE_ADMIN_HOSTNAME`

Empty API/admin hostnames disable their route-specific resources. No speculative origin is created.

## Forms and third-party integrations

The built Pages artifact contains FormSubmit form posts, including an AJAX submission. Repository documentation also references Formspree. Both are inventory entries pending owner confirmation; neither should be removed from an enforcing policy until the supported form provider is decided.

Because those submissions go directly from the browser to a third-party hostname, this application's edge cannot rate-limit or WAF-inspect the submitted request. Move the form to a separately protected first-party API endpoint if centralized abuse control, validation, or logging is required; otherwise rely on the form provider's controls and avoid sending sensitive data.

Observed source classes include:

- script/style libraries from `unpkg.com`; optional analytics loaders for `plausible.io` and `www.googletagmanager.com`
- Google Fonts from `fonts.googleapis.com` and `fonts.gstatic.com`
- a frame origin at `turbo-fishstick-jg11zep.pages.github.io`; repository header intent also names YouTube privacy-enhanced embeds
- numerous public data APIs, including GitHub, Open-Meteo, USGS, NOAA, CISA, exchange-rate/market-data, geocoding, satellite/aviation, and threat-intelligence endpoints
- `formsubmit.co`, `formspree.io`, `corsproxy.io`, and a browser-side `api.anthropic.com` integration
- no WebSocket endpoint was detected in the built artifact

`corsproxy.io` and direct browser access to `api.anthropic.com` are high-risk integration choices. CSP inventory records them to prevent breakage during observation, but application owners should replace them with a governed server-side API before CSP enforcement. Do not put provider/API secrets into Pages JavaScript.

## Existing CSP and security headers

- `_headers` records useful intent, but GitHub Pages does not apply Netlify-style `_headers` as HTTP response headers.
- `tools/build_pages.py` injects an enforcing CSP meta element and referrer meta into HTML. CSP directives that require HTTP headers, such as `frame-ancestors`, cannot be reliably supplied by a meta element.
- The current injected CSP source list is narrower than the observed artifact. Some optional pages/integrations can already be blocked by the browser.
- The new edge CSP remains `Content-Security-Policy-Report-Only`. It is derived from `csp-inventory.json`, so adding the edge configuration cannot itself tighten or break the frontend.
- The edge may enforce HSTS, nosniff, referrer, permissions, frame, COOP, and CORP only after compatibility validation. HSTS `includeSubDomains` and `preload` remain off in both committed environments.
- Application/origin code remains authoritative for route-specific CSP, CORS, `Cache-Control`, and sensitive responses.

## Environment and secret findings

Environment-variable names exist across the dynamic subprojects for databases, authentication, payment/webhook providers, deployment targets, analytics, and external APIs. Values were not inspected or copied. Edge-specific protected names are listed in `infra/edge/README.md`.

The edge implementation intentionally:

- receives provider and state credentials only from protected GitHub environment secrets
- renders an ephemeral mode-`0600` Terraform variable file without printing values
- excludes runtime variables, plans, and Terraform state from version control
- separates read/plan and write/apply provider tokens
- records policy version, commit SHA, operator, plan digest, environment, change ticket, and UTC timestamp without storing request secrets

## Security tooling and gaps found

Existing repository security tooling includes Pages artifact hardening, Terraform, pinned GitHub Actions, policy tests, and application-side security controls. The prior edge baseline had the following material gaps, addressed by this change:

1. Managed WAF scope covered only the public host, not future API/admin hosts.
2. Webhook rate limiting was documented but not represented in Terraform.
3. CI planning did not use an explicit locked remote-state backend.
4. Manual workflow inputs could alter broad WAF/rate actions without a reviewed configuration commit.
5. The policy schema was parsed but not actually enforced.
6. Emergency mode did not require a short expiry, accountable owner, and ticket.
7. CSP documentation did not match the built artifact.
8. Zone-wide bot controls could challenge non-browser API clients.
9. A single global rate-limit action could inappropriately challenge assets or webhooks.

## Residual risks and limitations

### GitHub Pages origin exposure

GitHub Pages cannot require Cloudflare-only identity, source ACLs, authenticated origin pulls, or mTLS. The edge can protect traffic sent to the custom hostname, but a determined client may reach a GitHub-controlled Pages hostname directly if it is known. This is an accepted residual risk until the static artifact moves to a private/authenticated origin such as an object store with origin access control, private storage behind an enterprise edge, or a Worker/object-store architecture.

### Provider plan and state ownership

Managed bot scores, threat fields, body-size fields, Logpush, origin shielding, and some actions vary by provider/plan. All plan-specific resources are disabled until a real provider plan confirms availability. Existing Cloudflare states must be consolidated or imported before this module owns the same zone phase.

The neutral policy includes a disabled repeated-challenge-failure escalation template, but the Cloudflare v4 ruleset adapter does not invent a per-client challenge-failure counter. Implement it only through a verified provider-native signal or a privacy-reviewed stateful edge service, with expiry; until then, alert on aggregate failure telemetry and use manually reviewed temporary quarantine.

### Configuration status

Committed staging and production files disable every provider-mutating feature. A successful local or CI validation proves only syntax and safety invariants. It does not prove DNS proxying, certificate issuance, provider activation, origin privacy, log delivery, or runtime policy effectiveness.

## Prioritized risk treatment

1. Confirm zone ownership, account plan, and the single authoritative Terraform state.
2. Configure privacy-minimized logging and dashboards before any enforcement.
3. Plan managed/custom WAF in staging with all custom actions still `log`.
4. Manually proxy a staging hostname and validate the full test matrix.
5. Promote uncertain automation to managed challenge only after false-positive review.
6. Route API/admin services through distinct hostnames with origin authentication and application-side enforcement.
7. Resolve browser-side Anthropic/CORS-proxy usage and then converge application and edge CSP.
8. Migrate the static artifact from Pages if non-bypassable origin access becomes mandatory.

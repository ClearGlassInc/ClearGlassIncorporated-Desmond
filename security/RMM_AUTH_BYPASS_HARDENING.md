# RMM Auth-Bypass Pattern Review — CVE-2026-18577 Class

**Status:** review completed, one repository control added. Not a certification.
**Review date:** 2026-08-05
**Scope:** the ClearGlass control planes in this repository, plus the client
posture guidance ClearGlass issues to managed clients.
**Owner to confirm:** `[SECURITY_OWNER]`

This document separates what was **verified in this repository** from what
**requires client-side action** on estates ClearGlass does not host. Nothing here
asserts that a client environment is patched — that is the checklist's job.

---

## 1. The trigger

On 2026-08-02 N-able published an advisory for **CVE-2026-18577**, an
authentication bypass in N-central, the RMM platform used by many MSPs and
internal IT teams to administer managed estates.

| Fact | Detail |
|------|--------|
| Vulnerability | Unauthenticated remote attacker bypasses authentication and gains administrative control of the N-central server |
| Origin | **Incomplete fix** for an earlier auth bypass, CVE-2026-18556 |
| Exploited in the wild | Since 2026-08-01 |
| CISA KEV | Added 2026-08-03 |
| Affected | All N-central up to and including 2026.3.1, prior to Hotfix 1 |
| Fix | Upgrade to **2026.3.1.7** or later |

Observed post-exploitation, per the vendor:

1. Attackers used N-central's **Take Control** feature to reach managed endpoints
   from the compromised server.
2. They dropped a file named **`svchost.exe` in users' Documents folders** — a
   legitimate binary name in an illegitimate location.
3. They created a Windows service named **`Cloudflared`** establishing an
   outbound **Cloudflare Tunnel** for persistent access.

N-able has published a custom service template to check Windows endpoints for
these indicators.

**ClearGlass exposure:** ClearGlass does not operate N-central in this repository
and ships no N-central integration. The exposure is **client-side** and is handled
through the posture checklist, not through code here.

## 2. Why this class matters more than this CVE

Strip the vendor name and the pattern is generic, and it is the pattern worth
defending against:

| Property | Why it hurts |
|----------|-------------|
| **The fix was incomplete** | The first patch closed the reported path, not the underlying class. Teams that patched CVE-2026-18556 and closed the ticket were still exposed. |
| **Pre-auth reachability** | No credential, no phishing, no user interaction. Internet exposure alone is sufficient. |
| **The compromised system is a trust anchor** | An RMM is *designed* to hold privileged remote access to every managed endpoint. Compromising it converts one bug into estate-wide reach — the blast radius is the whole client base, not one host. |
| **Post-exploitation looks like administration** | Take Control is the product's headline feature. `cloudflared` is a signed, legitimate tool. Neither trips naive malware detection. |
| **The MSP is the multiplier** | One compromised MSP console reaches every downstream client at once. |

The transferable lesson is not "patch N-central". It is: **a correct
authentication control with incomplete coverage is an authentication bypass.**

## 3. Repository review

Reviewed the ClearGlass commerce control plane — the closest analogue in this
repository to an RMM console, in that it holds an administrative surface capable
of consequential action (pricing, refunds, approvals, live-marketplace writes).

### 3.1 What was already sound

`clearglass-commerce/control-plane/app/security.py` holds up well against this
pattern class:

- **Fails closed at startup.** `APP_ENV=production` with no `ADMIN_API_KEY`
  raises at boot. A production control plane cannot come up wide open — the exact
  condition that makes a pre-auth bypass catastrophic.
- **Constant-time comparison** across all configured keys, no early exit.
- **Key rotation without downtime** (comma-separated keys), so rotating after an
  incident is not itself an outage decision.
- **Authenticated principal returned**, so `decided_by` on an approval is a real
  credential rather than a self-asserted request field. An attacker cannot
  approve their own action by claiming to be someone.
- **Approval gate is itself gated.** `/approvals/{id}/approve` requires admin —
  the governance model's weakest possible point is closed.
- Rate limits on checkout, the Stripe webhook, and approval decisions; webhook
  idempotency on redelivery.

Verified: every mutating route is in fact guarded. Routers are included with
`dependencies=[Depends(require_admin)]` in `app/main.py`, and the two open
mutating endpoints — customer checkout and the Stripe webhook — are open by
necessity and separately protected (rate limit; signature verification plus
idempotency).

### 3.2 The gap found, and closed

**Coverage was enforced by convention, not by a check.**

The guard is applied at `include_router()` time. That is correct and complete
*today*. But nothing failed if someone added a new router without
`dependencies=admin`, or added a mutating endpoint to the one router that is
deliberately un-included (`payments`, where only the refund is gated inline).
`tests/test_security.py` thoroughly tested that `require_admin` *works* — it did
not test that it is *applied everywhere it should be*.

That is precisely the CVE-2026-18577 shape: the control was never wrong, its
coverage was incomplete, and nothing detected the gap.

**Added:** `clearglass-commerce/control-plane/tests/test_route_auth_coverage.py`

It enumerates every route on the built application and asserts that each
`POST`/`PUT`/`PATCH`/`DELETE` either resolves `require_admin` anywhere in its
dependency tree, or appears in an explicit allow-list **with a written
justification**. Supporting assertions:

- the allow-list cannot hold stale entries for routes that no longer exist;
- an allow-listed route that later *gains* a guard must be removed from the list,
  so the list never overstates the open surface;
- the approval gate and the money/pricing routes are checked by name;
- allow-list reasons must be substantive, not placeholders.

Two details worth recording, because both were live defects during development:

1. **The test must not be able to pass vacuously.** FastAPI 0.14x stopped
   flattening included routers into `app.routes`; naive enumeration returned zero
   routes and the coverage assertion passed by finding no violations. A security
   test that silently finds nothing is worse than no test. There is now an
   explicit floor (`>= 10` mutating routes, plus a known path) that fails the
   suite if discovery breaks again.
2. **Include-time guards use a different object shape.** A resolved `Dependant`
   exposes its callable as `.call`; the `Depends` marker stored by
   `include_router(dependencies=...)` exposes it as `.dependency`. Checking only
   `.call` reported every include-time-guarded route as unguarded. The walker
   handles both.

Verified by regression: removing `dependencies=admin` from the store router makes
the suite fail and names all three newly-exposed endpoints, including
`/store/update-pricing`.

### 3.3 Residual, requiring action outside this repository

| Item | Owner | Note |
|------|-------|------|
| Network exposure of the control plane | Hosting | Admin surface should not be internet-reachable without an allow-list or IdP in front |
| MFA on operator identities | IdP | `ADMIN_API_KEY` is a bearer credential, not an identity. It is not MFA and should not be described as such |
| Externally retained audit copy | Hosting | The `events` ledger and RFED ledger live in the same database as the data they describe |
| Two-person release approval | GitHub | Branch protection + protected environments |

## 4. What ClearGlass changed in its own automation

The RFED™ module shipped alongside this review
(`docs/rfed_audit_trail_spec.md`) applies the same lesson to ClearGlass's own
agentic automation, where an agent holds RMM-shaped privilege:

- `execute_remote_command`, `grant_privileged_access`, `modify_access_policy`,
  `rotate_credentials`, `disable_security_control`, and `export_client_data` are
  scored 92–100 and are in the always-escalate set. **An agent cannot take an
  RMM-shaped action unattended**, whatever its confidence.
- Unknown actions fail closed at 85 rather than falling through to permitted.
- The workflow's routing Switch sends its **fallback** output to the blocked
  branch, so an unroutable decision is treated as blocked rather than executable.
- Ingress is HMAC-signed with a replay window; a missing secret refuses all work.
- Every decision is sealed into a hash chain, so post-incident you can prove what
  the automation did and did not do — the question every N-central victim is
  currently trying to answer from logs that were never designed for it.

## 5. Client posture

Client-facing actions live in **`security/CLIENT_POSTURE_CHECKLIST.md`**, updated
with an RMM section as part of this review. It is written to be handed to a
client directly.

## 6. Sources

- [Rapid7 — CVE-2026-18577 exploited in the wild](https://www.rapid7.com/blog/post/etr-cve-2026-18577-n-able-n-central-authentication-bypass-exploited-in-the-wild/)
- [N-able — N-central Security Update, August 2, 2026](https://www.n-able.com/blog/n-central-security-update-august-2-2026)
- [N-able Status — 2026.3 Hotfix 1 mitigation](https://status.n-able.com/2026/08/02/n-central-2026-3-hotfix-1-mitigation-for-cve-2026-18577/)
- [The Hacker News — CISA adds flaw to KEV after customer compromises](https://thehackernews.com/2026/08/cisa-adds-exploited-n-able-n-central.html)
- [BleepingComputer — N-able warns of auth bypass exploited in attacks](https://www.bleepingcomputer.com/news/security/n-able-warns-of-n-central-auth-bypass-flaw-exploited-in-attacks/)
- [Help Net Security — attackers reach managed endpoints](https://www.helpnetsecurity.com/2026/08/03/cve-2026-18577-n-able-n-central-vulnerability/)
- [Huntress — active exploitation analysis](https://www.huntress.com/blog/n-able-vulnerability-exploitation)

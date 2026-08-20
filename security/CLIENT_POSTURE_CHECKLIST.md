# ClearGlass Client Security Posture Checklist

**Version:** 2026.08 · **Updated:** 2026-08-05
**Prepared by:** ClearGlass Inc., Burlington, Ontario

A working checklist for managed and advisory clients. It is written to be worked
through in order, with evidence recorded against each line — not read once.

**How to use it.** Every item has an owner and an evidence column. "We think so"
is not evidence. A screenshot, a config export, a ticket number, or a query
result is. Items marked **[KEV]** address a vulnerability that is confirmed
exploited in the wild and on CISA's Known Exploited Vulnerabilities catalogue —
those are not scheduled, they are done now.

---

## 0. Immediate — remote monitoring & management (RMM) `[KEV]`

**Why this is section zero.** Your RMM holds privileged remote access to every
device it manages. It is the single system where one authentication bypass
becomes access to your entire estate. In August 2026 that stopped being
hypothetical: CVE-2026-18577, an authentication bypass in N-able N-central, was
exploited in the wild from 1 August and added to CISA KEV on 3 August. It existed
because the fix for an *earlier* bypass (CVE-2026-18556) was incomplete — so
organisations that had patched once were still exposed.

### 0.1 If you run N-able N-central

| # | Action | Owner | Evidence |
|---|--------|-------|----------|
| 0.1.1 | Confirm your exact N-central version. Anything **up to and including 2026.3.1 without Hotfix 1** is affected. | IT | Version screenshot |
| 0.1.2 | Upgrade to **2026.3.1.7 or later**. Treat as emergency change; do not wait for the next window. | IT | Change record |
| 0.1.3 | Confirm the earlier CVE-2026-18556 patch did **not** leave you believing you were covered. Both need the current build. | IT | Version check post-upgrade |
| 0.1.4 | Run N-able's published IoC service template against all managed Windows endpoints. | IT / MSP | Template run output |
| 0.1.5 | Hunt: any Windows service named **`Cloudflared`** you did not deliberately create. | SecOps | Query result |
| 0.1.6 | Hunt: any **`svchost.exe` inside a user's Documents folder**. Legitimate `svchost.exe` never lives there. | SecOps | Query result |
| 0.1.7 | Review historical network logs for traffic to the vendor-published malicious IPs, and for unexpected outbound Cloudflare Tunnel connections. | SecOps | Log review note |
| 0.1.8 | Review **Take Control** session history for sessions no technician can account for. | IT | Session export |
| 0.1.9 | If any indicator is found: treat as confirmed compromise of the RMM server. Rotate all credentials reachable from it, including those stored for managed endpoints. | IR lead | IR ticket |

### 0.2 Whatever RMM you run

The vendor name changes; the exposure does not. This applies to N-central,
ScreenConnect, Kaseya, Datto, SimpleHelp, TeamViewer, Atera, or anything else
holding remote privileged access.

| # | Action | Owner | Evidence |
|---|--------|-------|----------|
| 0.2.1 | Inventory every remote-access and RMM tool in the environment, including ones a single team installed for one project. | IT | Inventory list |
| 0.2.2 | Remove the console from direct internet exposure. Put it behind VPN, an IP allow-list, or an identity-aware proxy. | Network | Firewall rule |
| 0.2.3 | Enforce **MFA on every RMM operator account**, without exception for service or break-glass accounts (those get vaulted credentials and monitoring instead). | IdP | MFA report |
| 0.2.4 | Subscribe to the vendor's security advisories directly. Do not rely on discovering these through the news. | IT | Subscription proof |
| 0.2.5 | Establish an emergency patch path for RMM/remote-access specifically, with an agreed SLA (recommend: 24 hours for a KEV entry). | IT lead | Written SLA |
| 0.2.6 | **Re-verify after every vendor patch.** Confirm the specific CVE is closed in your running build — incomplete fixes are common enough to plan for. | IT | Post-patch verification |
| 0.2.7 | Alert on outbound tunnelling tools (`cloudflared`, `ngrok`, `tailscale`, `frp`) appearing on servers where they are not part of the design. | SecOps | Detection rule |
| 0.2.8 | Confirm your MSP's own RMM posture in writing. Their console is a path into your estate. | Vendor mgmt | Written attestation |
| 0.2.9 | Alert on new Windows service creation on servers. Both this campaign and most persistence generally land here. | SecOps | Detection rule |

## 1. Identity and access

| # | Action | Owner | Evidence |
|---|--------|-------|----------|
| 1.1 | MFA on all administrative accounts. Phishing-resistant (FIDO2/passkey) for the highest privilege. | IdP | Coverage report |
| 1.2 | No shared administrator accounts. Named accounts only, so an audit trail means something. | IdP | Account list |
| 1.3 | Separate day-to-day accounts from privileged ones. | IdP | Account list |
| 1.4 | Quarterly access review; remove leavers within 24 hours of departure. | HR / IT | Review record |
| 1.5 | Vault service-account credentials; rotate on a schedule and after any incident. | IT | Vault export |
| 1.6 | Confirm bearer API keys are **not** counted as MFA. They are a shared secret, not an identity. | IT | Written confirmation |

## 2. Exposure

| # | Action | Owner | Evidence |
|---|--------|-------|----------|
| 2.1 | External attack-surface scan. Every internet-reachable service justified or removed. | SecOps | Scan report |
| 2.2 | No management interface (RMM, hypervisor, backup console, database admin) reachable from the internet. | Network | Firewall review |
| 2.3 | Track CISA KEV and treat entries affecting your stack as emergency changes. | SecOps | KEV process doc |
| 2.4 | Documented patch SLAs by severity, with KEV items shortest. | IT lead | Written SLA |

## 3. Detection and response

| # | Action | Owner | Evidence |
|---|--------|-------|----------|
| 3.1 | EDR on all servers and workstations, alerting to a monitored destination. | SecOps | Coverage report |
| 3.2 | Logs retained off the system that generates them, minimum 90 days. An attacker with admin on a box can edit its local logs. | SecOps | Retention config |
| 3.3 | Written incident response plan naming the people, not just the roles. | IR lead | Plan document |
| 3.4 | Tested restore from backup within the last 6 months. Backups you have never restored are a hypothesis. | IT | Restore test record |
| 3.5 | Offline or immutable backup copy, unreachable from the RMM and from domain admin. | IT | Backup config |

## 4. Third parties

| # | Action | Owner | Evidence |
|---|--------|-------|----------|
| 4.1 | Inventory every vendor with remote access, and what each can reach. | Vendor mgmt | Vendor list |
| 4.2 | Vendor access is time-bound and revocable, not standing. | IT | Access config |
| 4.3 | Contracts require breach notification within a defined window. | Legal | Contract clause |

## 5. If you use AI automation

Applies to any AI system that can act, not only ClearGlass-built ones.

| # | Action | Owner | Evidence |
|---|--------|-------|----------|
| 5.1 | Confirm no AI agent can take a privileged action — remote execution, access change, credential rotation, data export — without human approval. | IT lead | Policy config |
| 5.2 | Confirm every agent action is logged with the **exact model id**, its inputs, and the approver. | IT lead | Sample audit record |
| 5.3 | Confirm the audit log is append-only and tamper-evident, and that you can verify it independently of the vendor. | SecOps | Verification run |
| 5.4 | Confirm the system fails **closed** on an unrecognised action. | IT lead | Test result |
| 5.5 | Confirm content retrieved from untrusted sources is treated as data, never as instructions. | IT lead | Policy config |
| 5.6 | Run new automation in dry-run for a defined review period before it acts. | IT lead | Dry-run log |

> ClearGlass systems meet 5.1–5.6 through the RFED™ audit-trail module. Ask for
> a chain verification against your own ledger — you should not have to take our
> word for it, and the module is built so you don't have to.

---

## Sign-off

| Field | Value |
|-------|-------|
| Client | |
| Completed by | |
| Date | |
| Sections not applicable (with reason) | |
| Next review due | |

**Standing caveat.** This checklist reduces risk; it does not eliminate it, and
completing it is not a certification or a warranty. Items depending on systems
ClearGlass does not host are the client's to verify — we can advise and validate,
but we cannot attest to an estate we do not operate.

**Sources for section 0:**
[Rapid7](https://www.rapid7.com/blog/post/etr-cve-2026-18577-n-able-n-central-authentication-bypass-exploited-in-the-wild/) ·
[N-able advisory](https://www.n-able.com/blog/n-central-security-update-august-2-2026) ·
[CISA KEV addition](https://thehackernews.com/2026/08/cisa-adds-exploited-n-able-n-central.html) ·
[BleepingComputer](https://www.bleepingcomputer.com/news/security/n-able-warns-of-n-central-auth-bypass-flaw-exploited-in-attacks/)

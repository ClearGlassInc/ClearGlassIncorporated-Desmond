# ClearGlassInc Artemis custom-domain email runbook

> **Scope:** establish the production mailbox `desmond@clearglassinc.com` without changing the website hosted on the same domain. This is an operator runbook, not evidence that any provider, tenant, DNS record, or security control is currently configured.

## Exact outcome and shortest safe path

Owning `clearglassinc.com` is necessary, but it does not itself create a mailbox. The domain must be connected to a mail host, and the mail host must contain a licensed user whose primary address is `desmond@clearglassinc.com`.

Email domain names and, in normal hosted-mail operation, mailbox addressing are case-insensitive. Configure and publish the canonical address in lowercase as `desmond@clearglassinc.com`; messages addressed as `Desmond@clearglassinc.com` should reach the same mailbox, while the lowercase form avoids inconsistent display, forms, and documentation.

The recommended implementation is:

1. Buy **Microsoft 365 Business Premium** directly from Microsoft for one user. Do not buy a second domain during checkout.
2. Create the temporary Microsoft tenant and protect its administrator with phishing-resistant MFA.
3. In the Microsoft 365 admin center, add the existing domain `clearglassinc.com` and copy Microsoft's unique verification TXT record into the domain's authoritative DNS console.
4. After verification, create the user **Desmond**, set the username and primary address to `desmond@clearglassinc.com`, and assign the Exchange-containing licence.
5. Copy the tenant-specific MX, SPF, Autodiscover, and DKIM values shown by Microsoft into DNS. Preserve all website records; only replace obsolete mail records.
6. Enable DKIM, publish DMARC initially at `p=none`, and test inbound and outbound delivery before tightening DMARC.

Do not copy another tenant's MX, verification, or DKIM targets from this document or a tutorial. Those values are generated for the specific Microsoft tenant. DNS changes are the only part performed at the registrar or DNS provider; mailbox creation and security configuration happen in Microsoft 365.

### Completion checklist

The setup is complete only when all of the following are true:

- `desmond@clearglassinc.com` can sign in at Outlook on the web with MFA.
- External test accounts can send to the mailbox and receive replies.
- A received test message reports aligned `spf=pass`, `dkim=pass`, and `dmarc=pass` in its authentication results.
- Existing `clearglassinc.com` website records and GitHub Pages routing still resolve normally.
- Recovery accounts, DNS rollback values, and tenant ownership are recorded in the approved credential/recovery system—not in this repository.

## Recommendation

Use **Microsoft 365 Business Premium** for ClearGlassInc Artemis. It gives a small security-focused company hosted Exchange, first-class Outlook support, Microsoft Entra ID, Conditional Access, Intune, and the stronger Defender capabilities in one operational boundary. Business Basic or Standard can host the same mail domain, but Premium is the better baseline when device posture, phishing resistance, and identity controls matter.

| Provider | Strengths | Trade-offs | Best fit |
| --- | --- | --- | --- |
| [Microsoft 365](https://www.microsoft.com/en-us/microsoft-365/business/compare-all-microsoft-365-business-products) | Native Outlook/Exchange experience; mature identity and device policy; Conditional Access and endpoint management in Business Premium; strong audit and compliance ecosystem | More administration; licensing and some security features vary by plan; legacy protocol settings require attention | **Recommended** when Outlook, Windows, Microsoft security, or regulated customer work is central |
| [Google Workspace](https://workspace.google.com/pricing.html) | Excellent browser-first Gmail collaboration; straightforward administration; strong anti-spam and identity controls; broad SaaS integration | Outlook is not the native experience; advanced endpoint, retention, and security features depend on edition; Outlook sync behavior should be tested before standardizing | Browser-first teams already centered on Google Drive and Meet |
| [Zoho Mail](https://www.zoho.com/mail/zohomail-pricing.html) | Lower-cost plans; custom-domain email; useful admin and migration tooling; broad Zoho suite | Smaller security/integration ecosystem; advanced retention, S/MIME, and archival features vary by plan; Outlook access may require a paid tier and enabled IMAP/ActiveSync | Cost-sensitive teams with modest compliance and endpoint-management needs |

Pricing, plan entitlements, and product names change. Confirm the current plan comparison and data-residency terms before purchase. Do not choose only on mailbox price: identity protection, retention, eDiscovery, audit-log duration, endpoint control, support, and recovery are part of the effective cost.

## Preconditions and change plan

1. Identify the **authoritative DNS host** for `clearglassinc.com` (the nameservers shown by `dig NS clearglassinc.com`), and sign in using a phishing-resistant administrator identity.
2. Export or screenshot the current DNS zone. Record the previous mail provider, existing MX/TXT/CNAME records, and rollback owner.
3. Inventory every legitimate sender using `@clearglassinc.com`: Microsoft 365, website forms, CRM, ticketing, monitoring, and bulk-mail platforms. SPF and DKIM must cover each one, preferably with bulk/transactional mail isolated on a subdomain.
4. Lower the TTL of mail-related records to approximately 300 seconds at least one old-TTL interval before the cutover. Do **not** remove website `A`, `AAAA`, `CNAME`, `CNAME`/Pages, or verification records unrelated to mail.
5. Create and test the mailbox before changing MX. Schedule the cutover during a monitored window; retain access to the old mailbox until migration and rollback windows close.

## Microsoft 365 implementation

Microsoft's admin wizard is the source of truth for tenant-specific record values. Labels shown below are examples; copy the exact values displayed for the tenant rather than guessing them.

### 1. Create the tenant and protect the bootstrap administrator

1. Purchase the selected Microsoft 365 business plan and create the tenant. The initial account uses an `*.onmicrosoft.com` address.
2. Create two dedicated cloud-only emergency administrator accounts on `*.onmicrosoft.com`; exclude only those accounts from Conditional Access, protect each with separate hardware security keys, alert on their use, and do not use them for email or daily work.
3. Create a separate named administrator account for routine administration. Do not give the future daily mailbox permanent Global Administrator privileges.
4. Register at least two strong authentication methods before changing the domain or access policies.

### 2. Add and verify `clearglassinc.com`

1. Open the [Microsoft 365 admin center](https://admin.microsoft.com), then **Settings → Domains → Add domain**.
2. Enter `clearglassinc.com`.
3. Select manual DNS setup. Microsoft supplies a verification TXT record similar to:

   ```dns
   Type: TXT
   Host/Name: @
   Value: MS=ms########
   TTL: 300 (or provider default)
   ```

4. Add that exact TXT value at the authoritative DNS host. Keep unrelated TXT records; a domain can have multiple TXT records.
5. Return to the wizard and select **Verify**. DNS propagation is not instantaneous, so retry after confirming the authoritative nameservers return the value.
6. Select only the Microsoft services actually being deployed. Do not delegate nameservers to Microsoft merely to configure email.

### 3. Create the first mailbox

1. In **Users → Active users → Add a user**, enter **Desmond** as the display name and select `clearglassinc.com` as the domain.
2. Set the username and primary address to `desmond@clearglassinc.com`. Avoid using a shared role address as the person's sign-in identity.
3. Assign a licence containing Exchange Online, set usage location, and require registration of strong authentication at first sign-in.
4. Create role addresses such as `security@`, `billing@`, or `support@` as shared mailboxes where appropriate. Grant named users access; do not share passwords.
5. Send a test message internally while MX still points to the old provider.

### 4. Publish the mail-flow and authentication records

In **Settings → Domains → `clearglassinc.com` → DNS records**, copy the values Microsoft currently displays. A typical Exchange Online configuration has this shape:

| Purpose | Type | Host | Value | Priority |
| --- | --- | --- | --- | --- |
| Inbound mail | MX | `@` | tenant-specific `…mail.protection.outlook.com` target | `0` or the lowest numeric value |
| Sender Policy Framework | TXT | `@` | `v=spf1 include:spf.protection.outlook.com -all` | — |
| Autodiscover | CNAME | `autodiscover` | `autodiscover.outlook.com` | — |
| DKIM selector 1 | CNAME | `selector1._domainkey` | tenant-specific target shown by Microsoft | — |
| DKIM selector 2 | CNAME | `selector2._domainkey` | tenant-specific target shown by Microsoft | — |

Apply these controls deliberately:

1. **MX:** remove obsolete MX records when cutting over. Multiple providers' MX records are not a migration strategy; they can split or misroute delivery. Do not place an HTTP/CDN proxy in front of mail DNS records.
2. **SPF:** publish **one** SPF TXT record at the root. If other services send as the root domain, merge their documented `include` mechanisms into the same record. Keep DNS lookups within SPF's limit; do not create several `v=spf1` records. End with `-all` after all senders are inventoried.
3. **DKIM:** add both CNAME selectors, wait until they resolve publicly, then enable DKIM for the custom domain in the Microsoft Defender or Exchange administration flow. Send a message and confirm the header reports `dkim=pass`. Microsoft rotates between the two selectors; retain both.
4. **DMARC:** start with reporting mode only after SPF and DKIM pass:

   ```dns
   Type: TXT
   Host/Name: _dmarc
   Value: v=DMARC1; p=none; pct=100; rua=mailto:dmarc@clearglassinc.com; adkim=s; aspf=s
   ```

   Create and monitor `dmarc@clearglassinc.com` (or use a reputable DMARC reporting service). Aggregate reports are XML and can expose mail-flow metadata, so restrict access and retention. Some external reporting services require destination authorization records.
5. Review reports for all legitimate services and forwarding behavior. Progress in controlled stages from `p=none` to `p=quarantine; pct=10`, increase `pct`, then use `p=reject; pct=100`. A final strict policy can be:

   ```dns
   v=DMARC1; p=reject; pct=100; rua=mailto:dmarc@clearglassinc.com; adkim=s; aspf=s
   ```

6. Consider publishing `sp=reject` only after every subdomain sender is inventoried. Consider MTA-STS/TLS-RPT after mail flow is stable; they are useful additional transport controls, not substitutes for SPF, DKIM, or DMARC.

### 5. Validate before declaring the cutover complete

Query the authoritative and public DNS views:

```bash
dig +short NS clearglassinc.com
dig +short MX clearglassinc.com
dig +short TXT clearglassinc.com
dig +short CNAME selector1._domainkey.clearglassinc.com
dig +short CNAME selector2._domainkey.clearglassinc.com
dig +short TXT _dmarc.clearglassinc.com
```

Then test messages in both directions with unrelated Microsoft, Google, and other external accounts. Inspect received headers for `spf=pass`, `dkim=pass`, and `dmarc=pass`, confirm alignment uses `clearglassinc.com`, and verify messages do not unexpectedly land in junk. Test reply, attachment, calendar invitation, shared mailbox, and password/MFA recovery paths. Keep the old service available until delayed mail, historical data, delegates, aliases, and mobile clients are accounted for.

## Outlook connection

### Outlook on the web

1. Visit [outlook.office.com](https://outlook.office.com).
2. Sign in with the full address, such as `firstname.lastname@clearglassinc.com`.
3. Complete MFA registration and verify the expected ClearGlassInc Artemis tenant/organization context before approving a prompt.
4. Configure time zone, language, signature, and notification preferences. Do not create rules that automatically forward company mail to personal accounts.

### Outlook desktop (Windows or macOS)

1. Install a supported Microsoft 365 Apps/Outlook release from the signed-in Microsoft 365 portal or managed company deployment.
2. Choose **Add account**, enter the full custom-domain address, and use the Microsoft sign-in window. Autodiscover should configure Exchange automatically.
3. Complete MFA. Do not select POP/IMAP or manually enter SMTP credentials for a normal Exchange Online mailbox.
4. Confirm mail, calendar, contacts, search, and shared-mailbox access. If discovery fails, verify the licence, domain, `autodiscover` CNAME, client version, and Conditional Access sign-in logs before attempting manual configuration.

Modern Outlook uses OAuth/modern authentication. **Do not enable app passwords** for Outlook. App passwords exist only for narrowly approved legacy clients when legacy authentication is still allowed; replacing or retiring that client is safer.

## Security hardening baseline

### Identity and privileged access

- Require phishing-resistant MFA (FIDO2/passkeys or certificate-based authentication) for administrators and prefer it for all users. SMS should be recovery-only where unavoidable.
- Use Conditional Access to require MFA, block legacy authentication, constrain risky sign-ins, and require compliant managed devices for administrative access. Build policies in report-only mode, examine results, exclude only monitored emergency accounts, and stage enforcement to avoid lockout.
- Separate daily and privileged accounts. Apply least-privilege roles and use time-bound privileged activation where the subscription supports it.
- Disable sign-in and revoke sessions immediately during offboarding; preserve or delegate the mailbox according to the retention policy.
- Configure self-service password reset with strong methods and alerts. Review authentication-method registration and privileged-role assignments regularly.

### Mail and collaboration

- Keep Exchange Online Protection anti-phishing, anti-malware, Safe Links, and Safe Attachments capabilities enabled as licensed. Protect executives and look-alike domains, but test impersonation policy before enforcement.
- Disable automatic external forwarding by default. Restrict inbox-rule creation and SMTP AUTH to justified exceptions; disable POP and IMAP unless a documented application needs them.
- Use shared mailboxes or groups for role identities. Never share user credentials, MFA factors, or application secrets.
- Establish retention, legal hold, and deletion rules based on business/legal requirements rather than indefinite default retention.
- Separate marketing and machine-generated mail onto controlled subdomains (for example, `notify.clearglassinc.com`) with their own SPF, DKIM, DMARC, credentials, rate limits, and reputation.
- Review message trace, quarantines, forwarding rules, consent grants, anomalous sign-ins, and administrator audit events. Send alerts to an independently monitored security channel.

### Applications and AI integrations

- Prefer OAuth with administrator-reviewed, least-privilege scopes. Do not give AI assistants full mailbox access merely for convenience.
- Treat email body, attachments, calendar content, and retrieved links as untrusted input. An AI agent must not execute instructions found in mail, send messages, open cases, or disclose data without deterministic policy checks and the required human approval.
- Use a dedicated service principal or mailbox per integration, restrict it to specific mailboxes where supported, rotate/revoke credentials, and log reads, drafts, approvals, and sends without logging message contents unnecessarily.
- Block user consent to unverified or high-privilege applications; use an audited admin-consent workflow. Periodically remove unused enterprise applications and delegated grants.

## Google Workspace or Zoho equivalent

If a different provider is selected, retain the same staged cutover and security model but use only the records generated for that account and region:

1. Add `clearglassinc.com` in the provider's administrator console and verify ownership with its unique TXT record.
2. Create the licensed user/mailbox before switching MX.
3. Replace old MX records with the provider's **current** documented MX set. Google Workspace and Zoho values can differ from historical examples or by Zoho data-center region; never copy records from an unrelated tutorial.
4. Publish a single root SPF policy containing that provider's current include plus every other authorized sender.
5. Generate DKIM in the admin console, publish the generated selector TXT/CNAME, verify it, and explicitly start DKIM signing if the provider requires that second step.
6. Publish DMARC at `_dmarc`, monitor alignment, and move gradually to rejection.
7. For Outlook, use the provider-supported OAuth account flow. Google Workspace Sync for Microsoft Outlook is edition/platform dependent; Zoho's Exchange ActiveSync/IMAP availability is plan dependent. Confirm support before purchasing.

Authoritative setup references:

- [Microsoft: add a custom domain](https://learn.microsoft.com/en-us/microsoft-365/admin/setup/add-domain)
- [Microsoft: DNS records for Microsoft 365](https://learn.microsoft.com/en-us/microsoft-365/enterprise/external-domain-name-system-records)
- [Microsoft: DKIM for custom domains](https://learn.microsoft.com/en-us/defender-office-365/email-authentication-dkim-configure)
- [Microsoft: DMARC for outbound mail](https://learn.microsoft.com/en-us/defender-office-365/email-authentication-dmarc-configure)
- [Google Workspace: activate Gmail with MX records](https://support.google.com/a/answer/174125)
- [Google Workspace: SPF, DKIM, and DMARC](https://support.google.com/a/topic/2759254)
- [Zoho Mail: domain setup](https://www.zoho.com/mail/help/adminconsole/domains.html)
- [Zoho Mail: email authentication](https://www.zoho.com/mail/help/adminconsole/email-authentication.html)

## Rollback and ownership

If inbound delivery fails, first verify authoritative DNS, record syntax, and provider service health. If recovery will exceed the agreed outage budget, restore the exported prior MX records and TTLs, confirm the old provider accepts mail, and investigate without repeatedly alternating MX. DNS rollback does not move messages already accepted by the new provider.

Assign named owners for tenant administration, DNS, billing, security monitoring, mailbox recovery, retention, and incident response. Store recovery codes and domain-registrar recovery material in an access-controlled offline system. Revalidate DNS authentication after adding any sender and at least quarterly.

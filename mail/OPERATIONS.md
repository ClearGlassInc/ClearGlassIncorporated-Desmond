# ClearGlass Mail Production Operations

## Deployment gate

Do not expose an internet-facing mailbox until all of the following are verified in the target environment:

- Controlled mail domain and correct MX records.
- SPF record authorizes the intended outbound senders.
- DKIM signing is enabled and the public key is published.
- DMARC policy is published and monitoring is configured.
- SMTP endpoint is reachable with correct reverse DNS and TLS configuration.
- MTA/MDA configuration rejects unauthorized relay.
- Mailbox authentication and authorization are enabled.
- PostgreSQL/storage/queue credentials are externalized and least-privileged.
- Attachment scanning is active before user release.
- HTML sanitization or isolated rendering is active before browser delivery.
- Rate limits and abuse controls are active.
- Health checks, structured logs, metrics and alerting are active.
- Backup and restoration procedures have been tested.

## Inbound processing

1. Receive the message at the MTA.
2. Apply connection and abuse controls.
3. Evaluate SPF/DKIM/DMARC and preserve relevant authentication evidence.
4. Pass raw RFC 5322 bytes to the bounded parser.
5. Persist the provenance digest and policy decision.
6. Scan attachments before making them downloadable.
7. Sanitize HTML before browser rendering.
8. Store mailbox metadata and content under authenticated ownership.
9. Emit an audit event for security-relevant state changes.

## Outbound processing

1. Authenticate the mailbox owner.
2. Validate recipients and message size/content policy.
3. Create an idempotent outbound job.
4. Persist an audit event without storing credentials or tokens.
5. Deliver asynchronously through the configured MTA/provider.
6. Retry only transient failures with bounded exponential backoff.
7. Record delivery state and provider response codes.
8. Stop retries on permanent failures and surface actionable diagnostics.

## Incident response

If mail abuse, credential compromise, malware, or unauthorized access is suspected:

- Disable the affected credential or mailbox through the approved control plane.
- Preserve relevant audit/provenance evidence.
- Do not delete evidence or rewrite repository history.
- Rotate affected secrets using the external secret-management process.
- Inspect authentication, delivery and access logs.
- Determine affected messages/accounts before containment is lifted.
- Re-run security and operational validation before restoring service.

## Rollback

Application rollback must use an immutable, previously verified artifact. Database migrations must be backward-compatible before deployment. Never roll back by deleting production mail data, rewriting Git history, or replacing a credential with an unreviewed value.

## Evidence standard

A production release is successful only when the actual deployment, health checks, security controls and rollback evidence have been executed and inspected. Repository code alone is insufficient evidence that internet mail delivery is operational.

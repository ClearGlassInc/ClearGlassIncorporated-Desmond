# ClearGlass Mail Security Model

## Security objective

Keep untrusted internet mail isolated from application identity, browser execution, storage paths, and outbound transport. The parser is a normalization boundary, not a trust boundary for message content.

## Assets

- Mailbox identity and authorization state
- Raw message provenance and transport headers
- Message metadata and content
- Attachments and object-storage references
- SMTP/IMAP credentials
- DKIM private keys
- Database and queue credentials
- Audit records

## Trust boundaries

1. **Internet SMTP -> MTA:** hostile network input. Enforce TLS policy, SPF/DKIM/DMARC evaluation and connection/rate controls at the mail edge.
2. **MTA/MDA -> parser:** raw RFC 5322 bytes. Apply bounded parsing and preserve a message digest before normalization.
3. **Parser -> storage:** normalized data remains untrusted. Store content separately from authorization metadata and never treat filenames as filesystem paths.
4. **API -> browser:** HTML and attachments remain untrusted. Sanitize HTML with a reviewed sanitizer or isolate it in a restrictive sandbox before rendering.
5. **Application -> outbound queue:** outbound delivery is asynchronous and must use explicit authorization, rate limits, idempotency controls and audit events.

## Controls implemented in the parser

- SHA-256 provenance digest calculated before parsing.
- Maximum raw message size.
- Maximum MIME part count.
- Maximum header count and aggregate per-header byte size.
- Per-attachment and aggregate decoded attachment limits.
- MIME header decoding with failure-safe fallback.
- Attachment hashes recorded without executing content.
- HTML preview extraction ignores script/style/template/noscript content.
- Parser explicitly marks HTML and attachments as untrusted.
- No network access, command execution, file writes, or HTML rendering.

## Controls required outside the parser

- Authentication and mailbox-owner authorization on every message operation.
- CSRF protection for cookie-authenticated state-changing endpoints.
- Parameterized database access.
- Content Security Policy and restrictive framing policy for mail HTML.
- Reviewed HTML sanitizer before browser rendering.
- Malware/content scanning before attachment release.
- Object storage outside the web root with opaque identifiers.
- Login, search, fetch, attachment, and outbound-send rate limits.
- Queue-based outbound delivery with bounded retries and idempotency keys.
- Secret storage outside Git and outside browser-delivered configuration.
- Audit logging without message bodies, credentials, tokens, or private keys.

## Residual risks

The repository currently contains a parser and application contract, not a complete internet-facing mail stack. MX/DNS, Postfix/Dovecot or an equivalent provider, authentication, PostgreSQL, object storage, queueing, HTML sanitization, malware scanning, monitoring, abuse handling, backup/recovery and operational controls remain deployment-layer work.

No production-mail deployment claim should be made until those controls are independently verified.

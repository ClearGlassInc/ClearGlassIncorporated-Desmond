# ClearGlass Inc. Mail Foundation

This directory defines the application boundary for a ClearGlass-hosted webmail service. It is a **software foundation**, not a claim that an internet-facing SMTP/IMAP service is already deployed.

## Architecture

```text
Internet SMTP
     |
     v
 [MTA: Postfix]
     |
     v
 [MDA: Dovecot / LMTP]
     |
     +--> [Mail quarantine / policy gate]
     |
     v
 [Bounded MIME parser + normalization]
     |
     +--> [Attachment scanning/object storage]
     +--> [PostgreSQL metadata]
     |
     v
 [Authenticated Mail API]
     |
     v
 [ClearGlass Mail UI]
```

## Current implementation boundary

The repository currently provides:

- A provider-agnostic API contract.
- A standard-library RFC 5322/MIME parser with SHA-256 provenance.
- Explicit raw-message, MIME-part, header, and attachment resource limits.
- Conservative HTML preview extraction that is **not** an HTML sanitizer.
- Attachment metadata and digests without executing attachments.
- Regression/security tests for normal, malformed-boundary, and resource-limit behaviour.
- A read-only GitHub validation workflow for the mail parser.
- Security and production operations documentation.

## Security boundary

- SMTP ingress must terminate TLS and enforce SPF, DKIM and DMARC policy at the receiving boundary.
- Message content is untrusted input. Never render raw HTML without a reviewed sanitizer and restrictive browser policy.
- Attachments are untrusted files. Scan before making them available to users and keep them outside the web root.
- Store passwords only as slow, salted password hashes using a reviewed password-hashing library; never store plaintext credentials.
- Use short-lived application sessions, CSRF protection where applicable, secure cookies, rate limits, audit events and account abuse controls.
- Keep SMTP/IMAP credentials, DKIM private keys, database credentials and object-storage credentials outside Git.
- Preserve message provenance: retain the original message hash and selected transport headers so security investigations can reproduce parsing decisions.

## Processing contract

1. Accept raw RFC 5322 bytes at the mail boundary.
2. Compute SHA-256 before parsing.
3. Parse MIME using a standards-compliant parser.
4. Normalize headers and decode MIME transfer encodings safely.
5. Enforce raw-size, part-count, header-count, header-size, per-attachment and aggregate-attachment limits.
6. Extract plain text and an untrusted HTML candidate; preview extraction is not sanitization.
7. Record attachment metadata without trusting filenames or media types.
8. Persist provenance and policy decisions.
9. Scan attachments and sanitize/isolate HTML before application exposure.
10. Only then expose the message to the authenticated API/UI.

## Validation

The mail-specific GitHub workflow performs Python compilation and the parser regression suite. Workflow execution evidence must be inspected before claiming that validation passed.

For a local checkout, use the repository's supported Python environment and run:

```bash
python -m compileall -q mail/parser
python -m pytest mail/parser/test_clearglass_incoming_parser.py -q
```

## Deployment prerequisites

The repository alone cannot provision public MX routing or make a mail domain deliverable. A production deployment additionally requires:

- a controlled mail domain and DNS MX records;
- SPF, DKIM and DMARC records;
- an internet-reachable SMTP endpoint with appropriate reverse DNS;
- Postfix/Dovecot or an equivalent managed mail stack;
- durable encrypted storage and backups;
- malware/content scanning;
- authentication and mailbox authorization;
- queue-based outbound delivery;
- monitoring, abuse handling and operational procedures.

See `mail/SECURITY_MODEL.md` and `mail/OPERATIONS.md` before any production activation.

The implementation intentionally fails closed when these external prerequisites are absent.

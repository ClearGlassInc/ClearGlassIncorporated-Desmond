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
 [MIME parser + normalization]
     |
     +--> [Attachment/object storage]
     +--> [PostgreSQL metadata]
     |
     v
 [Mail API]
     |
     v
 [ClearGlass Mail UI]
```

## Security boundary

- SMTP ingress must terminate TLS and enforce SPF, DKIM and DMARC policy at the receiving boundary.
- Message content is untrusted input. Never render raw HTML without sanitization and a restrictive browser policy.
- Attachments are untrusted files. Scan before making them available to users and keep them outside the web root.
- Store passwords only as slow, salted password hashes using a reviewed password-hashing library; never store plaintext credentials.
- Use short-lived application sessions, CSRF protection where applicable, secure cookies, rate limits, audit events and account lockout/abuse controls.
- Keep SMTP/IMAP credentials, DKIM private keys, database credentials and object-storage credentials outside Git.
- Preserve message provenance: retain the original message hash and selected transport headers so security investigations can reproduce parsing decisions.

## Processing contract

1. Accept raw RFC 5322 bytes at the mail boundary.
2. Compute SHA-256 before parsing.
3. Parse MIME using a standards-compliant parser.
4. Normalize headers and decode MIME transfer encodings safely.
5. Enforce size/depth/part-count limits.
6. Extract plain text and sanitized HTML candidates.
7. Record attachment metadata without trusting filenames or media types.
8. Persist provenance and policy decisions.
9. Only then expose the message to the application API/UI.

## Deployment prerequisites

The repository alone cannot provision public MX routing or make a mail domain deliverable. A production deployment additionally requires:

- a controlled mail domain and DNS MX records;
- SPF, DKIM and DMARC records;
- an internet-reachable SMTP endpoint with appropriate reverse DNS;
- Postfix/Dovecot or an equivalent managed mail stack;
- durable encrypted storage and backups;
- malware/content scanning;
- monitoring, abuse handling and operational procedures.

The implementation intentionally fails closed when these external prerequisites are absent.

# HydraGuard Lab Threat Model

## Assets
Authorization records, audit findings, administrator sessions, audit evidence, lab fixtures, reports, and operational metadata.

## Adversaries
Unauthenticated Internet clients, malicious lab users, compromised browser sessions, malicious FTP servers, DNS rebinding infrastructure, and poisoned/malformed protocol responses.

## Primary threats and controls
- SSRF -> TargetPolicy, DNS re-check immediately before connect, private/loopback allow-list, metadata/multicast/broadcast denial.
- DNS rebinding -> resolve immediately before connection and authorize every returned address; no arbitrary redirects.
- Credential leakage -> schemas reject password/password-list fields; fixed lab identity only; log/report redaction.
- CSRF/session theft -> secure HTTP-only SameSite cookies, CSRF token, session rotation, MFA-ready session abstraction.
- XSS -> React escaping plus CSP; sanitize FTP server text before rendering.
- Command injection -> no shell execution; typed library calls only.
- DoS -> bounded concurrency, timeouts, cancellation, token-bucket rate limits, exponential backoff, Docker resource limits.
- Unauthorized scope expansion -> unexpired engagement required for every audit job; approved port exact-match; immutable audit event.
- Supply-chain risk -> lockfile, dependency audit, container scan in CI.

## Abuse cases explicitly prevented
Public target scan, cloud metadata access, credential stuffing, brute-force password testing, FTP bounce scanning, exploit execution, persistence, evasion, lateral movement, arbitrary file retrieval.

## Security objective
The system must fail closed whenever authorization, target classification, DNS resolution, input validation, or execution deadline cannot be established deterministically.

# Minerals Platform Security Guide

## Production requirements

1. Set `AUTH_MODE` to a non-development value.
2. Place the service behind a trusted identity-aware ingress supporting OAuth/OIDC or SAML and MFA.
3. Strip all inbound `x-cg-user-id`, `x-cg-org-id`, `x-cg-role`, and `x-cg-subject` headers at the public edge; inject them only after successful identity verification.
4. Store database, Redis, SMTP, webhook, provider, AI, export, and audit secrets in the deployment secret manager. Never expose them as `NEXT_PUBLIC_*` values.
5. Use TLS end-to-end and encrypted managed storage.
6. Restrict PostgreSQL and Redis to private networks/security groups.
7. Run migrations from a controlled deployment identity rather than the web process.
8. Deploy the BullMQ worker separately with only the provider/network permissions it needs.

## Authorization

Routes enforce organization-scoped roles: Viewer, Analyst, Senior Analyst, Data Steward, Administrator, API Client. Risk overrides and report publication require Senior Analyst. Ingestion requires Data Steward. Exports and analyst queries require Analyst or higher.

## Audit

Mutating and sensitive read workflows emit `AuditLog` records. `entryHash` is HMAC-linked to the previous record. Set a strong `AUDIT_HASH_SECRET` in production and rotate only under an explicit audit-key migration procedure.

## Data boundaries

- Public/demo data and private organization data must remain separate.
- Demo records are never promoted to verified state.
- No secrets, private supplier records, customer records, or internal infrastructure details may be written to GitHub Pages data paths.
- Provider licenses control redistribution and retention.
- Sensitive personal data is prohibited from risk scoring.

## Exports

Exports require Analyst role, are audit logged, and are capped at 5,000 rows per synchronous request. Extend with asynchronous signed exports for larger datasets rather than increasing the synchronous cap.

## Alerts

Email, Slack, Teams, and webhook credentials are server-side only. Test each connector using non-sensitive synthetic messages before enabling production routing. Generic webhook receivers should validate an application-level signature when the delivery format is expanded to include signing.

## AI

No source records are sent to an external AI provider by default. If an external adapter is introduced, enforce retrieval-only context, source identifiers, data classification, provider retention settings, audit metadata, and human review before publication.

## Uploads

No upload endpoint is enabled in the initial service. If uploads are added, enforce maximum bytes, MIME/content validation, malware scanning, quarantine, object-storage isolation, authorization, and retention controls before parsing.

## Incident response

For suspected credential compromise: revoke/rotate affected secrets, disable provider connectors, preserve audit/provenance evidence, invalidate identity-gateway sessions, assess exports and ingestion activity, and document the recovery timeline. Do not delete audit evidence during containment.

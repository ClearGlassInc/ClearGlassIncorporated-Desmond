# HydraGuard Lab Architecture

## Trust boundaries
Browser -> authenticated Next.js API -> policy gate -> bounded audit worker -> authorized FTP service.

Browser requests never directly initiate network connections. Workers receive a signed job contract containing engagement ID, target, port, simulation state, deadline, and policy decision.

## Components
- Next.js 15 + TypeScript + Tailwind/shadcn UI
- Fastify-compatible service layer behind Next API routes
- PostgreSQL + Prisma
- Redis + BullMQ
- Docker Compose isolated lab
- Prometheus metrics + JSON audit logs
- Vitest unit/integration tests + Playwright E2E

## Data model
Engagements own targets and authorization windows. Audits own findings. Audit events are append-only and hash-chained where practical. Reports reference findings and scope metadata, never credentials.

## Network enforcement
`TargetPolicy` canonicalizes hostnames/IP literals, rejects dangerous address classes, resolves DNS immediately before connection, compares every answer against the engagement scope, and fails closed on ambiguity. No FTP redirects are followed.

## Audit protocol
1. TCP connect with bounded timeout.
2. Read FTP banner only.
3. Determine explicit TLS/FTPS capability using protocol-safe negotiation.
4. Anonymous-login check uses one predefined non-sensitive lab probe only and is disabled for real targets unless the engagement explicitly authorizes the check.
5. Observe passive-port configuration without scanning arbitrary ports.
6. Record timeout behavior and reliable version disclosure.

No password dictionary, exploit payload, FTP bounce scan, arbitrary file access, or shell command is present.

## Risk model
Critical = cleartext authentication plus confirmed anonymous access.
High = confirmed anonymous access.
Medium = TLS unavailable or weak server configuration.
Low = banner disclosure or missing hardening.
Informational = reachable service/scope metadata.

All findings include evidence, limitation, confidence, and remediation. Real-target results never use a compromised claim.

# HydraGuard Lab

Production-oriented, authorization-first FTP security assessment platform. The implementation is fail-closed: simulation mode is the default, public/metadata/multicast/broadcast targets are denied, and real password material is not accepted or stored.

## Architecture
- `apps/web`: Next.js 15 UI/API surface.
- `packages/policy`: deterministic target authorization and DNS-rebinding protection.
- `packages/audit`: safe FTP observation primitives only; no credential guessing, exploitation, file traversal, or shell execution.
- `packages/security`: admin authentication/session boundaries, redaction, CSRF/rate-limit contracts.
- `packages/db`: Prisma schema and migrations.
- `packages/jobs`: BullMQ/Redis job contracts with cancellation and bounded concurrency.
- `lab/`: isolated Docker FTP fixture and mock authentication service.
- `tests/`: unit, integration, security, and Playwright suites.

## Safety invariants
1. Every network action requires an unexpired engagement and target policy approval.
2. Simulation mode defaults to `true` and authentication simulation never transmits passwords.
3. Only the fixed lab fixture identity is used: `lab-user`; its value is non-sensitive and invalid outside the lab.
4. DNS is resolved immediately before connection and every resolved address is re-authorized.
5. Server responses are sanitized before persistence/rendering; sensitive fields are redacted.
6. No shelling out to Hydra, Metasploit, ftp clients, scanners, or arbitrary commands.

## Run
`cp .env.example .env`
`docker compose -f docker-compose.hydraguard.yml up --build`

The UI is available on the configured local application port. See `docs/THREAT_MODEL.md` and `docs/ARCHITECTURE.md` before operating against any authorized system.

## Safe developer commands
- `lab:start`
- `lab:reset`
- `audit:ftp --target lab-ftp --port 21`
- `simulation:run`
- `report:generate`

No credential attack, exploitation, evasion, persistence, or lateral-movement commands are implemented.

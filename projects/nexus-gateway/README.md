# ClearGlass NEXUS Advanced Security Gateway

A hardened FastAPI control plane for zero-trust identity verification, deterministic AI tool governance, bounded asynchronous telemetry, and optional AEGIS orchestration.

## Security posture

This project deliberately does **not** accept arbitrary bearer tokens, arbitrary tool names, arbitrary shell commands, or silent network mutation. Production authentication uses Microsoft Entra ID JWT signature, issuer, audience, role/scope and expiry validation. If identity configuration is absent, protected endpoints fail closed.

The supplied AEGIS materials already establish the right operating principle: run Audit first, keep auto-remediation gated, and only enable destructive response after tuning noise and validating thresholds. NEXUS preserves that boundary by keeping AEGIS execution disabled unless explicitly enabled and configured.

## Architecture

- **Identity broker** — Entra ID token validation using published JWKS.
- **Agent policy engine** — capability allowlist, SHA-256 objective binding, payload schema enforcement, forbidden control fields, and payload-size limits.
- **Telemetry bus** — bounded `asyncio.Queue`, asynchronous worker, recent event ring buffer, request correlation IDs, and overload rejection.
- **AEGIS bridge** — fixed executable + argument list using `create_subprocess_exec`; no `shell=True`; allowed modes only; disabled by default.
- **Operator console** — static NEXUS status interface at `/console/`.

## Local build

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e '.[dev]'
ruff check .
pytest -q
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/console/` or `http://127.0.0.1:8000/docs`.

## Development auth

Development auth is **off by default**. For a local-only session:

```powershell
$env:NEXUS_DEV_AUTH_ENABLED='true'
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Use `Authorization: Bearer dev-operator`. Never enable this on an internet-facing deployment.

## Production Entra ID configuration

Set at minimum:

```text
NEXUS_ENTRA_TENANT_ID=<tenant-guid>
NEXUS_ENTRA_AUDIENCE=<application-id-uri-or-client-id>
NEXUS_REQUIRED_ROLE=Nexus.Operator
NEXUS_REQUIRED_SCOPE=nexus.execute
```

The gateway accepts access only when the token verifies and contains the configured role **or** scope.

## AEGIS integration

The uploaded AEGIS v6.1.1 documentation defines Audit as a non-remediating scan mode and recommends Audit before enabling auto-remediation. This gateway therefore defaults AEGIS dispatch to `Audit` and does not expose `Restore` or automatic remediation through its API.

To enable the optional Windows bridge:

```text
NEXUS_AEGIS_EXECUTION_ENABLED=true
NEXUS_AEGIS_SCRIPT_PATH=C:\ProgramData\ClearGlassCorp\AEGIS\ClearGlassCorp_AEGIS_v6.1.1_HARDENED_FINAL.ps1
NEXUS_AEGIS_POWERSHELL_EXECUTABLE=powershell.exe
```

Keep AEGIS API keys and MFA secrets out of Git. The provided config examples should remain placeholders only.

## Container

```bash
docker build -t clearglass-nexus-gateway:12.1 .
docker run --rm -p 8000:8000 --env-file .env clearglass-nexus-gateway:12.1
```

AEGIS execution is intended for a Windows worker/agent. A Linux container can run the gateway and telemetry plane, but it cannot execute Windows-only AEGIS host controls unless PowerShell and the underlying Windows capabilities exist.

## API surface

- `GET /healthz` — public liveness.
- `GET /readyz` — public configuration readiness without secret disclosure.
- `GET /api/v1/sitrep` — authenticated operational status.
- `POST /api/v1/agent/execute` — validate governed tool requests; downstream execution remains separate.
- `POST /api/v1/telemetry` — authenticated asynchronous ingestion.
- `GET /api/v1/telemetry/recent` — authenticated bounded history.
- `POST /api/v1/aegis/dispatch` — authenticated AEGIS orchestration when explicitly enabled.

## Important boundary

The gateway is an application-layer control plane. Azure Front Door/Application Gateway/WAF remains responsible for perimeter controls such as DDoS protection, managed WAF rules, bot controls, geo/ASN policy, and upstream request filtering. Do not present application middleware as a replacement for the WAF.

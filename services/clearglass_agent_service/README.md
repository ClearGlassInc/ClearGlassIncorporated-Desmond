# ClearGlass Agent Service

ClearGlassInc-only lawful risk-intelligence API service.

This service implements a private control plane for structured public-source and authorized defensive risk analysis. It is designed to support ClearGlass internal agents, executive risk briefings, source audit workflows, and blue-team command surfaces.

The service is limited to lawful public-source and authorized defensive enterprise security workflows.

---

## Hardened runtime

The service now includes:

- ClearGlass organization + API-key authentication with constant-time key comparison.
- Fail-closed startup behavior when no API keys are configured.
- Bounded in-process request-rate limiting; production deployments should additionally enforce gateway/WAF limits.
- Request `Content-Length` guard with a configurable 256 KiB default maximum.
- Optional `TrustedHostMiddleware` enforcement through `CLEARGLASS_ALLOWED_HOSTS`.
- Strict security response headers and `Cache-Control: no-store`.
- Non-root container execution with a dedicated UID.
- Container healthcheck against `/health`.
- Deterministic regression tests for authentication, security headers, private-target rejection, and rate limiting.

The service does not claim government certification or equivalence. These are application hardening controls intended for high-assurance engineering.

## Files

```text
services/clearglass_agent_service/
  main.py
  agent.py
  schemas.py
  security.py
  requirements.txt
  test_service.py
  Dockerfile
```

## Environment

Required:

```bash
export CLEARGLASS_AGENT_API_KEYS="generate-a-long-random-secret-outside-source-control"
```

Optional:

```bash
export CLEARGLASS_ALLOWED_ORGS="ClearGlassInc"
export CLEARGLASS_ALLOWED_ORIGINS="https://www.clearglassinc.com"
export CLEARGLASS_ALLOWED_HOSTS="agent.example.com"
export CLEARGLASS_AGENT_VERSION="0.2.0"
export CLEARGLASS_AGENT_RATE_LIMIT=60
export CLEARGLASS_AGENT_RATE_WINDOW_SECONDS=60
export CLEARGLASS_MAX_REQUEST_BYTES=262144
export CLEARGLASS_DISABLE_DOCS=false
export PORT=8080
```

Never place real API keys in source control, documentation, CI parameters, images, or logs. Use an approved secret manager or protected deployment context.

## Local validation

```bash
python -m pytest -q services/clearglass_agent_service/test_service.py
python -m compileall -q services/clearglass_agent_service
```

## Local Run

```bash
cd services/clearglass_agent_service
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cd ../..
uvicorn services.clearglass_agent_service.main:app --reload --host 127.0.0.1 --port 8080
```

Health check:

```bash
curl http://127.0.0.1:8080/health
```

Policy check:

```bash
curl http://127.0.0.1:8080/policy \
  -H "X-ClearGlass-Org: ClearGlassInc" \
  -H "X-ClearGlass-API-Key: change-this-long-random-key"
```

Signal packet:

```bash
curl -X POST http://127.0.0.1:8080/v1/signal \
  -H "Content-Type: application/json" \
  -H "X-ClearGlass-Org: ClearGlassInc" \
  -H "X-ClearGlass-API-Key: change-this-long-random-key" \
  -d '{
    "target": "ClearGlass vendor exposure review",
    "mission": "risk_brief",
    "domain": "vendor",
    "constraints": {
      "sources": ["public_web", "vendor_advisory", "news"],
      "time_window": "past_30_days",
      "jurisdiction": "US",
      "max_results": 10,
      "lawful_basis": "public-source enterprise risk analysis"
    }
  }'
```

## Docker Run

```bash
docker build -f services/clearglass_agent_service/Dockerfile -t clearglass-agent-service .
docker run --rm -p 8080:8080 \
  -e CLEARGLASS_AGENT_API_KEYS="change-this-long-random-key" \
  clearglass-agent-service
```

## Deployment

This is a containerized FastAPI service. Deploy it to an approved container platform such as Fly.io, AWS, Google Cloud, or Azure.

Production controls should include:

- Secret-manager backed API credentials with rotation.
- HTTPS/TLS termination and gateway/WAF rate limiting.
- Restricted allowed origins and, where applicable, allowed hosts.
- API gateway or SSO/JWT validation when integrating with broader enterprise identity.
- Structured, redacted audit logging.
- Persistent audit storage with retention policy.
- External source connectors only after source terms and lawful basis are reviewed.
- Immutable, digest-addressed deployment artifacts.
- Independent health and authorization verification after deployment.

The repository's CircleCI release path remains the deployment authority. Normal commits do not deploy; production requires its existing protected approval gates.

## API Shape

### `GET /health`

Unauthenticated service health. Security headers are still returned.

### `GET /policy`

Authenticated ClearGlass-only policy disclosure.

### `POST /v1/signal`

Authenticated structured signal packet analysis.

Returns an audit-ready `AgentReport` with executive summary, findings, evidence metadata, compliance note, and request audit context.

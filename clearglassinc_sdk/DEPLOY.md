# Deploying the ClearGlassInc Agent SDK

The SDK ships a production HTTP surface (`clearglassinc_sdk/server.py`) and a
container that runs it. This guide covers configuration, the safety posture,
and three deploy paths.

## Configuration

All configuration is environment variables — nothing is baked into the image.

| Variable | Default | Purpose |
|---|---|---|
| `CLEARGLASS_PROVIDER` | `fake` | `openai`, `anthropic`, or `fake` (offline, no key) |
| `CLEARGLASS_MODEL` | provider default | Model id passed to the provider |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | — | Provider credential (never commit these) |
| `CLEARGLASS_API_KEY` | unset | Bearer token required on mutating endpoints |
| `CLEARGLASS_ENV` | `development` | `production` **requires** `CLEARGLASS_API_KEY` |
| `CLEARGLASS_SESSION_DIR` | `/data/sessions` | Where persisted sessions are written |
| `CLEARGLASS_AGENT_NAME` | `ClearGlassInc Agent` | Default agent's display name |
| `CLEARGLASS_AGENT_INSTRUCTIONS` | generic | Default agent's system prompt |
| `PORT` | `8000` | Listen port |

### Fail-closed auth

Auth mirrors the commerce control plane's posture:

- **No `CLEARGLASS_API_KEY`** → open. Fine for local dev and the offline fake
  provider; never for a public deploy.
- **`CLEARGLASS_API_KEY` set** → `/run`, `/run/stream`, `/sessions`, and
  `/traces` require `Authorization: Bearer <key>`. `/health` and `/ready`
  stay open so load balancers can probe them.
- **`CLEARGLASS_ENV=production` with no key** → the app **refuses to start**.
  A misconfigured production deploy fails loudly instead of silently serving
  an unauthenticated agent.

## Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/health` | open | Liveness — 200 whenever the process is up |
| GET | `/ready` | open | Readiness — provider configured? agents loaded? |
| POST | `/run` | gated | Run a turn, return the final answer + usage |
| POST | `/run/stream` | gated | Same, streamed as Server-Sent Events |
| GET | `/sessions` | gated | List persisted session ids |
| DELETE | `/sessions/{id}` | gated | Delete a persisted session |
| GET | `/traces` | gated | Recent spans, for debugging |

Error mapping: guardrail violations and schema failures → `422`, step-budget
exhaustion → `504`, tool failures → `500`.

```bash
curl -sS localhost:8000/run \
  -H "Authorization: Bearer $CLEARGLASS_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Summarize today'\''s orders","session_id":"ops-1"}'
```

## Path 1 — Docker Compose (fastest)

```bash
cd clearglassinc_sdk
docker compose up --build          # offline fake provider, no key needed
```

Go live by exporting credentials first:

```bash
export CLEARGLASS_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
export CLEARGLASS_API_KEY="$(openssl rand -hex 32)"
export CLEARGLASS_ENV=production
docker compose up --build -d
```

Sessions live on the `agent-sessions` named volume, so they survive restarts.

## Path 2 — Container registry → any host

```bash
docker build -t clearglassinc-sdk:0.2.0 clearglassinc_sdk
docker run -d -p 8000:8000 \
  -e CLEARGLASS_ENV=production \
  -e CLEARGLASS_API_KEY="$KEY" \
  -e CLEARGLASS_PROVIDER=anthropic \
  -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  -v clearglass-sessions:/data/sessions \
  clearglassinc-sdk:0.2.0
```

The image runs as non-root (uid 10001), carries a `HEALTHCHECK`, and installs
only prebuilt wheels in the runtime stage.

## Path 3 — Render / Fly / any PaaS

Point the platform at `clearglassinc_sdk/Dockerfile`, set the environment
variables above as secrets, and configure the health check to `GET /health`.
Attach a persistent disk at `/data/sessions` if you want sessions to survive
redeploys — otherwise set `CLEARGLASS_SESSION_DIR` to a `tmpfs` path and treat
sessions as ephemeral.

## Pre-deploy checklist

```bash
cd clearglassinc_sdk
pip install -e ".[dev,server]"
ruff check .                       # lint
python -m pytest -q                # 160 tests, no network needed
python examples/advanced_agent.py  # exercises every advanced feature
docker build -t clearglassinc-sdk:test .
```

The `Agent SDK CI` workflow (`.github/workflows/agent-sdk-ci.yml`) runs all of
this on every PR touching `clearglassinc_sdk/**`, plus a container build and a
live `/health` probe against the running image.

## Operational notes

- **Scaling**: the app is stateless apart from the session directory. Run
  several replicas behind a load balancer and put sessions on shared storage
  (or swap `FileSessionStore` for a `SessionStore` backed by your database).
- **Observability**: every run emits a span tree. `/traces` is the built-in
  debug view; for real telemetry attach a `JSONLExporter` (ship the file) or
  implement `SpanExporter` against your backend.
- **Cost control**: `RunResponse.usage` reports per-run token counts — meter
  it before it reaches your invoice.
- **Timeouts**: provider clients default to a 60s timeout and retry transient
  failures three times with jittered backoff; tune via `RetryPolicy` on the
  `Agent`.

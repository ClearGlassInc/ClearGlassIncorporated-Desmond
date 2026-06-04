# PERCIVAL · Autostore — Control Plane Monorepo

Production shape for the agentic ecommerce architecture: decisioning,
execution, and experience cleanly separated, with **pricing, refunds,
inventory, and ad spend inside hard rails**.

```
event → ingest → context (Store) → policy check → decision
                          → approval (if ESCALATE) → execute → log → learn
```

The AI may **recommend**; only the control plane can **authorize**. Workers
are dumb-by-design — they execute only validated packets emitted here.

## Layout

```
apps/autostore/
├── db/migrations/001_init.sql        — canonical Postgres schema
├── control_plane/                    — FastAPI surface + stdlib-testable core
│   ├── autostore/{models,store,policy,engine,audit,app}.py
│   ├── tests/test_engine.py          — 14 trust-loop tests
│   ├── Dockerfile · requirements.txt
├── cockpit/                          — Next.js (App Router) read-first cockpit
│   ├── app/{layout,page,approvals,audit}.tsx
│   ├── lib/api.ts · globals.css · package.json
├── deploy/docker-compose.yml         — Postgres + Redis + control plane + cockpit
└── README.md
```

## Run the stack

```bash
cd apps/autostore/deploy
docker compose up --build
# control plane:  http://localhost:8000/healthz · /docs (FastAPI)
# cockpit:        http://localhost:3000
```

## Try it

```bash
# in-policy price change — ALLOW, executed
curl -s -X POST localhost:8000/v1/events -H content-type:application/json \
  -d '{"type":"price_recommendation","payload":{"sku":"SKU-RIDGE-01","new_price_cents":7900}}'

# deep discount but ABOVE floor — ESCALATE (lands in /v1/approvals/pending and the cockpit)
# Default seed: SKU-RIDGE-01 price 8900, floor 4500, max_discount 30% (auto-allow above 6230)
curl -s -X POST localhost:8000/v1/events -H content-type:application/json \
  -d '{"type":"price_recommendation","payload":{"sku":"SKU-RIDGE-01","new_price_cents":5500}}'

# below floor — DENY (4500 floor)
curl -s -X POST localhost:8000/v1/events -H content-type:application/json \
  -d '{"type":"price_recommendation","payload":{"sku":"SKU-RIDGE-01","new_price_cents":4000}}'

# tamper-evident audit ledger
curl -s localhost:8000/v1/audit | jq '.[-3:]'
```

## Guardrails (every rule reconciles against the Store)

| Event | Guard | Outcomes |
|---|---|---|
| `price_recommendation` | floor = `min_price_cents`; max discount = `policy.max_discount_pct` | ALLOW · ESCALATE (deep discount) · DENY (below floor / unknown SKU) |
| `refund_request` | ≤ `policy.refund_auto_max_cents` auto; > order total denied | ALLOW · ESCALATE · DENY |
| `ad_spend_request` | per-day cap via `Store.ad_spend_today_cents()` | ALLOW · DENY (would exceed cap) |
| `inventory_event` | reconcile against canonical inventory; never negative | ALLOW · DENY |

## Tests

```bash
cd apps/autostore/control_plane
python -m pytest -q     # 14 passed
python -m ruff check autostore tests
```

## Build order followed
Postgres schema → FastAPI control plane → event ingestion API → worker queue
hooks (Redis up; consumer is a thin executor) → guardrails → audit ledger UI
→ Next.js cockpit. Anything further (assistant advisory layer, write-side
cockpit) plugs in **after** the control plane has proven stable.

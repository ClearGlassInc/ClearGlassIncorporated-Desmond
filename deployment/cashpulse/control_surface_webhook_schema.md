# Control Surface — n8n Webhook Payload Schema

This contract defines the **only** payloads the public `control-surface.html`
dashboard expects to receive. The dashboard is strictly read-only; n8n is the
event ingress and normalization layer.

- **Ingress:** one n8n `Webhook` node per event group
- **Egress:** static JSON served from a CDN/Pages-friendly URL (or a small
  edge function) and read by `control-surface.html`
- **Security:** dashboard fetches public, non-sensitive aggregates only.
  Signed HMAC + allowlisted IP enforced at the n8n webhook node.

---

## 1 · Universal event envelope

Every event posted to n8n MUST conform to:

```json
{
  "type":      "metrics.update | activity.append | health.ping | alert.raise | pipeline.update | run.append",
  "title":     "string — short human label, <= 80 chars",
  "status":   "ok | warn | bad",
  "value":     "string|number — optional, depends on type",
  "timestamp": "ISO-8601 UTC, e.g. 2026-06-14T05:18:40Z",
  "source":    "string — emitter id, e.g. cashpulse-bot, github-actions, plaid-sync",
  "severity":  "info | low | medium | high | critical",
  "payload":   { /* type-specific body, see below */ }
}
```

### Required fields by type

| type              | required `payload` keys                                  |
|-------------------|----------------------------------------------------------|
| `metrics.update`  | `label`, `value`, `delta`, `pct` (0–100)                 |
| `activity.append` | `detail`                                                 |
| `health.ping`     | `uptime`, `detail`                                       |
| `alert.raise`     | `detail`                                                 |
| `pipeline.update` | `label`, `value`                                         |
| `run.append`      | `detail`                                                 |

---

## 2 · Endpoint contract (dashboard side)

`control-surface.html` performs six independent GETs in parallel and falls
back to local sample data if any fail. Each endpoint returns a JSON **array**
(except `health`, which returns an **object**).

| Endpoint               | Returns                                  | Cache hint   |
|------------------------|------------------------------------------|--------------|
| `/api/cg/metrics`      | `MetricCard[]`                           | 30 s         |
| `/api/cg/health`       | `HealthSnapshot`                         | 15 s         |
| `/api/cg/activity`     | `ActivityItem[]` (newest first, ≤ 50)    | 10 s         |
| `/api/cg/pipeline`     | `PipelineCounter[]`                      | 60 s         |
| `/api/cg/alerts`       | `AlertItem[]`                            | 10 s         |
| `/api/cg/runs`         | `RunItem[]` (newest first, ≤ 25)         | 30 s         |

All responses MUST set:
- `Content-Type: application/json; charset=utf-8`
- `Access-Control-Allow-Origin: https://clearglassinc.github.io`
- `Cache-Control: no-store` (the dashboard refreshes itself)

### Shapes

```ts
type MetricCard = {
  label: string;       // "Active agents"
  value: string;       // "47" or "$14.8k"
  delta: string;       // "+3 this hour"
  pct:   number;       // 0..100 — drives the gradient bar
};

type HealthSnapshot = {
  status: "Operational" | "Degraded" | "Down";
  uptime: string;      // "99.94%"
  detail: string;      // "All core services reachable"
};

type ActivityItem = {
  title:  string;
  status: "ok" | "warn" | "bad";
  detail: string;
  time:   string;      // "12:41" — client display
  timestamp?: string;  // ISO-8601 — preferred for sorting
};

type PipelineCounter = {
  label: string;       // "New leads"
  value: string;       // "142"
};

type AlertItem = {
  title:  string;
  status: "warn" | "bad";
  detail: string;
};

type RunItem = {
  title:  string;      // "n8n workflow"
  status: "ok" | "warn" | "bad";
  detail: string;      // "Daily ingest completed"
  time:   string;
  timestamp?: string;
};
```

---

## 3 · n8n ingress → projection

Each webhook node accepts the universal envelope and projects it into the
right egress shape. Recommended n8n layout:

```
Webhook (POST /cg/event)
  → Function: validate envelope (reject if schema fails)
  → Switch on $json.type
      ├─ metrics.update  → Upsert Supabase row in cg_metrics
      ├─ activity.append → Insert into cg_activity (ring-buffer 50)
      ├─ health.ping     → Replace cg_health single row
      ├─ alert.raise     → Insert into cg_alerts (auto-expire 24h)
      ├─ pipeline.update → Upsert into cg_pipeline by label
      └─ run.append      → Insert into cg_runs (ring-buffer 25)
  → Audit: write to bot_actions (see deployment/cashpulse/audit_log.sql)
  → Respond 202
```

A second n8n cron flow exports each table to a static JSON file in S3 / GitHub
Pages every 10 s, served behind the endpoints in §2.

---

## 4 · Sample envelopes

### metrics.update
```json
{
  "type":"metrics.update",
  "title":"Active agents",
  "status":"ok",
  "timestamp":"2026-06-14T05:18:40Z",
  "source":"orchestrator",
  "severity":"info",
  "payload":{"label":"Active agents","value":"47","delta":"+3 this hour","pct":68}
}
```

### activity.append
```json
{
  "type":"activity.append",
  "title":"Webhook received",
  "status":"ok",
  "timestamp":"2026-06-14T05:18:40Z",
  "source":"n8n",
  "severity":"info",
  "payload":{"detail":"n8n event normalized and queued"}
}
```

### alert.raise
```json
{
  "type":"alert.raise",
  "title":"Stale metrics endpoint",
  "status":"warn",
  "timestamp":"2026-06-14T05:18:40Z",
  "source":"watchdog",
  "severity":"medium",
  "payload":{"detail":"No update in 16 minutes."}
}
```

---

## 5 · Validation rules

The n8n validation Function MUST reject the request (400) when any of:
- `type` is not in the allowlist
- `status` not in `{ok, warn, bad}`
- `severity` not in `{info, low, medium, high, critical}`
- `timestamp` is not ISO-8601 UTC
- `payload` is missing keys required for the given `type`
- envelope size exceeds 8 KB
- HMAC signature header `X-CG-Signature` does not verify against the shared
  secret (rotate every 30 days)

All rejections are written to `bot_actions` with `status='failed'` and
`action='webhook_rejected'`.

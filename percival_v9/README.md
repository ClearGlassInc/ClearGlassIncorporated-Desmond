# Percival v9 — Executable Scaffold

Runnable core of the blueprint in `docs/PERCIVAL_V9_ARCHITECTURE.md`.
Stdlib-only Python (per repo convention for governance modules), tested by the
root `Python Tests` CI gate via `tests/test_percival_v9_policy.py`.

> The blueprint names the tree `/percival-v9`; this package is `percival_v9/`
> because hyphenated directories are not importable Python packages.

| Module | Blueprint component | Guarantee |
|---|---|---|
| `internal/policy/engine.py` | Policy Governor (OPA sidecar contract) | Deny-by-default; high/critical risk gated on single-use approvals; **fail-closed** (deny-all) if the ledger can't record a decision |
| `internal/audit.py` | Audit Ledger (Kafka + S3 WORM contract) | Append-only, SHA-256 hash-chained; `verify()` detects any tamper |
| `internal/graph/state.py` | LangGraph state transitions + Escalation Gate | `EXECUTED` reachable only via `APPROVED`; illegal edges raise |
| `cmd/governor.py` | `cmd/governor` service entry point | OPA-compatible HTTP surface (`POST /v1/data/percival/authz/allow`, `GET /healthz`); malformed input / unknown routes **deny**, never grant |
| `policies/capabilities.json` | `deploy/policies` capability schema | Versioned, deny-by-default grants; loader rejects unknown schema versions |
| `policies/authz.rego` | OPA rego bundle | Same allow/deny semantics as the Python governor, portable to the sidecar (not exercised in CI — no OPA binary in the minimal env) |

Deploy layer authored under `deploy/` (K8s manifests, Terraform skeleton,
governor-gated Temporal worker) — **authored, not applied**; see
`deploy/README.md`. Provisioning (`terraform apply` / `kubectl apply`) remains
gated on cloud credentials + explicit approval, per the blueprint's own
Escalation Gate. The Envoy/Istio gateway is the one remaining unwritten piece.

```bash
python -m pytest tests/test_percival_v9_policy.py tests/test_percival_v9_service.py -q
python -m percival_v9.cmd.governor --self-check   # offline governance gate
python -m percival_v9.cmd.governor --port 8181    # serve the OPA-compatible API
```

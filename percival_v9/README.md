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

Not yet implemented (each gated on approval, per the blueprint): `cmd/` service
entry points, Temporal workers, OPA rego bundles, `deploy/terraform`.

```bash
python -m pytest tests/test_percival_v9_policy.py -q
```

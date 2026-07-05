# Agent & Bot System

ClearGlass runs a **static-compatible agent architecture**: agents are defined as
structured config (`agent.json`), documented prompts (`system_prompt.md`), and
tool schemas (`tool_schema.json`), and are executed by Python bots under
`bots/`/`scripts/` that are driven by GitHub Actions workflows. There is no
always-on backend for the public site — coordination happens through committed
config, scheduled workflows, and an append-only audit trail. The only governed
runtime backend is the commerce control plane (`clearglass-commerce/`), whose
safety model is described in `CLAUDE.md`.

## Where things live

| Path | Role |
|---|---|
| `agents/*/agent.json` | Per-agent definition: name, role, model recommendation, offerings, prompt path |
| `agents/*/system_prompt.md` | The agent's operating prompt |
| `agents/*/tool_schema.json` | Structured tool contract (where the agent uses tools) |
| `bots/`, `scripts/` | Python automation that runs the work (stdlib-first, testable) |
| `sentinel/` | Keyless, stdlib-only, fail-closed named-agent index (PERCIVAL, SENTINEL, AEGIS, PFAS, Agent Mesh) — see `sentinel/PERCIVAL_AGENTS.md` |
| `.github/workflows/` | Schedulers/triggers that invoke the bots and enforce gates |
| `tests/` | 423 tests covering the bots and governance |

## Defined agents (`agents/`)

- `clearglass_agent_os` — top-level operator OS prompt
- `clearglass_executive` — executive briefing / decisioning
- `clearglass_marketing_command` — marketing content (see `bot_ecosystem.md`)
- `clearglass_side_store` — storefront operations agent
- `artemis_service_agent` — cybersecurity sales / qualification
- `guardian_v5` — Guardian product agent (with `tool_schema.json`)
- `smb_cyber_trust_kit` — SMB trust-kit agent (with `tool_schema.json`)
- `workflow_repair` — repository/workflow self-repair agent

## Coordinated roles → real artifacts

The prompt's ten coordinating roles map onto existing, tested components rather
than a new backend:

| Role | Implemented by |
|---|---|
| **Intake** | `agent.yml` (Claude Code action) + `scripts/repo_audit.py` classify/route incoming tasks |
| **Planner** | `agents/workflow_repair/` + `.github/workflows/workflow-repair-agent.yml` break work into safe steps |
| **Executor** | Bots under `bots/`/`scripts/` invoked by their workflows; commerce actions gated by `clearglass-commerce/control-plane/app/governance.py` |
| **Auditor** | `scripts/site_reliability_audit.py`, `scripts/workflow_doctor.py`, `scripts/access_control_audit.py`, `.github/workflows/repo-audit.yml`, `security.yml`, `ip-protection-scan.yml` |
| **Logger** | Append-only `events` ledger (`clearglass-commerce/.../app/audit.py`); workflow run logs; `operations/` reports |
| **Deployment** | `pages.yml` (site), `commerce-deploy.yml` (backend); readiness validated by CI |
| **Marketing** | `agents/clearglass_marketing_command/`, `scripts/marketing_command_layer.py`, `content-pipeline.yml` |
| **Revenue** | `agents/clearglass_side_store/`, `scripts/store_sync.py`, `store.html`/`pricing.html` CTAs, commerce control plane |
| **Compliance** | `compliance-evidence.yml`, `policy-gate.yml`, `percival-policy-gate.yml`, `legal/` pages |
| **Monitoring** | `health-monitor.yml`, `defender-watch.yml`, `scripts/workflow_doctor.py` |

## Safety invariants

- **Governed execution.** In the commerce OS, every proposed action is scored
  0–100 and routed read-only → draft → **human approval** → execute. High/critical
  actions (pricing, payment, refunds, fulfillment, mass outbound) are blocked
  until an `approvals` row is `approved`. Do not add a code path that bypasses
  this — `tests/test_governance.py` and the daily-loop self-check fail by design.
- **Fail-closed.** `sentinel/` agents are keyless and stdlib-only so they run in
  minimal CI and refuse rather than guess.
- **Never fabricate** inventory, reviews, sales, or urgency. Log every material
  action.

## Extending the system

1. Add a new agent as `agents/<name>/agent.json` + `system_prompt.md`
   (+ `tool_schema.json` if it uses tools).
2. Implement the work as a testable Python bot in `bots/` or `scripts/` and add a
   test under `tests/`.
3. Wire a trigger in `.github/workflows/` with explicit least-privilege
   `permissions:` and a `workflow_dispatch` trigger.
4. Keep money-movement / pricing / outbound behind the commerce governance layer.
5. Run `pytest tests/ -q`, `ruff check .`, and
   `python scripts/site_reliability_audit.py` before pushing.

---

## ClearGlassInc Artemis coordinated company-agent registry

The current static-compatible command-system registry is maintained at `agents/company_system/agent_registry.json`. It connects the required Intake, Planner, Executor, Auditor, Logger, Deployment, Marketing, Revenue, Compliance, and Monitoring agents through explicit routing rules and guardrails.

Validation command:

```bash
python scripts/validate-site
```

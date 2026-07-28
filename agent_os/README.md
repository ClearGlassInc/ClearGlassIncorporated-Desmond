# ClearGlass Autonomous Agent OS v8.0 — Runtime

Runnable, stdlib-only, fail-closed implementation of the agent definition in
[`agents/clearglass_agent_os/`](../agents/clearglass_agent_os/). The definition
is the *contract*; this package is the *executable governance runtime* behind it.

## Modules

| Module | Responsibility |
|--------|----------------|
| `governance.py` | Risk scoring (0–100) + approval gating. The single auto-execute vs. escalate decision point. Fails closed. |
| `roster.py` | The thirteen specialist sub-agents as data (responsibilities + produced artifacts). |
| `planning.py` | Objective → executable DAG: parallel waves (Kahn) + critical-path estimate. Cycles fail closed. |
| `executive.py` | Expected-value strategy ranking + priority queue (`p·value − cost − risk·value`). |
| `intelligence.py` | Multi-source cross-reference; single-source cap, contradiction detection, min-confidence aggregation. |
| `memory.py` | Ranked persistent recall (`accuracy × recency × authority`); missing memory reported as missing. |
| `recovery.py` | Root-cause classification + bounded exponential-backoff retry + escalation. |
| `state_machine.py` | ARTEMIS // FAWL incident lifecycle transitions with attribution, evidence, policy decisions, correlation IDs, and tamper-evident audit entries. |
| `learning.py` | Outcome capture, deterministic metrics, lessons, optimization opportunities. |
| `audit.py` | Append-only, tamper-evident SHA-256 hash-chain ledger with `verify()`. |
| `orchestrator.py` | The executive loop. Composes the above into the mandated 13-field `MissionReport`. No side effects. |
| `self_check.py` | Governance + structural + audit self-check and a demo executive report. CI entrypoint. |
| `__main__.py` | `python -m agent_os` — end-to-end governed demo mission as JSON. |

## Run it

```bash
python -m agent_os                     # end-to-end governed demo mission
python -m agent_os.self_check          # human-readable self-check + report
python -m agent_os.self_check --json   # machine-readable
pytest tests/test_agent_os.py tests/test_agent_os_advanced.py tests/test_agent_os_state_machine.py -q
```

## Safety invariant (enforced in code)

`read-only analysis → draft → human approval → execution`

The self-check **fails the build** if any of these can auto-execute: an
always-escalate action (money, production deploy, access-control change, data
deletion, secret rotation, mass outbound); an unknown action; an action whose
confidence is unavailable; a conclusion with no supporting evidence. It also
fails if the audit chain does not detect tampering. Incident recovery workflows
are constrained by `state_machine.py`: an action cannot jump from detection to
execution, terminal states cannot be reopened by automation, and every accepted
transition requires actor, evidence, policy decision, correlation ID, timestamp,
and reason before being appended to the audit hash chain.

Mission confidence is reported as the **minimum** observed signal — the OS never
inflates certainty. The orchestrator performs no external side effects; it
decides and reports, leaving gated actions behind the human approval gate.

## CI

- **Python Tests** (`ci.yml`) runs `pytest tests/`, which includes both
  `tests/test_agent_os.py` and `tests/test_agent_os_advanced.py`.
- **Agent OS Self-Check** (`agent-os.yml`) runs the unit tests plus the
  governance/audit self-check on a schedule, on PRs touching `agent_os/**`, and
  on demand.

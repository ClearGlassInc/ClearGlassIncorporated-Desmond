# ClearGlass Autonomous Agent OS v8.0 — Runtime

Runnable, stdlib-only, fail-closed implementation of the agent definition in
[`agents/clearglass_agent_os/`](../agents/clearglass_agent_os/). The definition
is the *contract*; this package is the *executable governance skeleton* behind
it.

## Modules

| Module | Responsibility |
|--------|----------------|
| `governance.py` | Risk scoring (0–100) + approval gating. The single decision point for auto-execute vs. escalate. Fails closed. |
| `roster.py` | The thirteen specialist sub-agents as data (responsibilities + produced artifacts). |
| `planning.py` | Objective → executable DAG: parallel waves (Kahn) + critical-path estimate. Cycles fail closed. |
| `orchestrator.py` | The executive loop. Produces the mandated 13-field `MissionReport`; routes every proposed action through governance. No side effects. |
| `self_check.py` | Governance + structural self-check and a demo executive report. CI entrypoint. |

## Run it

```bash
# Human-readable governance self-check + executive report
python -m agent_os.self_check

# Machine-readable
python -m agent_os.self_check --json

# Tests (also run by the "Python Tests" CI job via pytest tests/)
pytest tests/test_agent_os.py -q
```

## Safety invariant (enforced in code)

`read-only analysis → draft → human approval → execution`

The self-check **fails the build** if any of these can auto-execute:

- an always-escalate action (money, production deploy, access-control change,
  data deletion, secret rotation, mass outbound);
- an unknown action;
- an action whose confidence is unavailable;
- a conclusion with no supporting evidence.

Mission confidence is reported as the **minimum** observed signal — the OS never
inflates certainty. The orchestrator itself performs no external side effects;
it decides and reports, leaving gated actions behind the human approval gate.

## CI

- **Python Tests** (`ci.yml`) runs `pytest tests/`, which includes
  `tests/test_agent_os.py`.
- **Agent OS Self-Check** (`agent-os.yml`) runs the unit tests plus the
  governance self-check on a schedule, on PRs touching `agent_os/**`, and on
  demand.

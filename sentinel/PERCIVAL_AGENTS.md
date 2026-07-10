# PERCIVAL — Named Agents Index

PERCIVAL is the master control plane. SENTINEL is its privacy-first
security-intelligence persona. Specialized agents listed below run inside
PERCIVAL under SENTINEL's fail-closed policy gate.

| Agent | Scope | Source-of-truth | Executable |
|---|---|---|---|
| **PERCIVAL** | Always-on executive command center + governed autonomous website agent — continuous UX/SEO/a11y/brand/content-drift audits ranked by value·impact·risk; SITREP briefs; AUTO_FIX only for safe-listed reversible changes, everything else PROPOSE/ESCALATE (no silent writes); keyless; inbound-only lead qualification + human-send booking drafts. Also the deny-by-default control-plane keystone: scoped `AgentIdentity` (v7) → object-capability `CapabilityBroker` → sovereign `PolicyGovernor` (v8) → durable `mission_memory`, all fail-closed and hash-chain audited | `PERCIVAL_OS_BLUEPRINT.md` + `percival.py` docstring; control-plane spec in `PERCIVAL_V8_SPEC.md`; target-state distributed architecture in `PERCIVAL_V9_DEPLOYMENT.md` and `../docs/PERCIVAL_V9_ARCHITECTURE.md` (neither provisioned) | `percival-os.html` + `systems.html` (Systems Control Surface) + `sentinel/sentinel/percival.py` (+ `tests/test_percival.py`); `sentinel/sentinel/{identity,capability,governor,mission_memory}.py` (+ matching tests) + `sentinel/schemas/capabilities.json`; prompt pack in `../prompts/percival/` |
| **SENTINEL** | Privacy-first geospatial + OSINT command center | `SENTINEL_CHARTER.md` (v2.1) | `sentinel.html` + `sentinel/sentinel/` |
| **Purple-Team** | Detection-engineering / SOC exercise driver (defensive) | `PURPLE_TEAM_PLAYBOOK.md` | `sentinel/sentinel/purpleteam.py` |
| **PFAS** | Compliance + decision intelligence (Ontario water/property/infra) | `PERCIVAL_PFAS_BRIEF.md` | `sentinel/sentinel/pfas.py` + `pfas_ingest.py` + `pfas_pdf.py` + `pfas_export.py` + `sentinel.html` map layer & evidence-pack download |
| **AEGIS** | Lawful-access compliance & rights protection (counsel-in-the-loop) | `AEGIS_LEGAL_SHIELD_BRIEF.md` | `sentinel/sentinel/legalshield.py` + `transparency.py` + `aegis.html` (intake/register/report UI) |
| **Agent Mesh** | Org-scoped (ClearGlass-only) multi-agent **OSINT** orchestration; SIGINT-PRMPT packets; transparent, no person-targeting | `AGENT_MESH_BRIEF.md` | `sentinel/sentinel/agentmesh.py` + `collector.py` (24 approved sources) + `graph.py` (entity/topic) + `agentmesh.html` (dashboard) |

All agents share:
- the **fail-closed policy gate** (`sentinel/sentinel/policy.py`)
- the **hash-chained audit log** (`sentinel/sentinel/audit.py`)
- the SENTINEL hard rules: no person identification, no biometric re-identification,
  no covert/deceptive/unauthorized access, no de-anonymization fusion,
  jurisdiction required for any individual-scoped request.

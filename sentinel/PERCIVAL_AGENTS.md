# PERCIVAL — Named Agents Index

PERCIVAL is the master control plane. SENTINEL is its privacy-first
security-intelligence persona. Specialized agents listed below run inside
PERCIVAL under SENTINEL's fail-closed policy gate.

| Agent | Scope | Source-of-truth | Executable |
|---|---|---|---|
| **PERCIVAL** | Always-on executive command center | `PERCIVAL_OS_BLUEPRINT.md` | `percival-os.html` + `sentinel/` |
| **SENTINEL** | Privacy-first geospatial + OSINT command center | `SENTINEL_CHARTER.md` (v2.1) | `sentinel.html` + `sentinel/sentinel/` |
| **Purple-Team** | Detection-engineering / SOC exercise driver (defensive) | `PURPLE_TEAM_PLAYBOOK.md` | `sentinel/sentinel/purpleteam.py` |
| **PFAS** | Compliance + decision intelligence (Ontario water/property/infra) | `PERCIVAL_PFAS_BRIEF.md` | `sentinel/sentinel/pfas.py` + `pfas_ingest.py` + `pfas_pdf.py` + `pfas_export.py` + `sentinel.html` map layer & evidence-pack download |
| **AEGIS** | Lawful-access compliance & rights protection (counsel-in-the-loop) | `AEGIS_LEGAL_SHIELD_BRIEF.md` | `sentinel/sentinel/legalshield.py` + `transparency.py` + `aegis.html` (intake/register/report UI) |

All agents share:
- the **fail-closed policy gate** (`sentinel/sentinel/policy.py`)
- the **hash-chained audit log** (`sentinel/sentinel/audit.py`)
- the SENTINEL hard rules: no person identification, no biometric re-identification,
  no covert/deceptive/unauthorized access, no de-anonymization fusion,
  jurisdiction required for any individual-scoped request.

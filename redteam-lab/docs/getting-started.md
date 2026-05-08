# Getting Started — ClearGlass Detection Forge

## Before You Run Anything: Read This

ClearGlass Detection Forge is an authorization-only platform. Every scenario
requires a completed, signed Authorization to Test (ATT) document before
execution. No exceptions.

**Start here:** [AUTHORIZATION_TEMPLATE.md](../AUTHORIZATION_TEMPLATE.md)

---

## What This Platform Does

Detection Forge helps you answer one question precisely:

> *"When an attacker does X, does our SIEM/EDR/NDR actually alert?"*

It does this by emitting the same telemetry artifacts a real attack would
generate — process events, network connections, registry changes, log entries
— without deploying real malware, capturing real credentials, or causing
any system damage.

---

## System Requirements

### Control Node (where you run clearforge CLI)

- Python 3.11+
- Docker 24+ (for containerized lab environments)
- 4GB RAM minimum
- Network access to target environment

### Target Environment

- Windows: Server 2019+ or Windows 10 22H2+
- Sysmon 15+ deployed and configured
- Windows Security Event Log → SIEM forwarding active
- EDR agent deployed (if testing EDR detections)

### SIEM Connectivity

Detection Forge validates results by querying your SIEM for expected alerts.
Supported:

| SIEM | API Support | Notes |
|------|-------------|-------|
| Splunk Enterprise | ✓ Full | REST API, search jobs |
| Microsoft Sentinel | ✓ Full | Azure Monitor Logs API |
| Elastic SIEM | ✓ Full | Elasticsearch API |
| IBM QRadar | ✓ Partial | Ariel Query API |
| Generic Syslog | ✓ Passive | No auto-validation |

---

## Installation

```bash
# Clone the repo
git clone https://github.com/ClearGlassInc/ClearGlassInc.github.io.git
cd ClearGlassInc.github.io/redteam-lab

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure
cp lab-configs/clearforge.config.example.yml clearforge.config.yml
```

---

## Configuration

Edit `clearforge.config.yml`:

```yaml
authorization:
  token: ""              # ATT token — generated after signing ATT document
  document_ref: ""       # ATT document reference number

environment:
  name: "lab-01"
  targets:
    - host: "192.168.100.10"
      role: "windows-endpoint"
      platform: "windows"
    - host: "192.168.100.20"
      role: "domain-controller"
      platform: "windows"

siem:
  type: "splunk"         # splunk | sentinel | elastic | qradar
  host: "https://splunk.internal:8089"
  token: ""              # SIEM API token
  index: "main"
  alert_wait_seconds: 120

telemetry:
  sysmon_enabled: true
  network_capture: true
  edr_agent: ""          # crowdstrike | defender | sentinelone | none

reporting:
  org_name: "Your Organization"
  logo_path: ""
  output_dir: "./reports"
```

---

## Your First Run

### 1. Validate configuration

```bash
python clearforge.py validate-config
```

Expected output:
```
✓ Authorization token: valid (scope: lab-01, expires: 2026-12-31)
✓ Environment: lab-01 (2 targets reachable)
✓ SIEM: Splunk connected (index: main)
✓ Telemetry: Sysmon active on all targets
Configuration valid — ready to run scenarios
```

### 2. List available scenarios

```bash
python clearforge.py scenarios list
python clearforge.py scenarios list --tactic lateral-movement
python clearforge.py scenarios list --technique T1550
```

### 3. Dry run (no emulation, validates pipeline only)

```bash
python clearforge.py run --scenario T1550.002 --dry-run
```

### 4. Execute a single scenario

```bash
python clearforge.py run \
  --scenario T1550.002 \
  --env lab-01 \
  --wait 120
```

### 5. Run a full assessment session

```bash
python clearforge.py session start \
  --playbook playbooks/purple-team/standard-assessment.yml \
  --env lab-01
```

### 6. Generate reports

```bash
python clearforge.py report \
  --session SES-2026-0001 \
  --format all
```

---

## Understanding Results

Each scenario produces one of three results:

| Result | Meaning | Action |
|--------|---------|--------|
| **DETECT** | Alert fired within window with useful IOCs | Document ✓, move to next scenario |
| **PARTIAL** | Alert fired but incomplete (wrong severity, missing fields, delayed) | Tune rule, re-test |
| **MISS** | No alert within window | Investigate pipeline → generate rule → re-test |

**If MISS:** First check whether the raw telemetry arrived at your SIEM.
- Telemetry arrived, no rule fired → **detection gap** (generate Sigma rule)
- Telemetry never arrived → **collection gap** (fix Sysmon/agent config first)

---

## Generating Detection Rules

For every MISS or PARTIAL, Detection Forge auto-generates a Sigma rule:

```bash
python clearforge.py rules generate \
  --session SES-2026-0001 \
  --filter miss \
  --output-format sigma,splunk,sentinel
```

---

## Getting Help

- **Documentation:** `docs/` directory
- **Commercial support:** [Desmondotieno@icloud.com](mailto:Desmondotieno@icloud.com)
- **Product page:** [clearglassinc.github.io/detection-forge.html](https://clearglassinc.github.io/detection-forge.html)
- **Issues:** GitHub Issues (bugs only — no security research requests)

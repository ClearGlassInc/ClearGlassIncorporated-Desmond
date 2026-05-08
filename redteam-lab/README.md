# ClearGlass Detection Forge
### Adversary Simulation & Detection Validation Platform

[![Authorization Required](https://img.shields.io/badge/USE-Authorization%20Required-red?style=flat-square)](./AUTHORIZATION_TEMPLATE.md)
[![ATT&CK Version](https://img.shields.io/badge/ATT%26CK-v14-orange?style=flat-square)](https://attack.mitre.org)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](./LICENSE)
[![CI](https://img.shields.io/badge/CI-Scenario%20Validation-green?style=flat-square)](.github/workflows/validate-scenarios.yml)

> **Authorization-only platform.** Every scenario requires a signed Authorization to Test (ATT) document before execution. This platform contains no live malware, no credential theft tools, no destructive payloads, and no unauthorized access capabilities. See [AUTHORIZATION_TEMPLATE.md](./AUTHORIZATION_TEMPLATE.md).

---

## What Is This?

ClearGlass Detection Forge is an enterprise **adversary simulation and detection validation platform** built for:

- **Security teams** validating whether their SIEM, EDR, and NDR actually detect the attacks they claim to
- **Purple teams** running structured red/blue collaboration exercises
- **Detection engineers** generating and tuning Sigma rules, Splunk SPL, and Sentinel KQL
- **Compliance teams** producing audit evidence for PCI DSS 4.0, SOC 2, ISO 27001, and NIST CSF 2.0
- **SOC analysts** training on realistic adversary telemetry against their own tooling

**What it is not:** an offensive toolkit, a malware repository, or a penetration testing framework for use against systems you do not own.

---

## Authorization Requirement

> **STOP. Read this before running anything.**

This platform requires written authorization before any scenario execution. The repository includes a mandatory [Authorization to Test (ATT) template](./AUTHORIZATION_TEMPLATE.md).

**Required before any execution:**
1. Complete and sign the ATT document with all stakeholders
2. Define scope: target environment, IP ranges, time window, authorized personnel
3. Store the signed ATT in a secure, retrievable location
4. Configure your `clearforge.config.yml` with the ATT token

No scenario will execute without a valid ATT token in the configuration. This is enforced at the CLI layer, not just by policy.

---

## Architecture

```
redteam-lab/
├── scenarios/               # Emulation scenarios by ATT&CK tactic
│   ├── initial-access/      # TA0001 — phishing, supply chain
│   ├── lateral-movement/    # TA0008 — PtH, RDP, SSH pivot
│   ├── privilege-escalation/# TA0004 — token manipulation, UAC bypass
│   ├── collection/          # TA0009 — staged data, clipboard
│   └── exfiltration/        # TA0010 — protocol-based, volume anomaly
├── playbooks/               # Engagement workflow documentation
│   ├── purple-team/         # Red/blue collaboration protocols
│   └── detection-validation/# SIEM-specific validation runbooks
├── detection-rules/         # Generated detection content
│   ├── sigma/               # Sigma YAML rules
│   ├── splunk/              # Splunk SPL queries
│   └── sentinel/            # Microsoft Sentinel KQL
├── mappings/                # ATT&CK Navigator layers, compliance maps
│   ├── mitre-attack/        # Navigator JSON (importable)
│   └── compliance/          # PCI, SOC2, ISO27001, NIST CSF
├── reporting/               # Report templates and generators
│   ├── templates/           # Jinja2 PDF templates
│   └── executive/           # Board-ready PPTX templates
├── lab-configs/             # Environment configuration examples
├── docs/                    # Full documentation
│   ├── getting-started.md
│   ├── authorization.md     # ATT process in detail
│   ├── architecture.md
│   └── monetization.md      # Consulting and licensing guide
└── .github/workflows/       # CI/CD validation pipelines
```

---

## Scenario Format

Every scenario is a YAML file with full metadata:

```yaml
# scenarios/lateral-movement/T1550.002-pass-the-hash.yml

id: CG-LM-001
technique: T1550.002
tactic: TA0008
name: "Pass-the-Hash Behavioral Emulation"
description: >
  Generates NTLM authentication event sequences and SMB access patterns
  consistent with PtH lateral movement using synthetic credentials in an
  isolated lab network. No real credential material is captured or transmitted.

authorization_required: true
safe_emulation: true
destructive: false
live_malware: false

targets:
  platforms: [windows]
  requirements: [domain_joined, smb_accessible]

telemetry:
  log_sources:
    - Windows Security Event Log
    - Sysmon
    - Network flow data
  key_events:
    - event_id: 4624
      description: "Logon Type 3 (Network) with NTLM authentication"
    - event_id: 4648
      description: "Logon using explicit credentials"
    - event_id: 4672
      description: "Special privileges assigned to new logon"

expected_detections:
  - rule_id: CG-SIGMA-LM-001
    description: "NTLM lateral movement — Type 3 logon from unusual source"
    confidence: HIGH
  - rule_id: CG-SIGMA-LM-002
    description: "Sequential Type 3 logons within time window"
    confidence: MEDIUM

compliance_coverage:
  - framework: PCI_DSS_4
    controls: ["10.2.5", "10.3.1"]
  - framework: SOC2_CC
    controls: ["CC6.1", "CC7.2"]
  - framework: ISO_27001
    controls: ["A.12.4.1", "A.16.1.5"]

references:
  - https://attack.mitre.org/techniques/T1550/002/
  - https://docs.microsoft.com/en-us/windows-server/identity/securing-privileged-access/

execution:
  steps:
    - phase: setup
      action: "Verify lab isolation and telemetry pipeline connectivity"
    - phase: execute
      action: "Emit synthetic NTLM authentication sequence to target"
    - phase: collect
      action: "Capture event log artifacts and network telemetry"
    - phase: validate
      action: "Check SIEM for expected alert within 120-second window"
    - phase: report
      action: "Log DETECT/MISS/PARTIAL result with artifact bundle"
```

---

## Detection Rules

### Sigma Rule Example

```yaml
# detection-rules/sigma/lateral-movement/T1550.002-pass-the-hash.yml

title: PtH Lateral Movement — NTLM Type 3 Logon from Unusual Source
id: cg-sigma-lm-001
status: stable
description: >
  Detects NTLM Type 3 (network) logon events that indicate pass-the-hash
  lateral movement based on source/destination patterns and authentication type.
references:
  - https://attack.mitre.org/techniques/T1550/002/
author: ClearGlass Detection Forge
date: 2026/05/08
tags:
  - attack.lateral_movement
  - attack.t1550.002
  - clearforge.generated
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 4624
    LogonType: 3
    AuthenticationPackageName: NTLM
  filter_legitimate:
    SubjectUserName|endswith: '$'
  condition: selection and not filter_legitimate
falsepositives:
  - Legacy applications using NTLM for network shares
  - Scheduled tasks with network authentication
level: medium
```

### Splunk SPL Example

```spl
| tstats count min(_time) as firstTime max(_time) as lastTime
  from datamodel=Authentication.Authentication
  where Authentication.action=success
    Authentication.authentication_type=NTLM
    Authentication.logon_type=3
  by Authentication.src Authentication.dest Authentication.user _time span=5m
| `drop_dm_object_name("Authentication")`
| eventstats count as session_count by src dest
| where session_count > 3
| eval risk_score=50
| `clearforge_tag("T1550.002", "lateral_movement")`
```

---

## Purple Team Workflow

```
KICKOFF (Day 1)
├── Scope confirmation with blue team lead
├── ATT selection (technique subset by priority)
├── Detection hypothesis documentation
└── SIEM baseline capture

EXECUTION (Day 2–4)
├── Red: Execute scenario → emit telemetry
├── Blue: Monitor for alerts in real time
├── Joint: Document DETECT / MISS / PARTIAL
└── Iterate: Tune rules, re-test immediately

REPORTING (Day 5)
├── Gap analysis by tactic
├── Detection rule delivery
├── Executive summary generation
└── Remediation backlog creation
```

---

## Report Outputs

| Format | Audience | Pages | Auto-Generated |
|--------|----------|-------|----------------|
| Executive Summary PDF | Board / C-Suite | 4 | ✓ |
| Technical Deep-Dive PDF | SOC / IR / Engineering | 38 | ✓ |
| Compliance Evidence Pack | Auditors / GRC | Variable | ✓ |
| STIX 2.1 Bundle | Threat Intel / SOAR | JSON | ✓ |
| JIRA Export | Engineering / Backlog | CSV | ✓ |

---

## Getting Started

### Prerequisites

```bash
python >= 3.11
docker (for lab environment containers)
git
```

### Installation

```bash
git clone https://github.com/ClearGlassInc/ClearGlassInc.github.io.git
cd ClearGlassInc.github.io/redteam-lab

pip install -r requirements.txt

cp lab-configs/clearforge.config.example.yml clearforge.config.yml
# Edit clearforge.config.yml with your environment details and ATT token
```

### First Run

```bash
# Validate configuration
python clearforge.py validate-config

# List available scenarios
python clearforge.py scenarios list --tactic lateral-movement

# Run a single scenario (requires valid ATT token in config)
python clearforge.py run --scenario T1550.002 --env lab-01 --dry-run

# Full purple team session
python clearforge.py session start --playbook playbooks/purple-team/standard-assessment.yml
```

---

## Compliance Mapping

| Framework | Coverage | Mappings File |
|-----------|----------|---------------|
| PCI DSS 4.0 | Requirements 10, 11, 12 | `mappings/compliance/pci-dss-4.0.json` |
| SOC 2 Type II | CC6, CC7, CC8 | `mappings/compliance/soc2.json` |
| ISO 27001:2022 | A.8, A.12, A.16 | `mappings/compliance/iso27001.json` |
| NIST CSF 2.0 | Detect, Respond | `mappings/compliance/nist-csf-2.json` |
| CIS Controls v8 | Controls 8, 10, 13 | `mappings/compliance/cis-controls-v8.json` |

---

## Commercial Engagements

| Tier | Format | Starting At |
|------|--------|-------------|
| Open Source | Self-service, community support | Free |
| Professional Assessment | Managed, analyst-led, full reports | $8,000/engagement |
| Enterprise Retainer | Monthly program, dedicated analyst | $2,000/month |

**Contact:** [Desmondotieno@icloud.com](mailto:Desmondotieno@icloud.com)  
**Product Page:** [clearglassinc.github.io/detection-forge.html](https://clearglassinc.github.io/detection-forge.html)

---

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md). Scenario contributions must include:
- Full YAML metadata with ATT&CK technique mapping
- Expected telemetry and event IDs
- At least one Sigma rule for the detection gap
- Compliance control mappings for at least two frameworks
- Verification that the scenario produces no real credential capture, no live malware execution, and no destructive behavior

---

## Legal

MIT License. See [LICENSE](./LICENSE).

**Important:** This software is provided for authorized security assessment, detection engineering, and analyst training only. Use against systems without explicit written authorization is illegal under the Computer Fraud and Abuse Act (18 U.S.C. § 1030), Canada's Criminal Code (s. 342.1), and equivalent laws in other jurisdictions. ClearGlass Inc. accepts no liability for unauthorized use.

---

*Built by [ClearGlass Inc.](https://clearglassinc.github.io) · Burlington, Ontario, Canada · Vision 2040*

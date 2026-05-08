# Standard Purple Team Assessment Playbook
## ClearGlass Detection Forge · 5-Day Engagement

---

## Overview

This playbook defines the standard 5-day purple team assessment workflow
for a ClearGlass Detection Forge engagement. It is designed for security
teams that want structured, repeatable adversary simulation with immediate
detection feedback.

**Prerequisites:**
- Signed Authorization to Test (ATT) document on file
- SIEM telemetry pipeline validated
- Blue team lead designated and briefed (or blind mode confirmed)
- Scenario selection agreed upon with stakeholder

---

## Day 1 — Scope Confirmation & Environment Validation

### Morning: Technical Setup (3 hours)

```
09:00 — ATT token validation and environment health check
09:30 — Sysmon deployment verification on all in-scope endpoints
10:00 — SIEM telemetry pipeline test (inject synthetic event, confirm receipt)
10:30 — Baseline telemetry capture (60 minutes of normal activity)
11:30 — Scenario queue configuration and priority ordering
12:00 — Lunch break
```

### Afternoon: Kickoff & Alignment (2 hours)

```
13:00 — Stakeholder kickoff (CISO, SOC lead, red team, ClearGlass analyst)
         · Confirm scope boundaries
         · Review ATT document and rules of engagement
         · Confirm emergency stop contacts
         · Confirm blue team awareness level (standard / blind)
13:45 — Hypothesis documentation
         · For each selected technique: what does the blue team EXPECT to detect?
         · Document current rule coverage per tactic
14:30 — Detection gap hypothesis matrix completed
15:00 — Day 1 complete
```

**Day 1 Outputs:**
- [ ] Environment validation report
- [ ] Baseline telemetry capture
- [ ] Detection hypothesis matrix (pre-assessment)

---

## Day 2-3 — Scenario Execution

### Execution Protocol

For each scenario in the agreed queue:

```
STEP 1: Pre-execution brief (5 min)
  · Red team announces technique and phase to blue team (if aware)
  · Confirm blue team SIEM is monitoring
  · Start session recording

STEP 2: Execute scenario
  · Run clearforge scenario with ATT token
  · Monitor emulation output in real time
  · Note any unexpected behavior → STOP if environment impact observed

STEP 3: Detection window (120 seconds default)
  · Blue team: actively monitoring for alerts
  · Red team: logging telemetry artifacts

STEP 4: Record result
  · DETECT: Alert fired correctly, contains useful IOCs
  · PARTIAL: Alert fired but with incomplete/incorrect data
  · MISS: No alert within window

STEP 5: Root cause (if MISS or PARTIAL)
  · Pull raw event logs — did the telemetry arrive at SIEM?
  · If yes → detection rule gap
  · If no → log collection gap (more urgent)
  · Generate Sigma rule for gap (automated)

STEP 6: Iterate
  · Apply generated rule to SIEM (if MISS)
  · Re-run scenario to validate rule effectiveness
  · Document tuning iterations
```

### Day 2 — Initial Access through Lateral Movement

| Timeslot | Technique | Expected Duration |
|----------|-----------|-------------------|
| 09:00 | T1566.002 — Spearphishing Link emulation | 20 min |
| 09:30 | T1078.002 — Valid Accounts (domain) | 20 min |
| 10:00 | T1133 — External Remote Services | 20 min |
| 10:30 | Break + documentation | 30 min |
| 11:00 | T1550.002 — Pass-the-Hash | 20 min |
| 11:30 | T1021.001 — RDP lateral movement | 20 min |
| 12:00 | Lunch | |
| 13:00 | T1021.002 — SMB lateral movement | 20 min |
| 13:30 | T1570 — Lateral Tool Transfer | 20 min |
| 14:00 | Results review + gap triage | 60 min |
| 15:00 | Rule generation session | 60 min |
| 16:00 | Day 2 standup — results vs. hypothesis | 30 min |

### Day 3 — Privilege Escalation, Persistence, Defense Evasion

| Timeslot | Technique | Expected Duration |
|----------|-----------|-------------------|
| 09:00 | T1134.001 — Token Impersonation | 20 min |
| 09:30 | T1068 — Exploitation for Privilege Escalation (emulation) | 20 min |
| 10:00 | T1547.001 — Registry Run Keys (persistence) | 20 min |
| 10:30 | T1053.005 — Scheduled Task (persistence) | 20 min |
| 11:00 | T1070.001 — Log Clearing | 20 min |
| 11:30 | T1562.001 — Disable Security Tools (emulation) | 20 min |
| 12:00 | Lunch | |
| 13:00 | T1055 — Process Injection (behavioral emulation) | 25 min |
| 13:30 | T1027 — Obfuscated Files/Information | 20 min |
| 14:00 | Results review + gap triage | 60 min |
| 15:00 | Rule generation and SIEM tuning | 60 min |
| 16:00 | Day 3 standup | 30 min |

---

## Day 4 — Collection, C2, Exfiltration

| Timeslot | Technique | Expected Duration |
|----------|-----------|-------------------|
| 09:00 | T1074.001 — Local Data Staging | 20 min |
| 09:30 | T1005 — Data from Local System | 20 min |
| 10:00 | T1071.001 — C2 over HTTP(S) — beacon emulation | 25 min |
| 10:30 | T1071.004 — C2 over DNS | 25 min |
| 11:00 | T1041 — Exfiltration over C2 channel (synthetic data) | 20 min |
| 11:30 | T1048 — Exfiltration over alternative protocol | 20 min |
| 12:00 | Lunch | |
| 13:00 — 16:00 | Targeted re-testing of MISS gaps from Days 2–3 | |

---

## Day 5 — Reporting & Handoff

### Morning: Report Generation (3 hours)

```bash
# Generate all reports from session data
python clearforge.py report \
  --session-dir ./sessions/2026-05-engagement/ \
  --format all \
  --org "CLIENT NAME" \
  --logo ./assets/client-logo.png
```

**Outputs generated:**
- `reports/executive-summary.pdf`
- `reports/technical-report.pdf`
- `reports/compliance-pack.pdf`
- `reports/stix-bundle.json`
- `reports/remediation-backlog.csv`
- `reports/detection-rules/` (all generated Sigma, SPL, KQL)

### Afternoon: Readout & Handoff (3 hours)

```
13:00 — Executive readout (CISO + leadership · 45 min)
         · Coverage score vs. baseline
         · Top 3 gaps by business risk
         · Recommended remediation priority
         · Investment asks (if any)

14:00 — Technical handout (SOC + detection engineering · 60 min)
         · Per-technique DETECT/MISS/PARTIAL matrix
         · Generated detection rules walkthrough
         · Tuning recommendations
         · Rule deployment guidance

15:00 — Remediation backlog review (SOC lead + engineering · 45 min)
         · JIRA export walkthrough
         · Priority sequencing
         · Re-test scheduling (30-day recommended)

16:00 — Document destruction / data handling confirmation
         · Confirm all ATT documents retained by client
         · Confirm raw session data retention policy
         · Schedule 30-day re-test
```

---

## Emergency Stop Protocol

If any scenario causes unexpected system behavior:

1. **Immediately:** Type `Ctrl+C` in the clearforge CLI — stops all active emulation
2. **Within 2 minutes:** Call Emergency Stop Contact listed in ATT document
3. **Within 15 minutes:** Provide preliminary incident brief (what ran, when, what was observed)
4. **Within 24 hours:** Provide full telemetry log of all actions taken during session

---

## Deliverables Checklist

- [ ] Executive Summary PDF (4 pages)
- [ ] Technical Report PDF (30–50 pages depending on scope)
- [ ] Compliance Evidence Pack
- [ ] STIX 2.1 Bundle
- [ ] Generated Sigma rules (one per detected gap)
- [ ] Splunk SPL queries
- [ ] Microsoft Sentinel KQL queries
- [ ] ATT&CK Navigator layer (pre/post comparison)
- [ ] Remediation Backlog (JIRA-importable CSV)
- [ ] Re-test schedule recommendation

---

*ClearGlass Detection Forge · Version 2.1 · [clearglassinc.github.io](https://clearglassinc.github.io)*

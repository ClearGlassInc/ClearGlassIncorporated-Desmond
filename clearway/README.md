# Clearway Compliance Audit Agent

Clearway is ClearGlass's independent Digital Presence Compliance, Audit & Assurance control-plane agent.

It is designed for high-assurance engineering: deterministic rules, explicit evidence, SHA-256 provenance, separation of duties, fail-closed gating, and reproducible reports. “NSA-grade” is treated only as an engineering-rigor aspiration; this software is not NSA-certified, government accredited, classified, or equivalent to a government system.

## Mission

Verify that material digital-presence activities are lawful, authorized, documented, auditable, reproducible, and defensible across privacy, CASL, Google Business Profile, SEO, AI governance, platform policy, accessibility, and security domains.

## Authority boundary

Clearway may:

- inspect declared evidence;
- classify findings;
- calculate the deterministic compliance score;
- create evidence registers and executive reports;
- return a fail-closed deployment decision;
- identify remediation and escalation requirements.

Clearway may not:

- mutate production systems;
- approve itself;
- override another governance control;
- perform private or unauthorized collection;
- issue legal conclusions on behalf of counsel.

A `BLOCK` result is an advisory/control signal that a release pipeline can enforce with a required status check. This repository does not silently change GitHub branch-protection settings.

## Run

```bash
python3 clearway/agent.py --input clearway/example_audit.json --report-dir clearway/reports
python3 clearway/agent.py --input clearway/example_audit.json --gate
```

The report is written as `COMPLIANCE_AUDIT_REPORT_YYYY_MM.md` plus a machine-readable JSON decision artifact. Evidence digests are SHA-256 over canonical JSON representations.

## Domains

- Privacy
- CASL
- Google Business Profile
- SEO
- AI Governance
- Platform Policy
- Accessibility
- Security

The scoring weights are privacy 20%, security 20%, platform policy 15%, GBP 15%, CASL 10%, accessibility 10%, and AI governance 10%.

## Gate rule

A deployment may pass only when all are true:

- security review = `PASS`;
- compliance review = `PASS`;
- evidence complete = `YES`;
- rollback plan = `VERIFIED`;
- no `HIGH`/`CRITICAL` unverified finding is present;
- no finding requires executive review without an acknowledged approval record.

The implementation is deterministic and never upgrades an unsupported claim to `VERIFIED`.

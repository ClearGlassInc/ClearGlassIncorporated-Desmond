# Workflow Doctor Learning Log

## Operating model

This log records verified workflow failures, remediations, workarounds, and reliability improvements. It must never contain credentials, tokens, cookies, private keys, or secret values.

## 2026-08-21

- Added a structured failure-pattern database at `.github/workflow-patterns.json`.
- Added a fail-closed workaround decision tree at `.github/workarounds/decision-tree.md`.
- Runner-admission failures are treated as platform blockers rather than code failures.
- Production approval and branch-protection controls remain mandatory.
- Missing-secret handling is validation/mock-mode only; no fabricated credentials are permitted.

### Improvement rule

Only promote a workaround to production behavior after reproducible evidence, security review, and explicit approval where required.

# CI Control-Plane Changelog

## 2026-08-22 — CircleCI control-plane pipeline

- Added governed CircleCI 2.1 validation, packaging, deployment, verification, and rollback orchestration.
- Added explicit pipeline parameters and fail-closed preflight validation.
- Isolated `ci-readonly`, `staging-deploy`, and `production-deploy` contexts.
- Added immutable release bundle and SHA-256 manifest evidence.
- Added HTTPS/status/release-marker post-deployment verification.
- Added GitHub Actions YAML and floating-reference integrity evidence.
- Added sandbox-only agent contract checks.
- Added deny-by-default security allowlist and release policy templates.
- Added production and rollback approval gates.
- Deployment and rollback adapters remain intentionally fail-closed until provider-specific commands and credentials are supplied through restricted contexts.
- No GitHub branch protection, ruleset, environment approval, protected secret, or deployment gate is bypassed.

## 2026-08-21 — High-Assurance CircleCI Control Plane

- Replaced the CircleCI entry point with a parameterized, fail-closed 2.1 orchestration design.

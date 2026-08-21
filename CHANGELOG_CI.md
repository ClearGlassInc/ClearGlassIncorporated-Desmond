# CI Control-Plane Changelog

## 2026-08-21 — High-Assurance CircleCI Control Plane

- Replaced the CircleCI entry point with a parameterized, fail-closed 2.1 orchestration design.
- Added immutable release manifest and SHA-256 artifact verification.
- Added deterministic lockfile/package-manager detection.
- Added GitHub Actions supply-chain validation for floating action references and dangerous trigger surfaces.
- Added sandbox-only agent contract checks.
- Added staging/production deployment and deterministic rollback adapters that refuse unconfigured provider commands.
- Added separate production deployment and production rollback approvals.
- Added deny-by-default security and release policy templates.
- Added machine-readable evidence collection and final evidence checksums.
- Preserved the rule that CircleCI does not bypass GitHub branch protection, rulesets, environment approvals, or GitHub Actions controls.
- Explicitly marked unavailable deployment-provider configuration as `NOT VERIFIED` rather than fabricating success.

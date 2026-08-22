# ClearGlass CircleCI 2.1 Control Plane

## Architecture

`.circleci/config.yml` is a parameterized control plane for validation, immutable packaging, restricted deployment, post-deploy verification, and rollback. Validation is read-only. Mutation requires an explicit pipeline parameter and restricted CircleCI context.

## Contexts

- `ci-readonly`: checkout, tests, policy checks, workflow integrity, artifact construction.
- `staging-deploy`: staging deployment and rollback credentials only.
- `production-deploy`: production deployment and rollback credentials only; never attach to validation jobs.

Create these contexts in CircleCI with least-privilege credentials. The repository cannot verify account-side context existence through GitHub alone.

## Trigger matrix

| Operation | Required controls |
|---|---|
| Validation | `run_validation=true`, target `none`, no deploy/rollback flag |
| Staging | `deploy_staging=true`, target `staging`, validation enabled, emergency stop false |
| Production | `deploy_production=true`, target `production`, validation enabled, change reference, authorized ref, approval |
| Staging rollback | `rollback_staging=true`, target `staging`, verified prior artifact, approval |
| Production rollback | `rollback_production=true`, target `production`, verified prior artifact, change reference, separate approval |

## Evidence and artifacts

Release packaging creates `release-bundle.tar.gz`, `artifacts/release/artifact.sha256`, and `artifacts/release/manifest.json`. The manifest records Git SHA, CircleCI pipeline ID, UTC build timestamp, SHA-256 artifact digest, and deployment target. Deployment scripts verify the digest before invoking the provider adapter.

## Deployment adapters

`REPLACE_ME_DEPLOY_COMMAND` and `REPLACE_ME_ROLLBACK_COMMAND` are intentional fail-closed placeholders. They must be supplied only through restricted CircleCI contexts after provider-specific review. A placeholder is never treated as successful deployment.

## Verification

`scripts/ci/post-deploy-verify.sh` requires an HTTPS URL, HTTP 200, and an explicit release marker. Evidence is written under `artifacts/evidence/`. No mutable response content is treated as a release identity unless the configured marker matches.

## GitHub workflow integrity

`scripts/ci/validate-github-workflows.sh` parses `.github/workflows/*.yml` and `.yaml`, rejects floating action references such as `@main` or `@master`, and writes `artifacts/evidence/workflow-integrity.json`.

## Agent safety

Agent contract tests always require `DRY_RUN=true`, `SANDBOX_MODE=true`, and `ENABLE_EXTERNAL_WRITES=false`. Startup and health checks are opt-in through restricted test configuration; no live external write is performed by validation.

## Rollback

Rollback consumes a last-verified immutable artifact, never a mutable branch. Production rollback requires a separate approval and change reference. Automatic production rollback is not enabled.

## Validation

Run `circleci config validate` with the CircleCI CLI. If the CLI is unavailable, record that limitation in CI evidence rather than claiming validation passed. Then trigger a validation-only pipeline with no deploy or rollback parameters.

## Security boundary

CircleCI does not bypass GitHub branch protection, repository rulesets, required status checks, environment approvals, protected secrets, or Cloudflare/Netlify deployment controls.

# ClearGlass CircleCI Release Control Plane

## Architecture

`.circleci/config.yml` defines five workflow classes: `validate`, `staging_release`, `production_release`, `staging_rollback_release`, and `production_rollback_release`.

`validate` is read-only and runs on normal branch/PR pipelines. Release workflows are selected only by explicit pipeline parameters. Privileged contexts are isolated: `ci-readonly`, `staging-deploy`, and `production-deploy`. Production context is never attached to validation jobs.

## Manual trigger matrix

| Operation | Required parameters |
|---|---|
| Validation | `run_validation=true`, `dry_run=true`, `target_environment=none` |
| Animation validation | validation + `deploy_animations=true`; publication remains disabled |
| Agent sandbox validation | validation + `run_agent_health_checks=true`; agent writes remain disabled |
| Staging release | `deploy_staging=true`, `target_environment=staging`, `dry_run=false`, `emergency_stop=false`, `deploy_production=false`, rollback flags false |
| Production release | `deploy_production=true`, `target_environment=production`, `dry_run=false`, `emergency_stop=false`, non-empty `change_reference`, authorized protected ref, CircleCI approval |
| Staging rollback | `rollback_staging=true`, `target_environment=staging`, `dry_run=false`, `emergency_stop=false`, verified prior release |
| Production rollback | `rollback_production=true`, `target_environment=production`, `dry_run=false`, `emergency_stop=false`, non-empty `change_reference`, verified prior release, separate approval |

## Required configuration

Create the CircleCI contexts exactly as follows:

- `ci-readonly`: verification-only credentials and release-signing verification material.
- `staging-deploy`: staging-only deployment identity.
- `production-deploy`: production-only deployment identity.

Use OIDC for cloud authentication when the provider supports it. Configure the provider trust policy with:

- audience: `REPLACE_ME_OIDC_AUDIENCE`
- role/service account: `REPLACE_ME_CLOUD_ROLE`
- subject binding: `REPLACE_ME_OIDC_SUBJECT`
- allowed branch/tag: `REPLACE_ME_ALLOWED_REF`

No private credential is committed to this repository.

## Provider-specific boundary

The repository currently exposes provider-specific deployment surfaces, but this control-plane branch does not assume a provider command when the exact production adapter cannot be established from the current source. Deployment adapters therefore fail closed on `REPLACE_ME_DEPLOY_COMMAND`, `REPLACE_ME_STAGING_URL`, `REPLACE_ME_PRODUCTION_URL`, or an unconfigured prior-release resolver. This is intentional and produces `NOT VERIFIED` rather than simulated success.

## Evidence

Every control-plane job writes machine-readable evidence under `artifacts/evidence/`. The release manifest contains Git SHA, ref, CircleCI pipeline/workflow IDs, UTC build timestamp, artifact SHA-256, lockfile digest, and deployment target. The final evidence bundle contains SHA-256 checksums for all evidence files.

## Rollback

Staging rollback is eligible only after a failed staging post-deploy verification and only when `emergency_stop=false`. It must resolve the last verified immutable release; mutable branches/tags are not acceptable rollback targets.

Production rollback is never automatically initiated by a failed production verification. It requires `hold_production_rollback`, the restricted `production-deploy` context, a verified prior release, and a separate change reference.

## Emergency shutdown

Trigger a manual pipeline with `emergency_stop=true`. This prevents new mutating CI actions. It does not revoke an already-issued cloud credential or stop an external deployment that is already running; use the deployment provider's incident procedure for those actions.

## Validation

Before enabling a release context, validate the configuration with the CircleCI configuration validator and run a validation-only pipeline. Do not treat an unconfigured provider adapter as a successful deployment.

# ClearGlass Inc.

**Transparency is infrastructure.**

ClearGlass Inc. is an Ontario-focused cybersecurity, AI-governance, OSINT, automation, and intelligence-platform company. This repository is the primary engineering and web platform for ClearGlassInc.com, including the public website, product surfaces, research systems, operational data, automation, and platform architecture.

## Live Platform

- Website: https://www.clearglassinc.com
- Intelligence Platform: https://www.clearglassinc.com/intelligence-platform.html
- Governed Data Fabric Diagnostics: https://www.clearglassinc.com/data-fabric.html
- Ontario OSINT: https://www.clearglassinc.com/Ontario-osint.html
- Products: https://www.clearglassinc.com/products.html
- Store: https://www.clearglassinc.com/store.html

## Core Systems

- **ClearGlass Nexus** — central intelligence and orchestration layer
- **Artemis** — AI/cyber intelligence product family
- **Guardian / Sentinel** — defensive cybersecurity and monitoring surfaces
- **Guardian DPPP** — Digital Presence Protection Program for protecting public digital assets, brand integrity, reputation, visibility integrity, compliance controls, and defensible incident response
- **Ontario OSINT** — public-source intelligence and regional analysis
- **XENOLITH** — sovereign intelligence-lattice research platform
- **ClearGlass Data Fabric** — governed same-origin repository data layer
- **Growth / SEO / Commerce** — revenue, marketing, search, and product systems

## Guardian Digital Presence Protection Program

Guardian now includes a protection-first Digital Presence Protection Program governed by ARTEMIS and the AEGIS lifecycle:

```text
OBSERVE → DETECT → ANALYSE → VERIFY → RESPOND → AUDIT → IMPROVE
```

The program monitors authorized public-facing surfaces including websites, domains/subdomains, business listings, social profiles, search surfaces, directories, GitHub identities, public references, reviews, and public-source mentions.

Protection priorities are:

- Brand and impersonation protection
- Reputation assurance
- Digital-asset integrity
- Geo-Grid Visibility Assurance rather than rank-only optimization
- Compliance-control monitoring
- Evidence provenance and auditability
- Defensible incident coordination

Implementation artifacts:

- `docs/GUARDIAN_DPPP.md` — full operating and security control specification
- `config/guardian/dppp.json` — machine-readable fail-closed policy contract
- `scripts/validate_guardian_dppp.py` — dependency-free policy validator and SHA-256 evidence generator

The validator must pass before the DPPP policy is considered structurally valid:

```bash
python3 scripts/validate_guardian_dppp.py
```

Guardian DPPP uses dual classification for findings: **severity** (`INFORMATIONAL` through `CRITICAL`) and **epistemic status** (`VERIFIED FACT`, `INFERENCE`, `ASSUMPTION`, `UNKNOWN`, `UNVERIFIED`). Significant findings require source identification, timestamps, evidence digesting, verification state, confidence, and provenance. Unsupported claims remain `UNVERIFIED`.

External-impact actions remain human-authorized by policy. Missing authorization, integrity failures, expired authorization, schema failures, and emergency-stop conditions fail closed. The repository makes no claim of NSA certification or equivalence; “high-assurance” describes the intended engineering discipline rather than a government accreditation.

## Governed Data Fabric

Repository-backed operational data is cataloged through `data/catalog.json` and accessed through `assets/js/clearglass-data-fabric.js`.

The fabric provides:

- same-origin loading
- parent-traversal blocking
- JSON and CSV decoding
- module and root-dataset discovery
- browser health checks
- restricted browser access for sensitive workflow boundaries such as `data/leads`

Run the offline validator when a local checkout is available:

```bash
python3 scripts/validate_data_fabric.py
node --check assets/js/clearglass-data-fabric.js
```

## Actions-Independent Release Path

GitHub Pages is configured from `main` and can publish through the repository's legacy Pages build path. The site also includes browser-based data-fabric diagnostics so the public runtime can be checked without depending on a GitHub-hosted Actions runner.

See `docs/ACTIONS_BILLING_FALLBACK.md` for the operational fallback and recovery procedure.

## Secure CircleCI Orchestration

`.circleci/config.yml` is the guarded CircleCI 2.1 orchestration entry point for repository validation, GitHub-workflow validation, frontend/animation artifact builds, sandbox agent checks, and approved Fly.io releases of the ClearGlass agent service.

### Workflows

- **`validate`** is the default branch/pull-request path. It runs preflight, dependency verification, lint/type/test/build, dependency and secret scans, GitHub workflow validation, frontend/animation smoke tests, and sandbox agent contract tests. It performs no deployment or GitHub mutation.
- **`staging_release`** exists only when the manually supplied pipeline parameter `deploy_staging=true`. Preflight additionally requires `run_validation=true`, `target_environment=staging`, `emergency_stop=false`, and a branch ref. All validation/security jobs must pass before the `staging-deploy` context is available to the deployment job.
- **`production_release`** exists only when the manually supplied pipeline parameter `deploy_production=true`. Preflight additionally requires `run_validation=true`, `target_environment=production`, `emergency_stop=false`, and either the protected `main` branch or a trusted signed `v...` release tag. A CircleCI `hold_production` approval job must be approved before the `production-deploy` context can be used.

### Manual pipeline parameters

| Parameter | Type | Default | Purpose |
|---|---|---:|---|
| `run_validation` | boolean | `true` | Run the validation chain. Required for either deployment. |
| `run_github_automation_checks` | boolean | `false` | Add extended, read-only GitHub workflow checks. Never triggers or writes GitHub Actions. |
| `run_agent_health_checks` | boolean | `false` | Add extended local/sandbox agent HTTP contract checks. |
| `deploy_staging` | boolean | `false` | Request a staging release. Requires `target_environment=staging`. |
| `deploy_production` | boolean | `false` | Request a production release. Requires `target_environment=production` and approval. |
| `enable_agents` | boolean | `false` | Reserved for a separately reviewed activation adapter. Currently fails closed if set `true`. |
| `deploy_animations` | boolean | `false` | Reserved for a separately reviewed frontend publication adapter. Currently fails closed if set `true`. |
| `emergency_stop` | boolean | `false` | Global mutation stop. If `true`, every deployment/activation/publication request is rejected. |
| `target_environment` | enum | `none` | One of `none`, `staging`, or `production`. |

Trigger release pipelines from CircleCI's manual pipeline trigger surface and supply only the parameters needed for that release. Do not place secret values in pipeline parameters.

### Required restricted contexts

Create and restrict these CircleCI contexts before enabling release workflows:

**`ci-readonly`**

- Must not contain a GitHub write token, deploy token, or other repository-mutation credential.
- For signed production tag verification, set `TRUSTED_RELEASE_SIGNER_FINGERPRINT` to the reviewed release-signing public identity.

**`staging-deploy`**

- `FLY_API_TOKEN` — staging-scoped Fly.io credential.
- `FLYCTL_VERSION` — exact approved Fly CLI version; `latest` is rejected.
- `STAGING_FLY_APP=REPLACE_ME` — dedicated staging Fly.io app. Do not point this at the production app.
- `STAGING_HEALTH_URL` — optional explicit staging health endpoint.
- `FLY_IMAGE_REF` — commit-addressed or digest-pinned image reference.

**`production-deploy`**

- `FLY_API_TOKEN` — production-scoped Fly.io credential.
- `FLYCTL_VERSION` — exact approved Fly CLI version; `latest` is rejected.
- `PRODUCTION_FLY_APP` — optional; defaults to the existing `clearglass-agent-service` app.
- `PRODUCTION_HEALTH_URL` — optional explicit health endpoint.
- `FLY_IMAGE_REF` — immutable image reference.

Restrict the staging and production contexts to the appropriate CircleCI security groups/project controls. Production credentials must never be copied into `ci-readonly`.

### GitHub automation boundary

CircleCI validates `.github/workflows/**`, YAML syntax, and immutable action pinning. It does **not** trigger, rerun, unblock, cancel, approve, or modify GitHub Actions and it does not auto-merge pull requests. Any future GitHub write integration requires a separately approved GitHub App/token scope, a new explicit pipeline parameter defaulting to `false`, and independent review of repository rules and environments.

### Frontend animations and agents

The frontend/animation job builds deterministic assets and stores evidence; it does not publish by default. `deploy_animations=true` remains fail-closed until a reviewed publication adapter exists. Agent tests run only in dry-run/sandbox mode with external writes disabled. `enable_agents=true` remains fail-closed until a reviewed activation adapter and enforceable runtime rate-limit policy exist.

### Dependency and secret gates

- Node uses `npm ci` with the committed `package-lock.json`.
- High/critical npm audit findings block the release path.
- Changed source files are scanned for common credential patterns and fail closed on candidates.
- Secret and dependency findings are never silently suppressed.

### Immutable deployment and evidence

Fly releases use commit-addressed or digest-pinned image references. Before mutation, the pipeline records the currently deployed immutable image so rollback is possible. Deployment evidence is stored under `deploy-evidence/` as CircleCI artifacts.

Post-deploy verification requires 20/20 successful health requests and records the deployment revision and endpoint evidence. A deployment is not considered successful until endpoint verification passes.

### Rollback procedure

**Staging:** deployment or post-deploy verification failure automatically redeploys the previously recorded immutable image and verifies health. The rollback result is written to deployment evidence.

**Production:** post-deploy failure does not silently mutate production again. CircleCI records the prior immutable image. After incident review and approval, run the production release with the `production-deploy` context and execute the reviewed rollback path. Never substitute an unreviewed tag or `latest` image.

No rollback procedure rotates secrets, changes repository permissions, alters organization settings, deletes data, or bypasses a protected environment.

## Repository Safety

- No credentials or private API keys belong in source control.
- Production secrets must remain in approved external secret stores or platform configuration.
- Public OSINT and cybersecurity functions are defensive, lawful, and evidence-oriented.
- Counter-UAS material in this repository is a component/research area; it is **not** the identity or primary purpose of this repository.

## Company

**ClearGlass Inc.**  
Ontario, Canada  
https://www.clearglassinc.com

© 2026 ClearGlass Inc. All rights reserved except where a file or third-party component states otherwise.

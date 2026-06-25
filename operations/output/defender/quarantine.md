# ClearGlass Defender — Quarantine Record

- Run (UTC): 2026-06-24T03:59:41+00:00
- Repository: `clearglassinc/clearglassinc.github.io`
- Quarantined items: 5
- Enforcement: **advisory** (no files were modified or deleted)

> Quarantine is a review gate, not a destructive action. Enforce the response plan through branch protection, required reviews, and token rotation.

## Incidents

### HIGH — Remote script piped straight into a shell

- Rule: `curl_pipe_shell` (command)
- Location: `runner/setup-runner.sh:48`
- File SHA-256: `a51ef6679debabfb9d4239b31f164860ea20b0e75417d455eb2ccc8fe9ae82b7`
- Recommended actions: `require_review`, `alert_owner`, `open_incident_issue`, `block_merge`
- Status: `flagged_for_review` (enforcement: advisory)

### HIGH — Third-party action is not pinned to a full commit SHA

- Rule: `require_sha_pinned_actions` (workflow)
- Location: `.github/workflows/agent.yml:57`
- File SHA-256: `d4388b7466ac982e4120b4b8216bc175c83747ec2eb7463902fdf60dc46ac0b7`
- Recommended actions: `require_review`, `alert_owner`, `open_incident_issue`, `block_merge`
- Status: `flagged_for_review` (enforcement: advisory)

### HIGH — Third-party action is not pinned to a full commit SHA

- Rule: `require_sha_pinned_actions` (workflow)
- Location: `.github/workflows/agent.yml:62`
- File SHA-256: `d4388b7466ac982e4120b4b8216bc175c83747ec2eb7463902fdf60dc46ac0b7`
- Recommended actions: `require_review`, `alert_owner`, `open_incident_issue`, `block_merge`
- Status: `flagged_for_review` (enforcement: advisory)

### HIGH — Third-party action is not pinned to a full commit SHA

- Rule: `require_sha_pinned_actions` (workflow)
- Location: `.github/workflows/codeql.yml:51`
- File SHA-256: `82bc11b30342adedaa0dcde1b1fd8d7ef70789723b787d84366f62f1ad91bfd2`
- Recommended actions: `require_review`, `alert_owner`, `open_incident_issue`, `block_merge`
- Status: `flagged_for_review` (enforcement: advisory)

### HIGH — Third-party action is not pinned to a full commit SHA

- Rule: `require_sha_pinned_actions` (workflow)
- Location: `.github/workflows/codeql.yml:58`
- File SHA-256: `82bc11b30342adedaa0dcde1b1fd8d7ef70789723b787d84366f62f1ad91bfd2`
- Recommended actions: `require_review`, `alert_owner`, `open_incident_issue`, `block_merge`
- Status: `flagged_for_review` (enforcement: advisory)

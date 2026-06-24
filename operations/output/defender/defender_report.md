# ClearGlass Defender Report

- Run (UTC): 2026-06-24T03:59:41+00:00
- Repository: `clearglassinc/clearglassinc.github.io`
- Files scanned: 400
- Build gate: ✅ pass

## Severity summary

| 🔴 critical | 🟠 high | 🟡 medium | 🔵 low | ⚪ info |
| --- | --- | --- | --- | --- |
| 0 | 5 | 0 | 0 | 0 |

## Response plan

- `require_review`
- `alert_owner`
- `open_incident_issue`
- `block_merge`

## Findings

### 🟠 HIGH — Remote script piped straight into a shell

- Rule: `curl_pipe_shell` (command)
- Location: `runner/setup-runner.sh:48`
- Evidence: `curl -fsSL https://deb.nodesource.com/setup_20.x | bash -`
- Suspicious command pattern in automation surface.

### 🟠 HIGH — Third-party action is not pinned to a full commit SHA

- Rule: `require_sha_pinned_actions` (workflow)
- Location: `.github/workflows/agent.yml:57`
- Evidence: `uses: actions/checkout@v5`
- Tag and branch refs are mutable and can be re-pointed at malicious code. Pin actions to a full 40-character commit SHA (keep the version in a trailing comment).

### 🟠 HIGH — Third-party action is not pinned to a full commit SHA

- Rule: `require_sha_pinned_actions` (workflow)
- Location: `.github/workflows/agent.yml:62`
- Evidence: `uses: anthropics/claude-code-action@v1`
- Tag and branch refs are mutable and can be re-pointed at malicious code. Pin actions to a full 40-character commit SHA (keep the version in a trailing comment).

### 🟠 HIGH — Third-party action is not pinned to a full commit SHA

- Rule: `require_sha_pinned_actions` (workflow)
- Location: `.github/workflows/codeql.yml:51`
- Evidence: `uses: github/codeql-action/init@v3`
- Tag and branch refs are mutable and can be re-pointed at malicious code. Pin actions to a full 40-character commit SHA (keep the version in a trailing comment).

### 🟠 HIGH — Third-party action is not pinned to a full commit SHA

- Rule: `require_sha_pinned_actions` (workflow)
- Location: `.github/workflows/codeql.yml:58`
- Evidence: `uses: github/codeql-action/analyze@v3`
- Tag and branch refs are mutable and can be re-pointed at malicious code. Pin actions to a full 40-character commit SHA (keep the version in a trailing comment).

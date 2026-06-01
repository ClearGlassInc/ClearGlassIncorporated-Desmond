# API Security Audit Bundle

A self-contained, repo-ready package for auditing API authorization against
access-control abuse: **IDOR, broken object-level authorization (BOLA), missing
authentication, privilege escalation, and request tampering.**

Defensive, authorized-testing only — no brute force, no fuzzing, no credential
guessing, no exploitation, no destructive actions.

---

## Layout

```
api-security-audit/
├── prompt/
│   ├── master_prompt.md        # Full audit prompt for an agent or engineer
│   └── scanner_prompt.md       # Prompt to (re)generate the safe scanner
├── tests/
│   ├── endpoint_matrix.csv     # Test-case matrix template (37 scenario rows)
│   └── endpoints_example.json  # Scanner input — replace with real endpoints
├── reports/
│   ├── report_schema.json      # JSON Schema (2020-12) for audit reports
│   └── sample_report.json      # Example completed report (3 findings)
├── scanner/
│   └── audit_scan.py           # Zero-dependency Python 3.11 scanner
├── .github/
│   └── workflows/
│       └── api-security-audit.yml   # TEMPLATE copy (see note below)
└── README.md
```

> **Workflow note:** GitHub Actions only runs workflows from the
> **repository-root** `.github/workflows/` directory. The active copy lives at
> the repo root; the copy inside this bundle is a portable template. If you
> extract this bundle into a new repo, move that file to the new repo's root
> `.github/workflows/` to activate it.

---

## Quick start

### 1. Define your endpoints

Edit `tests/endpoints_example.json`:

```json
[
  {
    "method": "GET",
    "path": "/api/v1/users/{id}",
    "auth_required": true,
    "roles": ["admin", "self"],
    "object_type": "User",
    "example_id": "42"
  }
]
```

`example_id` must be a resource **owned by your valid test user**. The scanner
substitutes `{id}` and walks a bounded ±3 range for sequential-ID checks.

### 2. Run the scanner (staging/dev only)

```bash
python api-security-audit/scanner/audit_scan.py \
  --base-url   https://staging-api.example.com \
  --endpoints  api-security-audit/tests/endpoints_example.json \
  --valid-token     "$AUDIT_VALID_TOKEN" \
  --low-priv-token  "$AUDIT_LOW_PRIV_TOKEN" \
  --other-user-id   "77" \
  --output-dir audit-reports
```

The scanner **refuses** any URL containing `prod` or `production`.

### 3. Review the output

Two files land in `--output-dir`:

- `api_audit_<timestamp>.json` — conforms to `reports/report_schema.json`
- `api_audit_<timestamp>.csv` — one row per test, for spreadsheets/triage

Exit code is non-zero when any test fails, so it doubles as a CI gate.

---

## What the scanner checks per endpoint

| Scenario | Expected |
|---|---|
| Unauthenticated request | `401` (or `200` for declared public routes) |
| Low-privilege user | `403` |
| Valid user, own object | `200` |
| Cross-user object access (IDOR) | `403` |
| Sequential ID enumeration (±3) | `403` for non-owned IDs |

## Pass / Fail rule

If changing only the object identifier yields unauthorized access,
modification, or data leakage — **fail**. If the server does not independently
confirm ownership, role, or permission — **broken access control**.

---

## CI integration

The workflow runs weekly (Mon 03:00 UTC) and on manual dispatch. It:

1. Refuses production targets.
2. Runs the scanner against the `staging` environment.
3. Uploads JSON + CSV artifacts (90-day retention).
4. Writes a job summary and fails the job on any authorization failure.

### Required secrets (on the `staging` environment)

| Secret | Purpose |
|---|---|
| `AUDIT_VALID_TOKEN` | Bearer token for a valid test user |
| `AUDIT_LOW_PRIV_TOKEN` | Bearer token for a low-privilege test user |
| `AUDIT_OTHER_USER_ID` | An object ID owned by a different test user (IDOR check) |

---

## References

- [OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/)
- [OWASP WSTG — Testing for IDOR](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/05-Authorization_Testing/04-Testing_for_Insecure_Direct_Object_References)
- NSA/CISA Joint CSA — Preventing Web Application Access Control Abuse (2023)
- [CWE-639](https://cwe.mitre.org/data/definitions/639.html), [CWE-284](https://cwe.mitre.org/data/definitions/284.html)

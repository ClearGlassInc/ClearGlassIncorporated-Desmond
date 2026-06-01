# Scanner Prompt — Safe Defensive API Scanner

Generate a defensive API scanner that accepts a list of authorized endpoints and
checks for missing authentication, weak authorization, and suspicious
object-reference handling.

The scanner should:

- Send baseline requests without credentials.
- Compare responses with and without auth.
- Test one-step object-ID substitution on known example endpoints.
- Flag endpoints that return `200` where `401` or `403` would be expected.
- Record status code, response length, and notable error text.
- Output JSON and CSV reports.

The scanner **must avoid**:

- Brute force
- Payload fuzzing
- Credential guessing
- Exploit attempts
- Account takeover behavior
- Any destructive or production-modifying action

---

## Operating Constraints (always enforced)

| Constraint | Rule |
|---|---|
| Target | Staging/dev only — refuse hostnames matching `prod`/`production` |
| Enumeration | Sequential-ID checks limited to a small bounded range (±3) around a known example ID |
| Authorization | Requires the operator to supply tokens for authorized test accounts |
| Output | Local-only JSON + CSV; no automatic exfiltration |
| Idempotency | Read-first; never issue writes unless explicitly authorized on a non-prod target |

A reference implementation that satisfies this prompt is provided at
`../scanner/audit_scan.py`.

# Workflow Workaround Decision Tree

## Safety contract

Workarounds are **test-only unless explicitly approved for production**. Never bypass branch protection, environment approvals, required checks, authentication, or security policy. Never create fake credentials or place secret values in source control.

1. **Runner admission / account billing / quota**
   - Do not alter deployment semantics.
   - Preserve the workflow and record `runner-admission` as BLOCKED.
   - Use local validation, static YAML validation, unit tests, and another authorized CI provider only when its credentials and policy are already configured.
   - Escalate the account/platform issue.

2. **Missing secret**
   - Do not create a fake secret in production.
   - Run configuration/schema validation without the protected operation.
   - Record the exact secret *name*, never its value.

3. **Approval/environment gate**
   - Do not bypass it.
   - Test build/package artifacts in an unprotected non-production environment if one already exists.
   - Keep production promotion gated.

4. **Rate limit/network**
   - Use bounded exponential backoff with jitter where semantically safe.
   - Cache immutable dependencies.
   - Fail closed after the retry budget.

5. **Dependency failure**
   - Reproduce first.
   - Prefer lockfiles and known-good versions.
   - Do not silently downgrade security-sensitive dependencies.

6. **Permission failure**
   - Request the minimum additional permission required.
   - Never substitute a broad token merely to make a workflow green.

7. **Unknown failure**
   - Capture evidence.
   - Add a pattern candidate.
   - Open an issue for human review rather than autonomous production modification.

## Evidence rule

A workaround is successful only when its intended test completes and the evidence is retained. A skipped deploy is **not** a successful deployment.

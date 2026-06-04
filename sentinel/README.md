# SENTINEL — Phase-One Governance Shell

A defense-grade, **fail-closed** reference implementation of permission-aware
retrieval for the PERCIVAL / JARVIS OS control plane. It proves the Phase-One
exit milestone: *the Governance Shell catches and blocks unauthorized agent
retrieval in a restricted scope.*

## The assurance gate (SABER-aligned)

```
Execution = Permitted  iff  (C ≥ τ) ∧ (R_data ⊆ P_user) ∧ (S_threat < ε)
          = Denied     otherwise   (and Denied if ANY term is uncomputable)
```

- **C** — request/agent confidence (`τ` default 0.60)
- **R_data ⊆ P_user** — requested data within the user's permission boundary
- **S_threat** — adversarial-injection score from a secondary red-team scorer (`ε` default 0.50)
- **Fail-closed** — an RBAC/DB outage, a raised scorer, or any unverifiable term ⇒ **Denied**

## RBAC model (see `../docs/adr/0001-vector-rbac-model.md`)

Hybrid, defense-in-depth:

1. **Tenant** = hard partition (namespace/collection per tenant). Blast-radius
   containment, per-tenant delete + KMS key.
2. **Role / sensitivity** = ACL metadata pre-filter *inside* the partition
   (optimization that narrows candidates).
3. **Authority** = every returned `doc_id` is **re-authorized against Postgres
   RBAC** before any chunk reaches the LLM. A vector-layer bug or poisoned
   embedding metadata degrades to *missed results*, never *leaked results*.

## The trust loop (`sentinel/retrieval.py`)

```
ingest(query) → S_threat
   → resolve P_user (fail-closed)
   → Governance Shell gate (C, scope, S)
   → select tenant namespace (server-side)
   → fail-closed ACL filter (deny-all if P_user unresolved)
   → vector query (candidates)
   → RE-AUTHORIZE doc_ids vs Postgres RBAC   ← authoritative gate
   → assemble chunks + provenance + confidence band
   → append to hash-chained audit log
```

## Run

```bash
# Core trust loop — no external deps:
cd sentinel && python -m pytest -q          # 11 proof tests

# Optional HTTP layer:
pip install -r requirements.txt
uvicorn sentinel.app:app --reload
# curl -s localhost:8000/v1/retrieve -H 'Authorization: Bearer tok-acme-analyst' \
#      -H 'content-type: application/json' -d '{"query":"revenue report"}'
```

## What the tests prove (`tests/test_governance.py`)

| Property | Test |
|---|---|
| Authorized retrieval returns only in-scope docs | `test_authorized_retrieval_returns_only_in_scope` |
| Admin clearance unlocks sensitive doc | `test_admin_clearance_unlocks_sensitive_doc` |
| Clearance ceiling filters secrets | `test_clearance_boundary_filters_secret` |
| **Cross-tenant blocked even when the vector store leaks** | `test_cross_tenant_blocked_even_when_vector_store_leaks` |
| RBAC outage ⇒ fail-closed (deny, 0 chunks) | `test_failclosed_when_rbac_unavailable` |
| Prompt injection ⇒ denied | `test_prompt_injection_denied` |
| Low confidence ⇒ denied | `test_low_confidence_denied` |
| Custom thresholds enforced | `test_custom_thresholds_enforced` |
| Audit chain tamper-evident | `test_audit_chain_is_tamper_evident` |

## Production swap-ins

| Reference | Production |
|---|---|
| `InMemoryRBAC` | `PostgresRBAC` (`schema.sql`, short statement timeout) |
| `InMemoryVectorStore` | Pinecone (namespace=tenant) or Milvus (partition-key=tenant) |
| `embed()` hashing stub | real embedding model |
| `HeuristicRedTeam` | dedicated red-team / injection-classifier model |
| in-memory `AuditLog` | append-only Postgres table + periodic anchoring |

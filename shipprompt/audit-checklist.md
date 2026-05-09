# ShipPrompt 40-Point MLOps & Prompt-Ops Audit

> The exact checklist we run against your repository, infra, and CI in the
> 48-hour audit. Score each item Pass / Partial / Fail. Score < 28 / 40 means
> you have material risk.

**Engagement:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_
**Auditor:** ClearGlass Inc. — ShipPrompt
**Date:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_
**Repos in scope:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_

---

## 1. Deployment Automation (5)

| # | Check | Pass criteria | Score |
|---|---|---|---|
| 1 | Single-command deploy | One make target or CLI command builds + deploys to a target env | |
| 2 | One-command rollback | Previous artifact + previous prompt registry can be restored in < 60s | |
| 3 | Idempotent infra-as-code | Terraform / Pulumi / CDK; plan-apply with no drift on second run | |
| 4 | Pinned model & framework versions | All models pinned to a specific snapshot/version; no `latest` tags | |
| 5 | Reproducible build from clean checkout | Fresh clone → green build with no human steps | |

## 2. Prompt Registry & Versioning (5)

| # | Check | Pass criteria | Score |
|---|---|---|---|
| 6 | Prompts in Git, not Notion / Slack / Docs | Single source of truth in repo | |
| 7 | Stable prompt IDs + semantic versions | `prompt_id` + `version` per prompt | |
| 8 | Signed prompt artifacts | Hash + signature stored alongside artifact | |
| 9 | Diff-able prompt history | `git log` and tooling can show prompt-level diffs | |
| 10 | Prompt → model binding manifest | Manifest declares which prompt versions ship with which model version | |

## 3. CI/CD & Eval Gates (5)

| # | Check | Pass criteria | Score |
|---|---|---|---|
| 11 | Eval suite runs on every PR | Automated, blocking, deterministic seed | |
| 12 | Quality regression blocks merge | Score-delta threshold enforced in CI | |
| 13 | Canary / staged rollout | Traffic split or feature-flag rollout with auto-promote | |
| 14 | Auto-tagging of deploys | Each deploy creates an immutable tag with prompt + model versions | |
| 15 | Required reviewers for prompt PRs | CODEOWNERS or branch protection on `prompts/**` | |

## 4. Observability (5)

| # | Check | Pass criteria | Score |
|---|---|---|---|
| 16 | Per-prompt latency + cost metrics | Dashboard slices by `prompt_id`, `prompt_version` | |
| 17 | Per-model token attribution | Input + output tokens per request, per model | |
| 18 | Trace IDs across model calls | OpenTelemetry trace spans through all model hops | |
| 19 | Prompt-version tag on every log line | Structured logs include `prompt_version` | |
| 20 | SLO + alerting wired | Latency, error-rate, and quality SLOs with paging | |

## 5. Security & Secrets (5)

| # | Check | Pass criteria | Score |
|---|---|---|---|
| 21 | No keys in git history | gitleaks / trufflehog clean on full history | |
| 22 | Provider keys scoped + rotated | Per-environment, < 90-day rotation, auditable | |
| 23 | Egress policy on inference workers | Only allowlisted endpoints; no arbitrary outbound | |
| 24 | Prompt-injection test corpus | Curated adversarial test set runs in CI | |
| 25 | Output filtering / PII guard | Outbound responses scrubbed for PII, secrets, prompt leakage | |

## 6. Compliance & Audit Trail (5)

| # | Check | Pass criteria | Score |
|---|---|---|---|
| 26 | Model lineage record | Training data, base model, fine-tune, and deploy chain documented | |
| 27 | Prompt change attribution | Every prompt change has commit, author, reviewer, justification | |
| 28 | Approval workflow for prod prompts | Two-person review for production prompt changes | |
| 29 | Retention & deletion policy | Logs, prompts, and artifacts have explicit lifecycle | |
| 30 | Compliance evidence export | SOC 2 / ISO / EU AI Act evidence pack exportable in < 1 day | |

## 7. Cost Controls (5)

| # | Check | Pass criteria | Score |
|---|---|---|---|
| 31 | Monthly inference budget + alerts | Hard cap or pager on overrun | |
| 32 | Per-feature cost dashboard | Cost attributable to product surface, not just provider | |
| 33 | Caching layer for deterministic prompts | Idempotent prompts cached by content hash | |
| 34 | Model-tier routing | Cheap model first, escalate only on confidence threshold | |
| 35 | Idle worker shutdown | GPU / inference workers scale to zero when idle | |

## 8. Reliability & Runbook (5)

| # | Check | Pass criteria | Score |
|---|---|---|---|
| 36 | Documented rollback procedure | Single page, tested, < 5 minutes to execute | |
| 37 | On-call rotation | Defined primary + secondary, paging works | |
| 38 | Incident postmortem template | Used for last incident, blameless format | |
| 39 | DR test in last 90 days | Evidence of a real or game-day recovery | |
| 40 | Vendor-failover plan | Documented switch path between OpenAI / Anthropic / self-host | |

---

## Scoring & Risk

| Score | Tier | Meaning |
|---|---|---|
| 36–40 | **Green** | Mature. Minor optimization only. |
| 28–35 | **Yellow** | Functional but exposed. 1 sprint closes the gap. |
| 16–27 | **Orange** | Material risk. Sprint + retainer recommended. |
| 0–15  | **Red** | Pre-incident. Enterprise tier required. |

## Deliverables

1. Completed scorecard (this file, filled).
2. Risk & remediation report (PDF).
3. 30 / 60 / 90-day plan with dollar-impact estimates.
4. Loom walkthrough (15–25 minutes).
5. Quote for follow-on Sprint or Enterprise engagement.

---

© ClearGlass Inc. · ShipPrompt Audit Template v1 · MIT-licensed for client use.

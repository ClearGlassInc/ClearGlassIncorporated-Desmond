# Architect Checklist — Week of 2026-08-11 (ISO W33)

**Prepared:** 2026-08-14 · **Scope:** `ClearGlassInc/ClearGlassIncorporated-Desmond`
· **Owner:** Architecture

This is the weekly architect review. Items grounded in this repo carry concrete
findings and, where applicable, a change shipped in this same PR. Items that need
hardware, spend data, or a scheduled meeting carry a decision-ready plan instead
of a fabricated result.

| # | Item | Status | Artifact |
|---|------|--------|----------|
| 1 | Audit CI/CD for permission bloat + secret exposure | ✅ Audited — posture strong | findings below |
| 2 | Benchmark one AI workload on AMD accelerators | 📋 Plan ready — needs GPU/host | plan below |
| 3 | Review agent/tool permissions + sandboxing | ✅ Audited — 2 gaps noted | findings below |
| 4 | Update tech radar with K8s AI maturity items | ✅ Shipped | `TECH_RADAR.md` |
| 5 | Schedule cross-team supply-chain + agentic-risk session | 📋 Agenda + invite drafted | below |
| 6 | Model Q3 cloud spend vs AI growth | 📋 Model + assumptions ready — needs actuals | below |
| 7 | Trial one vuln-detection AI tool in non-prod pipeline | ✅ Shipped (pilot) | `.github/workflows/codeql-trial.yml` |

---

## 1 — CI/CD permission + secret-exposure audit ✅

**Method:** enumerated all 48 workflows in `.github/workflows/`, checked for a
`permissions:` block per workflow, scanned for over-broad token scopes, secret
interpolation into `run:`/`env:`, `pull_request_target`, and tag-pinned (vs
SHA-pinned) third-party actions.

**Findings — the posture is genuinely strong:**

- **Least privilege is the norm.** Every workflow declares a `permissions:`
  block; the common top-level default is `contents: read`, and jobs widen only
  to what they need (e.g. `pages.yml` → `pages: write` + `id-token: write`;
  `ip-protection-scan.yml` → `issues/pull-requests: write`). No `write-all`
  anywhere. `workflow-repair-agent.yml` even sets `id-token: none` explicitly.
- **All third-party actions are SHA-pinned** to full 40-char commits
  (`actions/checkout@df4cb1c…`, `peter-evans/create-pull-request@84ae59a…`,
  `sigstore/cosign-installer@6f9f177…`, etc.). This is enforced, not just
  convention — `bots/defender/engine.py` fails on any unpinned `uses:`.
- **No `pull_request_target` triggers.** The only textual match is a *comment* in
  `defender-watch.yml` documenting that it deliberately avoids the pattern; the
  Defender's own detector strips comments, so this is clean.
- **No secret exposure.** No `echo`/`run` of `secrets.*`, no secrets pushed into
  `env:` for logging. A dedicated `secret-scan` job in `security.yml` greps the
  full history for AWS keys, GitHub PATs, etc., and `.github/dependabot.yml`
  keeps the pinned actions patched.

**Minor items (low severity, no action forced this week):**

- `security.yml`'s dependency-review job runs `continue-on-error: true` because
  Dependency Graph is disabled in repo settings — so a flagged vulnerable
  dependency surfaces in logs but does **not** block the PR. *Recommendation:*
  enable Dependency Graph under Settings → Code security, then drop the
  `continue-on-error` to restore hard enforcement. (Settings toggle — cannot be
  done from a workflow file.)
- 48 workflows is a large surface with visible overlap between the several
  "military-op" / orchestrator / policy-gate workflows. *Recommendation:* a
  consolidation pass to reduce scheduled-run cost and review load — tracked as a
  candidate, not urgent.

**Verdict:** no permission bloat or secret exposure found. The estate is already
running the hardening most orgs are still trying to reach.

---

## 2 — Benchmark one AI workload on AMD accelerators 📋

Cannot be executed from this environment (no GPU host, no AMD ROCm runner). Plan
is ready to run the moment a node pool exists (see the GPU Operator / Kueue
entries added to `TECH_RADAR.md`).

- **Workload:** the Kimi-K3 / model bakeoff already scoped in
  `KIMI_K3_TECH_RADAR.md` — a fixed suite of real tasks from this repo
  (component migration, test generation, terminal-driven fixes, doc updates) run
  as an offline inference/eval job.
- **Comparison:** AMD (MI300-class, ROCm) vs the current NVIDIA/API baseline,
  same model + same prompts.
- **KPIs:** tokens/sec, latency p50/p95, $/1M tokens, task success rate,
  hallucinated-file rate, and — critically — **framework compatibility friction**
  (vLLM/kernel gaps on ROCm), which is usually the real cost, not raw FLOPs.
- **How to run it cleanly:** as a **Kueue** batch job on a non-prod GPU node pool
  so the bakeoff can't starve other work. This is exactly why Kueue/GPU-Operator
  were added to the radar's Trial ring this week.
- **Next action:** provision one non-prod GPU node (owner: infra) → then this
  item converts from plan to result.

---

## 3 — Agent/tool permissions + sandboxing review ✅

**Method:** reviewed the agent definitions in `agents/*/agent.json` +
`tool_schema.json`, the named-agent stack under `sentinel/`, and the commerce OS
gate they all ultimately answer to.

**Findings — the model is sound where it's wired to the gate:**

- The **commerce OS safety model** is the backbone: read-only → draft → human
  approval → execute, scored 0–100 in `governance.py`, with high/critical actions
  blocked until an `approvals` row is `approved`, everything logged to the
  append-only `events` ledger, and mutating admin routes gated behind
  `require_admin` (`app/security.py`). This is real, tested
  (`tests/test_governance.py`), and enforced in `daily_loop.py`'s self-check.
- Agent definitions carry explicit `safety_model` / `hard_rules` blocks (e.g.
  `agents/engineering_execution/agent.json`: "never weaken the commerce OS
  approval gates," "never commit or log secrets").
- The `sentinel/` agents are described as keyless, stdlib-only, fail-closed —
  the right default posture for autonomous components.

**Gaps to close (this is the actionable part):**

1. **Prompt-declared rules ≠ runtime sandbox.** An agent's `hard_rules` in JSON
   are guidance to the model, not an enforced boundary. The *only* hard boundary
   today is the commerce OS governance gate. Any agent path that can act
   **outside** that gate (filesystem, outbound HTTP, shell) is governed by prose,
   not code. *Recommendation:* for every agent with tool access, the enforced
   isolation should live in the runtime (container/namespace, egress
   NetworkPolicy, read-only mounts) — the GPU-Operator/isolation Trial entry and
   the "cluster-wide privileged agent runtimes → Hold" entry added to the radar
   this week are the vehicle.
2. **No single inventory of which agent holds which tool/credential.** Tool
   schemas are scattered per-agent. *Recommendation:* generate a capability
   matrix (agent → tools → scopes → does-it-touch-money) as a committed artifact,
   so this review is a diff next quarter instead of a re-read. Good candidate to
   auto-generate from the `agent.json` files.

**Verdict:** governed money paths are well-sandboxed; non-commerce agent tool use
relies on prompt discipline and should graduate to runtime-enforced isolation.

---

## 4 — Tech radar: K8s AI maturity items ✅ (shipped in this PR)

Created **`TECH_RADAR.md`** as a consolidated, ring-based radar (Adopt / Trial /
Assess / Hold) and populated a **"Kubernetes + AI platform maturity"** ring:
KServe, Kueue, Dynamic Resource Allocation for GPUs, KubeRay, inference gateways
(vLLM/TGI), GPU Operator + node isolation, and signed-image admission (cosign) —
each with its ring and the blocker keeping it there. The existing
`KIMI_K3_TECH_RADAR.md` is now cross-linked as the AI-models entry rather than
standing alone. Every K8s item is deliberately **Assess/Trial/Hold** — none is
Adopt, because no GPU node pool is provisioned yet.

---

## 5 — Cross-team session: supply-chain + agentic risk 📋

Meeting not auto-created (an outward calendar invite should be sent by a human,
or on explicit request). Draft is decision-ready:

- **Title:** Supply-chain + Agentic Risk Review (Q3)
- **Duration / cadence:** 60 min; propose recurring monthly.
- **Invite:** Architecture, Security/Defender owner, Commerce OS owner,
  Infra/Platform, one Agents/Sentinel maintainer.
- **Agenda:**
  1. CI/CD supply-chain state — SHA-pinning + cosign/SBOM/provenance already in
     `release-supply-chain.yml`; extend attestation to *cluster admission* (radar
     Trial entry).
  2. Agentic risk — item 3 gaps: runtime-enforced agent sandboxing and the
     capability matrix.
  3. CodeQL pilot (item 7) — review first week of alerts, decide graduation.
  4. Dependency Graph re-enable decision (item 1 minor).
- **Next action:** confirm attendees + slot, then I can create the calendar event
  and send the invite on request (Google Calendar connector is available this
  session).

---

## 6 — Model Q3 cloud spend vs AI growth signals 📋

Framework ready; needs the actual billing export + usage series to produce
numbers (not fabricating them here).

- **Cost drivers to model:** (a) model/API inference spend — the dominant AI
  line, scales with agent invocations + token volume; (b) prospective self-host
  GPU node pool (fixed monthly per node — see radar); (c) CI minutes — 48
  workflows incl. several scheduled loops (`commerce-daily-loop`,
  `control-surface-feeds`, `defender-watch` every 6h), a real and *reducible*
  line; (d) Pages/storefront/control-plane hosting (Render).
- **Growth signals to regress against:** agent-invocation count, commerce OS
  order/checkout volume, and token throughput per accepted change (the KPI from
  the Kimi radar).
- **Method:** unit-economics — **$ per accepted agent change** and **$ per
  order** — then project Q3 under low/expected/high AI-adoption scenarios. This
  ties spend to value delivered instead of raw infra totals.
- **Quick win visible now:** the scheduled-workflow cadence is a controllable
  cost lever independent of AI growth (see item 1 consolidation note).
- **Next action:** pull the cloud billing export + agent-usage series (owner:
  finance/infra) → I'll populate the model.

---

## 7 — Trial a vuln-detection AI tool in a non-prod pipeline ✅ (shipped in this PR)

Piloted **GitHub CodeQL** (semantic SAST / code analysis) as
**`.github/workflows/codeql-trial.yml`**:

- Scans **Python** and **JavaScript/TypeScript** (`build-mode: none`), on PR +
  push to `main`, weekly, and on demand, with `security-extended` queries to see
  full signal before tuning.
- **Non-prod by construction:** analysis-only, uploads to the Code Scanning tab,
  and is **not** wired into branch protection — it cannot block merges during the
  trial.
- Matches estate policy: least-privilege token (`contents: read` top-level;
  job adds `security-events: write` + `actions: read`), all actions SHA-pinned
  (`github/codeql-action@67ba681…` v3.37.7), no `pull_request_target`. Verified
  against `bots/defender/engine.py` — passes.
- **Graduation criteria:** after ~1 week of alerts, if the false-positive rate is
  low, promote by requiring the `CodeQL Trial / Analyze` check in branch
  protection (and optionally move to GitHub default setup). Decision lands in the
  item-5 session.

---

## Shipped in this PR

- `.github/workflows/codeql-trial.yml` — CodeQL vuln-detection pilot (item 7).
- `TECH_RADAR.md` — consolidated ring-based radar incl. K8s AI maturity (item 4).
- `operations/architect-checklist-2026-W33.md` — this report (items 1–6 findings
  + plans).

## Open follow-ups (owners outside this PR)

- Enable Dependency Graph → restore hard dependency-review gate (item 1).
- Provision one non-prod GPU node → unblocks items 2 + 3-sandboxing (infra).
- Confirm attendees/slot for the risk session → invite goes out (item 5).
- Pull billing + usage exports → populate the Q3 spend model (item 6).
- Generate the agent→tool→scope capability matrix (item 3).

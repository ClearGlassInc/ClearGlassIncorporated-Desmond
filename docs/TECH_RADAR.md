# ClearGlass Tech Radar

**Maintained by:** Architecture · **Last updated:** 2026-07-28 (week 31)

A standing record of what we run, what we are actively trialling, what we are
watching, and what we have decided *not* to pursue yet. Each entry states a
position and the reason **for us** — a technology can be excellent in general
and still sit in Hold here because it does not fit our deployment shape.

## Rings

| Ring | Meaning |
|------|---------|
| **Adopt** | In production. New work should default to it. |
| **Trial** | Running in a real but non-gating pipeline, with a review date. |
| **Assess** | Worth understanding. Not yet justified — usually blocked on a precondition. |
| **Hold** | Deliberately not pursuing now. Revisit only if the stated trigger fires. |

## The constraint that shapes this radar

Production runs on **Render** (`clearglass-commerce/render.yaml`): a managed
PaaS hosting the FastAPI control plane plus managed Postgres 16, with the
storefront and admin deployed as separate Next.js services. The static
marketing site is GitHub Pages.

There is **no Kubernetes cluster in production.** The repo does contain K8s
artifacts — `deployment/artemis/k8s/` (Deployment, HPA, ConfigMap),
`percival_v9/deploy/k8s/`, and a Kyverno `ClusterPolicy` at
`platform/policies/k8s/require-signed-images.yaml` — but these are target-state
scaffolding, and the v9 material carries its own "not provisioned" banner.
Nothing in those directories is applied to a live cluster.

This matters for every K8s AI entry below. Their real cost to us is not the
tool; it is **the cluster we would have to stand up and operate to use it.**
Treating that as a hidden line item is how platform migrations get approved by
accident, one radar entry at a time. So each K8s entry below names the
precondition explicitly.

---

## Kubernetes AI maturity (new this week)

### Assess — Kubernetes as the AI serving substrate

The K8s AI serving stack has genuinely matured: scheduling, autoscaling and
multi-tenancy for inference are no longer research problems. The industry
default for self-hosted model serving is converging on Kubernetes.

**Our position: Assess, not Adopt.** We do not currently self-host model
inference at all — our AI workloads are API-backed (Anthropic/OpenAI via
`agent.yml`, `codex-autofix.yml`). The substrate question only becomes live if
we move a workload in-house, and that decision should be driven by the
economics in the Q3 spend model, not by the substrate's maturity.

**Precondition to promote:** a self-hosted inference workload with a
demonstrated cost or latency case against the managed API.

### Assess — Dynamic Resource Allocation (DRA) for accelerators

DRA is the structural fix for how Kubernetes hands out GPUs: it replaces the
opaque `nvidia.com/gpu` integer count with a real resource-claim model that can
express device classes, sharing and topology. It is the piece that makes
heterogeneous accelerator fleets — mixed NVIDIA/AMD — schedulable without
vendor-specific hacks.

**Why it is on the radar now:** it is the natural landing place for the AMD
accelerator work in this week's checklist (item 2). If that benchmark says AMD
is viable for one of our workloads, a mixed fleet becomes plausible, and DRA is
what makes a mixed fleet operable. Assessing it now is cheap; discovering it
after committing to a scheduler is not.

**Precondition to promote:** the AMD benchmark returns a viable result *and*
we choose to self-host.

### Assess — Admission-time image signature + provenance verification (Kyverno)

This is the highest-value K8s entry we have, and it is half-built.

The **producing** half is real and running: `release-supply-chain.yml` performs
keyless OIDC signing and emits SLSA provenance attestations (`id-token: write`,
`attestations: write`). The **verifying** half —
`platform/policies/k8s/require-signed-images.yaml`, which rejects unsigned or
unattested images at the cluster — is written but unprovisioned.

So today we sign artifacts that nothing checks. That is not worthless (the
attestations are independently auditable after the fact), but the control it
implies — "a stolen registry credential is worthless" — **is not in force.**
The radar should say so plainly rather than let the presence of the policy file
imply coverage.

**Precondition to promote:** a cluster exists. Until then, treat the signing
pipeline as producing evidence, not as enforcing deployment integrity.

### Hold — KubeRay / KServe / operator-managed model serving

Mature and well-supported, and squarely aimed at a problem we do not have: we
run no distributed training and no self-hosted inference fleet. Adopting an
operator would mean adopting Kubernetes first.

**Revisit trigger:** self-hosted inference reaches a scale where per-request
API pricing loses to reserved capacity — which is exactly what the Q3 model
(checklist item 6) is built to detect.

### Hold — GPU time-slicing and MIG partitioning

Sharing techniques that pay off when you own accelerators and need to raise
utilization. We own none. Filed so that a future capacity conversation starts
from a known option rather than rediscovering it.

**Revisit trigger:** same as above, plus owned or reserved accelerator capacity.

---

## AI tooling

### Trial — CodeQL for application SAST

Added this week as `.github/workflows/codeql-trial.yml` (checklist item 7).

We had no static application security testing at all. `security.yml` covers
dependency review, a regex secret sweep and workflow linting — none of which
reads application logic. That is a real gap on a codebase whose control plane
handles checkout, Stripe webhooks and refunds, where the interesting bugs are
taint-flow bugs (untrusted request field reaching a query or a shell) that
regex scanning cannot see.

Running **non-gating on purpose**: schedule plus manual dispatch only, never on
`pull_request`, with `continue-on-error` on analysis. It cannot block a merge
or become a required check during the trial.

**Review:** 2026-08-24. Promote to a required PR check only if the
false-positive rate is low enough to triage weekly without eroding trust in the
signal. Criteria in `operations/architect-checklist/2026-W31.md`.

### Assess — Kimi K3 as an agentic coding model

Detailed entry retained at [`KIMI_K3_TECH_RADAR.md`](../KIMI_K3_TECH_RADAR.md).
Position unchanged: evaluate in a sandboxed lane against our own task suite;
not a default production model. Its published benchmarks remain promising
rather than production-proven.

### Adopt — Governed agent execution with a human approval gate

Not a vendor choice — our own pattern, and the one architectural decision in
this repo that has held up best.

`clearglass-commerce/control-plane/app/governance.py` scores every proposed
action and routes it by risk tier: low auto-executes, medium queues, high and
critical block until an `approvals` row is approved. Unknown actions default to
**high** — it fails closed. `app/security.py` refuses to boot a production
deployment with no `ADMIN_API_KEY`. `sentinel/sentinel/policy.py` and
`rbac.py` apply the same fail-closed posture to retrieval.

New agent-facing surfaces should route through this pattern rather than invent
a parallel one. The gap — agent permission declarations that are *not* wired to
this enforcement — is recorded as this week's checklist item 3.

---

## Supply chain

### Adopt — SHA-pinned GitHub Actions

All 49 workflows pin every third-party action to a full 40-character commit
SHA; the only unpinned `uses:` are local `./` paths, which is correct. This is
already the house standard and this week's audit found no drift. Keep it that
way — a tag-pinned action is a mutable dependency with write access to CI.

### Adopt — Keyless OIDC signing + SLSA provenance on release

`release-supply-chain.yml`. Producing side is in force; see the Kyverno entry
above for what is *not* yet verified.

### Trial — Least-privilege secret binding at step scope

Tightened this week: `CG_ORG_PAT`, the broadest credential in the repo, moved
from job-level `env:` (visible to every step, including `pip install` and
`apt-get`) to the two steps that call the GitHub API. Extending this pattern to
the remaining secret-bearing workflows is tracked in the week-31 checklist.

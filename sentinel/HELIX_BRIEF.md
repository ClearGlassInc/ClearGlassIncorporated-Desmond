# HELIX — dual-strand exposure & response lattice

> Leak/extortion exposure link analysis **fused with** agent-based society
> simulation: the exposure seeds a synthetic population, the simulation returns
> a blast radius, and the blast radius re-ranks severity — which decides which
> response actions unlock and which stay blocked pending human approval.
> Executable: `sentinel/sentinel/helix.py` · tests: `sentinel/tests/test_helix.py`
> · operator surface: `helix.html` · self-check: `python -m sentinel.helix --json`.

## What this merges

Two products normally sold separately, joined at the point where they actually
answer each other's question:

| Strand | Lens | Question it answers |
|---|---|---|
| **A — Exposure Lattice** | Dark-web / leak-index link analysis | *What is exposed, who is claiming it, and where is the campaign in its arc?* |
| **B — Society Lattice** | Agent-based population simulation | *Who finds out, how fast, and what happens when they do?* |

Neither is decisive alone. A severe leak nobody hears about is a smaller problem
than a modest one that reaches every regulator and customer in nine steps. The
**crossover** is the product: exposure seeds propagation, propagation returns
reach, reach re-ranks severity, severity routes the response through the gate.

The demo case is deliberately moderate. On the raw signals it scores **72** —
serious, not dramatic. Simulated reach carries it to **92**, which is the
threshold where regulatory notification and a public statement enter the
playbook at all — and both arrive **BLOCKED**.

## DARPA lineage — mapped to mechanisms, not slogans

| Program | Concretely, in this module |
|---|---|
| **MEMEX** | `SignalIntake` — domain-specific exposure discovery over an *injected* fetch boundary |
| **GARD** | `SignalIntake._adversarial` — poisoned, injected and back-dated signals are quarantined before they can touch a score |
| **HIVE** | `Lattice` — typed graph analytics: weighted degree centrality, components, shortest blast paths |
| **KAIROS** | `SchemaInducer` — complex-event schema induction: where a campaign sits in its arc and what step is predicted next |
| **AIDA** | `HypothesisEngine` — competing hypotheses retained with calibrated confidence; never silently collapsed to one story |
| **SocialSim** | `Society.simulate` — cohort-level information propagation |
| **Ground Truth** | `calibrate` — the simulator is scored against held-out observations and a badly calibrated model is *forbidden* from reporting high confidence |
| **XAI** | every score carries a `rationale` string; no unexplained numbers |
| **Transparent Computing** | hash-chained `AuditLog` provenance on every material step |

## Deliberate guardrails

These are charter constraints inherited from SENTINEL, enforced in code and
covered by tests — not documentation promises.

- **No person nodes.** `Lattice.add_node` rejects `person`/`individual`/`human`/
  `people`, the same rule `graph.EntityGraph` enforces. Strand B is built from
  *synthetic cohort statistics*; sampled personas carry `synthetic=True` and
  correspond to no real individual. The reference product this borrows its
  society view from simulates **named real people** — HELIX deliberately does
  not, which removes the PII liability and is what makes it sellable into
  regulated buyers.
- **No collection here.** HELIX never opens a socket. A `Fetcher` is injected, so
  robots.txt / ToS / rate-limit / legal-authority compliance is enforced at the
  collector boundary and cannot be bypassed by this module. A fetch that raises
  fails **closed**.
- **Derived notifications, not stolen material.** The approved source registry
  covers our own telemetry, contracted monitoring vendors, CERT/ISAC notices, LE
  victim notifications, public breach indexes and vulnerability intel. Signals
  from anywhere else are quarantined, not down-weighted.
- **No high-risk auto-execution.** Public statements, mass outbound notice,
  regulatory filings, takedown demands and law-enforcement referral are always
  human-gated. An **unknown** action scores 100 and is blocked — never treated
  as harmless.

## Governance bands

Mirrors the commerce control plane's doctrine so one number means one thing
across the monorepo:

| Risk | Verdict | Behaviour |
|---|---|---|
| ≤ 35 | `AUTO` | reversible and internal — executes and logs |
| 36–69 | `APPROVE` | queued for human approval |
| ≥ 70 | `BLOCKED` | blocked until an approval record reaches `approved` |

An approval *reference* is evidence, not authorization: passing `approval_ref`
to a risk-85 action still returns `BLOCKED`. The gate is the authority.

## The Ground Truth rule

A simulator that has never been scored is capped at `UNVERIFIED` — it does not
get the benefit of the doubt. Scoring against held-out `(seeds, observed_reach)`
pairs earns a ceiling: MAE ≤ 0.10 → `HIGH`, ≤ 0.20 → `MEDIUM`, worse → `LOW`.
The reported forecast confidence is the **minimum** of the severity band and
that ceiling, so a confident-looking severity can never smuggle in an
uncalibrated forecast.

## Running it

```bash
cd sentinel
python -m sentinel.helix              # narrated assessment + invariant self-check
python -m sentinel.helix --json       # machine-readable, non-zero exit on violation
python -m pytest tests/test_helix.py -q
ruff check sentinel/helix.py tests/test_helix.py
```

The self-check asserts, and CI fails on violation of, these invariants:

1. adversarial signals are quarantined (future timestamp, prompt injection,
   unapproved source)
2. clean signals are accepted
3. no high-risk response auto-executes
4. every action at or above the block floor is `BLOCKED`
5. competing hypotheses are retained (≥ 2)
6. the forecast never exceeds its calibration ceiling
7. person nodes are rejected
8. blast radius stays a bounded fraction
9. the audit chain verifies

## Operator surface

`helix.html` is the analyst canvas for this engine. Every constant on the page —
cohorts, transmission channels, campaign arcs, response risk scores, governance
bands — mirrors `helix.py`, so the picture and the engine cannot disagree.

- **Exposure lattice (strand A):** force-directed link canvas with radial
  campaign bursts, force/radial/cluster layouts, filter, node inspector.
- **Society 3D (strand B):** hand-rolled 3D projection of cohort hubs and their
  synthetic member clouds, orbit/zoom, cohort legend, grouping control, and a
  synthetic-persona card for message rehearsal.
- **Transport:** the timeline is the *propagation* clock. Pressing play spreads
  awareness through the society while severity climbs and the response playbook
  expands — every newly unlocked action arriving `BLOCKED`.

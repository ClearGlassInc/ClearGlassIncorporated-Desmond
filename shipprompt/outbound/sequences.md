# ShipPrompt Outbound Sequences

Ready-to-send copy for cold email, LinkedIn, and warm referral. Personalize
the bracketed fields. Cap each thread at 3 touches across 9 days.

---

## A. Cold email — Series A AI startup CTO

### A1 · Touch 1 (Day 0) — pattern interrupt + offer

**Subject:** Your prompts probably live in 4 places

Hi [First name],

I run audits for AI startups that have shipped LLM features but haven't
hired an MLOps lead yet. Recurring pattern: deployment is one engineer's
bash script, prompts are spread across the repo + Notion + a Google Doc
+ Slack DMs, and there's no rollback when a prompt change tanks quality.

If that sounds familiar, I do a 48-hour audit for $4,500. You get a
40-point scorecard, a written remediation plan with dollar-impact, and a
Loom walkthrough. The fee credits 100% to a follow-on sprint if you want
implementation.

Worth 15 minutes to see whether [Company] is actually exposed?

— [Your name]
[your.email]
ClearGlass Inc. · ShipPrompt
https://clearglassinc.github.io/shipprompt/

### A2 · Touch 2 (Day 4) — value drop, no ask

**Subject:** Re: Your prompts probably live in 4 places

[First name] — figured I'd just send the checklist instead of pinging you
again. The 40-point ShipPrompt audit, free:

https://clearglassinc.github.io/shipprompt/audit-checklist.md

Run it on your repo. If you score below 28, the audit is worth a call.
If not, you've got a free clean bill of health. Either way, fine by me.

— [Your name]

### A3 · Touch 3 (Day 9) — close the loop

**Subject:** Closing the loop

[First name] — last note from me. If LLM deploy + prompt-ops isn't a Q1
priority, totally understood. If it becomes one, the door's open and the
next audit slot is [date]. Otherwise I'll stop the bothering.

— [Your name]

---

## B. Cold email — Head of ML at scale-up (Series B/C)

### B1 · Touch 1

**Subject:** SOC 2 + EU AI Act + 14 prompts in production

Hi [First name],

[Company] is in the SOC-2 / EU-AI-Act zone where auditors will start
asking for prompt lineage and model-change attribution. Most teams
discover during the audit that they can't produce either.

I do a 48-hour pre-audit audit ($4,500) that scores your repo against the
40-point ShipPrompt checklist and produces a SOC-2/EU-AI-Act-aligned
evidence-readiness plan. Output is a single PDF + Loom your auditor or
GRC lead will love.

15 minutes worth your time?

— [Your name]
ClearGlass Inc. · ShipPrompt
https://clearglassinc.github.io/shipprompt/

---

## C. LinkedIn DM — short, after a connection accept

Hey [First name] — thanks for the connect. Quick context: I run 72-hour
MLOps + prompt-ops sprints for AI teams that have shipped models but
haven't hired a platform engineer yet. Audits are $4,500 / 48 hours,
sprints are $14,500 / 72 hours. If [Company] is in that zone, happy to
send the 40-point checklist so you can self-score first. No pitch unless
you want one.

---

## D. Warm referral request — to portfolio operator / investor

**Subject:** Quick intro request — ShipPrompt

Hey [First name],

Quick ask. I'm running ShipPrompt — 72-hour MLOps + prompt-ops sprints
for AI startups that have models in prod but no MLOps hire. Audits are
$4,500, sprints $14,500. Sweet spot is Series A–C, 15–80 engineers,
shipped LLM features, no platform engineer yet.

Three companies in your portfolio I'd love a warm intro to if you think
the timing is right:

  1. [Company A] — [reason: e.g. "saw they're hiring an MLOps lead, can
     bridge the gap until that hire lands"]
  2. [Company B] — [reason]
  3. [Company C] — [reason]

Happy to send a 1-paragraph blurb you can forward. No worries if any of
these are off-limits.

— [Your name]

---

## E. X / Twitter teardown thread (lead-gen)

**Hook (post 1):**
> I audited 5 Series A AI startups' LLM deploy pipelines. Same 4 problems
> in every single one. A 🧵

**Post 2:** Deployment is one engineer's bash script. When that engineer
is on a flight, the model can't ship. Bus factor: 1.

**Post 3:** Prompts live in 4 places: code, Notion, a Google Doc, and
Slack DMs. Nobody can produce a definitive list of what's in production.

**Post 4:** No rollback. Last week's prompt change tanked quality, and the
only "fix" was "remember what it said yesterday." That's not a rollback.
That's a memory test.

**Post 5:** No eval-on-PR. Quality regressions ship to prod. You find out
from a customer email. By then you've burned trust *and* tokens.

**Post 6:** I built a free 40-point checklist that scores any repo
against this. If you're under 28/40, you have material risk. Link in
reply.

**Post 7 (CTA):** Free checklist:
https://clearglassinc.github.io/shipprompt/audit-checklist.md
A paid 48-hour audit (with a remediation plan + Loom) is $4,500:
https://clearglassinc.github.io/shipprompt/

---

## F. Hacker News "Show HN" post

**Title:** Show HN: ShipPrompt — opinionated prompt-ops + model-deploy CLI

**Body:**
Hi HN — I've been doing MLOps audits for AI startups that have shipped
LLM features but haven't hired a platform engineer. Same pattern every
time: prompts in 4 places, deploy is a bash script, no rollback, no
eval-on-PR.

shipprompt-starter is the scaffold I install during paid sprints. It's
MIT-licensed and lives at:

[link to repo]

Three rules:
  - prompts are content-addressed and versioned in git, never edited in place
  - the deploy manifest is the only thing the runtime trusts
  - rollback = restore previous manifest

The CLI is single-file Python. The deploy workflow is a single GitHub
Actions YAML. The whole thing is < 600 lines.

Happy to discuss design choices. The paid product is the 72-hour sprint
that embeds this and tunes it to your stack — but the scaffold itself is
free.

---

## G. Follow-up after audit delivery (turn audit → sprint)

**Subject:** Your ShipPrompt audit — and the 30/60/90

Hi [First name],

Audit attached. TL;DR: you scored [X] / 40. The three highest-leverage
fixes are:

  1. [Item] — saves ~$[N]/mo and unblocks SOC 2 evidence #4 and #7.
  2. [Item] — closes a prompt-injection vector our canary flagged.
  3. [Item] — gets you eval-on-PR so the next regression doesn't reach prod.

I quoted the Sprint at $14,500 for 72 hours of hands-on implementation
(prompt registry → CI/CD → eval harness → rollback → hardening →
runbook). Your audit fee credits 100% if you decide within 14 days.

Slot still available [date range]. Want me to hold it?

— [Your name]

---

## Cadence & metrics

| Channel | Volume / week | Reply target | Booking target |
|---|---|---|---|
| Cold email (A/B) | 200 | 8–12% | 1–2 audits |
| LinkedIn DM (C) | 60 | 20% | 1 audit |
| Warm referral (D) | 5 | 60% | 1 sprint |
| X/HN/MLOps Slack (E/F) | 1 thread/post | — | inbound 1–2 |
| Audit → Sprint (G) | 100% of audits | n/a | 50%+ conversion |

Stop sending if open rate < 35% or reply rate < 5% over 100 sends — fix
the subject line and re-test.

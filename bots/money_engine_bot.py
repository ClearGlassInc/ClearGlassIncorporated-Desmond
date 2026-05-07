"""
ClearGlass Inc. — Money Engine Bot
Tracks KPIs, generates daily action summaries, and outputs fresh outreach templates.
Run daily via GitHub Actions or locally: python -m bots.money_engine_bot
"""
from __future__ import annotations

import json
import os
import random
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "marketing" / "output"
ARCHIVE_DIR = OUTPUT_DIR / "archive"


# ---------------------------------------------------------------------------
# Configuration — override via env vars
# ---------------------------------------------------------------------------

@dataclass
class EngineConfig:
    # Weekly KPI targets
    outreach_target: int = int(os.getenv("OUTREACH_TARGET", "30"))
    proposal_close_pct: float = float(os.getenv("PROPOSAL_CLOSE_PCT", "0.15"))
    effective_hourly_rate: float = float(os.getenv("EFFECTIVE_HOURLY_RATE", "150"))
    content_pieces_target: int = int(os.getenv("CONTENT_PIECES_TARGET", "5"))
    discovery_calls_target: int = int(os.getenv("DISCOVERY_CALLS_TARGET", "2"))
    mrr_weekly_target: float = float(os.getenv("MRR_WEEKLY_TARGET", "500"))

    # Weekly actuals (supply via env to get real tracking)
    outreach_actual: int = int(os.getenv("OUTREACH_ACTUAL", "0"))
    proposals_sent: int = int(os.getenv("PROPOSALS_SENT", "0"))
    proposals_closed: int = int(os.getenv("PROPOSALS_CLOSED", "0"))
    content_actual: int = int(os.getenv("CONTENT_ACTUAL", "0"))
    calls_actual: int = int(os.getenv("CALLS_ACTUAL", "0"))
    mrr_actual: float = float(os.getenv("MRR_ACTUAL", "0"))
    hours_worked: float = float(os.getenv("HOURS_WORKED", "0"))
    revenue_earned: float = float(os.getenv("REVENUE_EARNED", "0"))

    # Projection toggles
    start_date: str = os.getenv("ENGINE_START_DATE", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    operator_name: str = os.getenv("OPERATOR_NAME", "ClearGlass Founder")


# ---------------------------------------------------------------------------
# KPI Analysis
# ---------------------------------------------------------------------------

@dataclass
class KPIResult:
    label: str
    target: float
    actual: float
    unit: str
    status: str          # green / yellow / red
    advice: str


def analyse_kpis(cfg: EngineConfig) -> list[KPIResult]:
    effective_rate = cfg.revenue_earned / cfg.hours_worked if cfg.hours_worked > 0 else 0
    close_rate = cfg.proposals_closed / cfg.proposals_sent if cfg.proposals_sent > 0 else 0

    def graded(actual: float, target: float, invert: bool = False) -> str:
        ratio = actual / target if target > 0 else 0
        if invert:
            ratio = 1 / ratio if ratio > 0 else 0
        if ratio >= 1.0:
            return "green"
        if ratio >= 0.65:
            return "yellow"
        return "red"

    results = [
        KPIResult(
            label="Outreach Touches",
            target=cfg.outreach_target,
            actual=cfg.outreach_actual,
            unit="/week",
            status=graded(cfg.outreach_actual, cfg.outreach_target),
            advice=(
                "Pipeline is healthy — maintain cadence."
                if cfg.outreach_actual >= cfg.outreach_target
                else f"Behind by {cfg.outreach_target - cfg.outreach_actual} touches. Batch 10 DMs each morning using your Instantly.ai sequence."
            ),
        ),
        KPIResult(
            label="Proposal Close Rate",
            target=cfg.proposal_close_pct * 100,
            actual=round(close_rate * 100, 1),
            unit="%",
            status=graded(close_rate, cfg.proposal_close_pct),
            advice=(
                "Close rate exceeds target — consider raising rates 15% on next proposal."
                if close_rate >= cfg.proposal_close_pct
                else "Review proposal structure. Add a 48-hr expiry clause and a Loom demo link to each open proposal."
            ),
        ),
        KPIResult(
            label="Effective Hourly Rate",
            target=cfg.effective_hourly_rate,
            actual=round(effective_rate, 2),
            unit="$/hr",
            status=graded(effective_rate, cfg.effective_hourly_rate),
            advice=(
                "Rate is healthy. Protect capacity — decline any project below this floor."
                if effective_rate >= cfg.effective_hourly_rate
                else "Effective rate below target. Audit where your hours are going. Raise rate on next new client by $25/hr."
            ),
        ),
        KPIResult(
            label="Content Pieces",
            target=cfg.content_pieces_target,
            actual=cfg.content_actual,
            unit="/week",
            status=graded(cfg.content_actual, cfg.content_pieces_target),
            advice=(
                "Content cadence strong — compound effect building."
                if cfg.content_actual >= cfg.content_pieces_target
                else f"Need {cfg.content_pieces_target - cfg.content_actual} more pieces. Use Taplio to batch-draft on Sunday for the week."
            ),
        ),
        KPIResult(
            label="Discovery Calls",
            target=cfg.discovery_calls_target,
            actual=cfg.calls_actual,
            unit="/week",
            status=graded(cfg.calls_actual, cfg.discovery_calls_target),
            advice=(
                "Good call volume. Focus on qualifying budget early."
                if cfg.calls_actual >= cfg.discovery_calls_target
                else "Not enough calls. Add Calendly link to LinkedIn banner and every outreach DM."
            ),
        ),
        KPIResult(
            label="New MRR Added",
            target=cfg.mrr_weekly_target,
            actual=cfg.mrr_actual,
            unit="$/week",
            status=graded(cfg.mrr_actual, cfg.mrr_weekly_target),
            advice=(
                "MRR on track. Prioritize retainer conversions over one-off projects."
                if cfg.mrr_actual >= cfg.mrr_weekly_target
                else f"${cfg.mrr_weekly_target - cfg.mrr_actual:.0f} MRR gap. Push one existing project client to convert to monthly retainer."
            ),
        ),
    ]
    return results


# ---------------------------------------------------------------------------
# Daily Action Generator
# ---------------------------------------------------------------------------

STREAM_1_ACTIONS = [
    "Apply to 3 Upwork AI/automation gigs — personalize each proposal with a specific insight about the client's stack",
    "Reach out to 5 Ontario CTOs on LinkedIn with the AI automation template (personalise the trigger line)",
    "Publish one technical post: 'How I automated [specific task] with Python + LLM in 2 hrs'",
    "Record a 90-second Loom of an existing AI pipeline (Artemis, Guardian) — add to proposal template",
    "Follow up on all open AI consulting proposals older than 48 hours — add a 24-hr close nudge",
    "Research 5 new target companies using Apollo.io — build next week's outreach batch",
    "Pitch one cold LinkedIn DM to a Series-A CTO with a specific AI pain point you observed",
    "Audit your Upwork profile — update portfolio with latest Artemis/StegoForge screenshots",
]

STREAM_2_ACTIONS = [
    "Send 3 Fractional CISO outreach DMs to startups with no listed security lead (use LinkedIn People filter)",
    "Write a LinkedIn post: '3 security gaps I see in Ontario Series-A startups' — drives inbound authority",
    "Submit a Clarity.fm profile — security advisory calls at $150–$300/hr, immediate bookings",
    "Research one prospect's compliance posture (SOC 2, ISO 27001 status) — personalize your CISO pitch",
    "Publish a short Substack: 'Zero-trust checklist for Ontario SaaS — 5 things to fix before your next enterprise deal'",
    "Reach out to 2 warm contacts who work in startup ecosystems — ask for intro to CTOs they know",
    "Follow up on CISO proposals — include a 'Security Gap Assessment Framework' PDF as a value-add nudge",
    "Submit a talk proposal to a Toronto or Hamilton tech meetup on AI + cybersecurity convergence",
]

STREAM_3_ACTIONS = [
    "Spend 45 min on your SaaS landing page — write the headline, 3 bullets, and pricing table",
    "Set up a Stripe checkout link for your SaaS micro-product beta — even a $29 plan ships value",
    "Submit a ProductHunt teaser post — 'Coming soon: [tool name] — [one sentence pitch]'",
    "Post your tool's GitHub repo with a great README — drive organic discovery and social proof",
    "DM 10 developers or startup founders: 'I built [tool] for [problem] — want early access at 50% off?'",
    "Write an AppSumo pitch draft — they want: problem, solution, traction, founder credibility",
    "Enable GitHub Sponsors on your profile — link from clearglassinc.github.io",
    "Research 3 competing tools on Product Hunt — identify gaps your tool fills, update your positioning",
]

AI_TOOL_TIPS = [
    "Use Claude today: paste your latest proposal into Claude and ask it to 'identify 3 objection points a CFO would raise and suggest responses'",
    "Batch your LinkedIn content with Taplio: spend 30 min drafting 7 posts, schedule them for the week",
    "Run an Apollo.io search: Ontario tech companies, 10–50 employees, founded after 2020, no CISO listed",
    "Set up one n8n automation today: trigger → new Calendly booking → auto-send onboarding email with intake form link",
    "Record a Loom: walk through your Guardian dashboard for 90 seconds — use it as your email signature this week",
    "Use Perplexity to research your top 3 target companies: recent funding, product launches, security incidents",
    "Open Instantly.ai and check your sequence analytics — identify which subject line has the highest open rate",
    "Use Claude to convert one of your existing docs/scripts into a public case study blog post",
]


def pick_daily_actions(day_of_week: int) -> dict:
    """Generate a prioritized daily action list based on day of week."""
    random.seed(day_of_week)
    return {
        "stream_1": random.choice(STREAM_1_ACTIONS),
        "stream_2": random.choice(STREAM_2_ACTIONS),
        "stream_3": random.choice(STREAM_3_ACTIONS),
        "ai_tool": random.choice(AI_TOOL_TIPS),
        "non_negotiable": "Log today's actions in your CRM or Notion tracker before end of day — what you don't measure, you don't improve.",
    }


# ---------------------------------------------------------------------------
# Outreach Template Generator
# ---------------------------------------------------------------------------

AI_CONSULTING_HOOKS = [
    "just raised your Series A",
    "recently hired a VP of Engineering",
    "launched a new product last quarter",
    "are growing your dev team fast",
    "are scaling your data pipeline",
]

CISO_PAIN_POINTS = [
    "enterprise sales cycles slow down when security questionnaires hit",
    "SOC 2 Type II readiness is becoming a table-stakes ask from enterprise buyers",
    "your AWS/Azure security posture may have gaps that would surprise an auditor",
    "incident response playbooks are missing at most Ontario startups until it's too late",
]


def generate_outreach_templates(company: str = "[Company]", contact: str = "[FirstName]") -> dict:
    hook = random.choice(AI_CONSULTING_HOOKS)
    pain = random.choice(CISO_PAIN_POINTS)

    ai_template = f"""Subject: Quick question about {company}'s AI stack

Hey {contact},

Noticed {company} {hook} — congrats on the momentum.

I architect AI automation pipelines for Ontario-based tech companies. Recent outcomes:
- 60–80% reduction in manual ops time using LLM + Python pipelines
- Agentic workflows for data ingestion, security triage, and customer communications
- 4–6 week delivery sprints with full handoff documentation

Are you currently evaluating where AI can remove bottlenecks in your engineering or ops stack?

Happy to share a 5-min Loom showing how I'd approach your setup — no pitch deck required.

— [Your Name]
ClearGlass Inc. | clearglassinc.github.io"""

    ciso_template = f"""Subject: Security gap I noticed at {company} — quick flag

Hey {contact},

I work with Ontario SaaS companies at your stage on fractional security leadership. Quick observation: {pain}.

Fractional CISO services I offer (10–15 hrs/month):
✓ Threat modelling and zero-trust architecture review
✓ SOC 2 Type II readiness roadmap
✓ Vendor and third-party security assessments
✓ Incident response playbook development

Most clients see ROI when they close their first enterprise deal — security questionnaires get fast-tracked.

Worth a 20-minute call to see if there's a fit? No obligation — I'll share our security gap assessment framework just for showing up.

— [Your Name]
ClearGlass Inc. | clearglassinc.github.io"""

    return {"ai_consulting": ai_template, "fractional_ciso": ciso_template}


# ---------------------------------------------------------------------------
# Income Projection Model
# ---------------------------------------------------------------------------

@dataclass
class StreamProjection:
    name: str
    month_1_low: float
    month_1_high: float
    month_2_low: float
    month_2_high: float
    month_3_low: float
    month_3_high: float
    key_lever: str


def get_projections() -> list[StreamProjection]:
    return [
        StreamProjection(
            name="AI Automation Consulting",
            month_1_low=4000, month_1_high=10000,
            month_2_low=8000, month_2_high=18000,
            month_3_low=12000, month_3_high=25000,
            key_lever="2–3 retainer clients at $3k–$8k/mo each",
        ),
        StreamProjection(
            name="Fractional CISO / Security",
            month_1_low=3000, month_1_high=7000,
            month_2_low=5000, month_2_high=12000,
            month_3_low=8000, month_3_high=18000,
            key_lever="Blend of retainer + one-time pentest/audit engagements",
        ),
        StreamProjection(
            name="SaaS Micro-Products",
            month_1_low=500, month_1_high=2000,
            month_2_low=1500, month_2_high=4000,
            month_3_low=3000, month_3_high=8000,
            key_lever="AppSumo launch + growing MRR base",
        ),
    ]


# ---------------------------------------------------------------------------
# Report Builder
# ---------------------------------------------------------------------------

def status_icon(status: str) -> str:
    return {"green": "✅", "yellow": "⚠️", "red": "🔴"}.get(status, "—")


def build_markdown(cfg: EngineConfig, kpis: list[KPIResult], actions: dict, templates: dict) -> str:
    now_utc = datetime.now(timezone.utc)
    projections = get_projections()
    totals = {
        "m1": (sum(p.month_1_low for p in projections), sum(p.month_1_high for p in projections)),
        "m2": (sum(p.month_2_low for p in projections), sum(p.month_2_high for p in projections)),
        "m3": (sum(p.month_3_low for p in projections), sum(p.month_3_high for p in projections)),
    }

    kpi_rows = "\n".join(
        f"| {k.label} | {k.target}{k.unit} | {k.actual}{k.unit} | {status_icon(k.status)} {k.status.upper()} | {k.advice} |"
        for k in kpis
    )

    proj_rows = "\n".join(
        f"| {p.name} | ${p.month_1_low/1000:.0f}k–${p.month_1_high/1000:.0f}k | ${p.month_2_low/1000:.0f}k–${p.month_2_high/1000:.0f}k | ${p.month_3_low/1000:.0f}k–${p.month_3_high/1000:.0f}k | {p.key_lever} |"
        for p in projections
    )

    return f"""# ClearGlass Inc. — Money Engine Report
**Generated:** {now_utc.replace(microsecond=0).isoformat()} UTC
**Operator:** {cfg.operator_name}
**Engine Start Date:** {cfg.start_date}

---

## 1. Weekly KPI Dashboard

| Metric | Target | Actual | Status | Advice |
|---|---|---|---|---|
{kpi_rows}

---

## 2. Income Projections

| Stream | Month 1 | Month 2 | Month 3 | Key Lever |
|---|---|---|---|---|
{proj_rows}
| **COMBINED** | **${totals['m1'][0]/1000:.1f}k–${totals['m1'][1]/1000:.0f}k** | **${totals['m2'][0]/1000:.1f}k–${totals['m2'][1]/1000:.0f}k** | **${totals['m3'][0]/1000:.0f}k–${totals['m3'][1]/1000:.0f}k** | Pipeline + automation |

---

## 3. Today's Action Pack

### Stream 01 · AI Automation Consulting
{actions['stream_1']}

### Stream 02 · Fractional CISO / Security
{actions['stream_2']}

### Stream 03 · SaaS Micro-Products
{actions['stream_3']}

### AI Tool Focus
{actions['ai_tool']}

### Non-Negotiable
{actions['non_negotiable']}

---

## 4. Fresh Outreach Templates

### AI Consulting Template
```
{templates['ai_consulting']}
```

### Fractional CISO Template
```
{templates['fractional_ciso']}
```

---

## 5. Red Flags — Quick Reference

| Flag | What It Looks Like | Action |
|---|---|---|
| Open-scope fixed price | "Pay $2k for the whole thing" with no defined scope | Define deliverables before price or walk away |
| Unpaid test project | "Do a small sample first" from a stranger | Send case studies + Loom instead |
| Equity-only offers | "We'll give you 0.5% for the build" | Pass — equity from pre-revenue is $0 today |
| Low-rate platforms | Fiverr, PeoplePerHour, Freelancer.com | Stick to Toptal, Arc.dev, Contra, direct BD |
| NDA resistance | Client won't sign mutual NDA | Don't share systems or strategy without NDA |
| Scope creep | "While you're at it, can you also..." | Invoke change-order clause — new quote within 24 hrs |

---

## 6. 30-Day Milestone Checklist

- [ ] Day 1: Profiles live on LinkedIn, Upwork, Toptal, Contra, Arc.dev
- [ ] Day 2: 3 case studies drafted + Loom demo recorded
- [ ] Day 3: 30-target prospecting list built in Apollo.io
- [ ] Day 4: First outreach wave sent (10 warm + 10 cold + Upwork bids)
- [ ] Day 5: Content engine running (5 posts/week scheduled)
- [ ] Day 6: Proposal template + PDF deck ready
- [ ] Day 7: First proposal sent, deposit requested
- [ ] Day 14: 1 signed contract + deposit in hand
- [ ] Day 21: 2nd client closed or 2nd proposal in negotiation
- [ ] Day 30: $7.5k+ contracted revenue + SaaS product live

---

*ClearGlass Inc. · Money Engine Bot · clearglassinc.github.io/money-engine.html*
"""


# ---------------------------------------------------------------------------
# Output Writer
# ---------------------------------------------------------------------------

def write_outputs(cfg: EngineConfig, kpis: list[KPIResult], actions: dict, templates: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    now_utc = datetime.now(timezone.utc).replace(microsecond=0)
    stamp = now_utc.isoformat().replace("+00:00", "Z").replace(":", "")

    md = build_markdown(cfg, kpis, actions, templates)
    payload = {
        "generated_utc": now_utc.isoformat(),
        "config": asdict(cfg),
        "kpis": [asdict(k) for k in kpis],
        "daily_actions": actions,
        "outreach_templates": templates,
        "projections": [asdict(p) for p in get_projections()],
    }

    (OUTPUT_DIR / "money_engine_latest.md").write_text(md, encoding="utf-8")
    (OUTPUT_DIR / "money_engine_latest.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (ARCHIVE_DIR / f"money_engine_{stamp}.md").write_text(md, encoding="utf-8")


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cfg = EngineConfig()
    kpis = analyse_kpis(cfg)
    day_of_week = datetime.now(timezone.utc).weekday()
    actions = pick_daily_actions(day_of_week)
    templates = generate_outreach_templates()
    write_outputs(cfg, kpis, actions, templates)

    print("Money Engine Bot complete.")
    print(f"Output: {OUTPUT_DIR / 'money_engine_latest.md'}")
    print("\n── KPI Summary ──")
    for k in kpis:
        icon = status_icon(k.status)
        print(f"  {icon} {k.label}: {k.actual}{k.unit} (target {k.target}{k.unit})")
    print("\n── Today's Non-Negotiable ──")
    print(f"  {actions['non_negotiable']}")

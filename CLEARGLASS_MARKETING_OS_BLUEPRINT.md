# ClearGlass Marketing OS — Governed Multi-Agent Growth Command System

ClearGlass Marketing OS is the revenue-growth companion to the ClearGlassInc Artemis agent runtime. It coordinates specialist marketing bots that research, plan, create, distribute, measure, optimize, and govern campaigns for premium B2B cybersecurity, AI, OSINT, and advanced software systems.

The system is intentionally **not** a free-form content generator. It is a deterministic, governed operating model with explicit bot inputs, outputs, KPIs, handoffs, evidence requirements, and human approval gates for customer-visible or high-risk work.

## Operating Loop

```text
research -> strategy -> creation -> distribution -> measurement -> optimization -> repeat
```

Each cycle produces:

1. Weekly action plan.
2. Daily execution plan.
3. Performance report.
4. Next-step recommendations.
5. Shared-memory updates for hooks, objections, failed experiments, and conversion learnings.

## Bot Roster

| Bot | Responsibility | Primary outputs | KPI discipline |
| --- | --- | --- | --- |
| Market Intelligence Bot | Audience, pain point, competitor, keyword, and demand-signal research | Audience segments, keyword map, demand signals | Evidence coverage, segment confidence |
| Strategy Bot | Channel strategy, positioning, offers, campaign architecture | Positioning, campaign plan, offer strategy | Pipeline fit, offer clarity |
| Content Bot | Long-form, landing pages, emails, social, scripts | Draft assets and CTAs | Message consistency, asset completion |
| SEO Bot | Intent, metadata, schema, internal links | Metadata, schema plan, linking plan | Organic reach, indexability |
| Distribution Bot | Repurposing and channel adaptation | Channel variants and publishing calendar | Qualified engagement, CTR |
| Lead Bot | Lead magnets, funnels, CTAs, nurture, qualification | Lead magnet, funnel, scoring rules | MQL quality, conversion rate |
| Analytics Bot | Performance and attribution | Report, attribution view, retention signals | CAC, LTV, pipeline influence |
| Optimization Bot | Experiments and next-best action | Variant comparison, bottleneck diagnosis | Lift, learning velocity |
| Compliance Bot | Brand, factuality, legal, platform-policy review | Approval decision, risk notes | Claim accuracy, policy pass rate |

## Shared Memory Schema

The Python runtime stores campaign memory as structured fields rather than unbounded notes:

```python
MarketingMemory(
    audience_insights=["CISOs respond to auditability over generic AI speed claims"],
    past_campaigns=["Q3 governed AI webinar"],
    top_hooks=["Machine speed without uncontrolled autonomy"],
    failed_experiments=["Generic AI productivity hook produced low-fit leads"],
    objections=["How is this governed and auditable?"],
    conversion_data={"landing_conversion": 0.047},
    content_inventory=["/artemis-os.html", "/CLEARGLASSINC_ARTEMIS_PALANTIR_SELF_EVOLVING_AI_IMPLEMENTATION.md"],
)
```

## Campaign Output Contract

Every generated campaign must return the ten required operating fields:

1. Campaign objective.
2. Target audience.
3. Channel plan.
4. Hook and message angle.
5. Assets to produce.
6. Publishing sequence.
7. KPI targets.
8. Risks and constraints.
9. Experiment plan.
10. Weekly review and optimization recommendations.

The runtime implements this contract in `agent_os/marketing_os.py` as `CAMPAIGN_OUTPUT_FIELDS` and `CampaignPlan`.

## Governance Model

Marketing actions inherit the repository's fail-closed governance rules:

- Drafting and read-only analysis may proceed when evidence and confidence are present.
- Publishing content is reviewed as customer-visible work.
- Mass outbound sends are always gated.
- Unsupported claims are escalated rather than invented.
- Prompt, workflow, and routing changes are recommendations until a human approves rollout.

## Example Python Usage

```python
from agent_os.marketing_os import CampaignBrief, MarketingMemory, MarketingOS

brief = CampaignBrief(
    objective="book executive demos",
    product="ClearGlassInc Artemis",
    audience="CISOs and intelligence leaders",
    theme="governed AI intelligence operations",
    evidence=("approved architecture brief",),
)

memory = MarketingMemory(
    conversion_data={"landing_conversion": 0.04},
    content_inventory=["/artemis-os.html"],
)

plan = MarketingOS().build_campaign(brief, memory)
print(plan.to_dict())
```

## Human-in-the-Loop Self-Improvement

The platform gets better safely by turning campaign outcomes into reviewed updates:

1. Analytics Bot captures CTR, conversion, lead quality, attribution, objections, and pipeline movement.
2. Optimization Bot compares variants and proposes which hooks, channels, CTAs, and workflows should change.
3. Compliance Bot checks factuality, brand voice, legal exposure, and policy constraints.
4. Human operator approves or rejects proposed prompt, workflow, and campaign changes.
5. Approved lessons are promoted into shared memory; rejected experiments are retained with reason codes.
6. Future campaigns use the memory without autonomously changing business goals or guardrails.

## Mission Fit for ClearGlassInc Artemis

ClearGlass Marketing OS keeps the brand's technical authority intact by forcing each marketing output to connect to evidence, measurable business outcomes, governed handoffs, and explicit review gates. It is designed for premium B2B demand creation where trust, accuracy, and compounding authority matter more than high-volume vanity metrics.

# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""ClearGlass Marketing OS — governed multi-agent campaign runtime.

A deterministic, stdlib-only planning layer for marketing campaigns. It encodes
specialist bot responsibilities, shared memory shape, handoff order, required
campaign outputs, KPI discipline, and approval gates for customer-visible work.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, timedelta

from .governance import score_action

MARKETING_LOOP: tuple[str, ...] = (
    "research", "strategy", "creation", "distribution", "measurement",
    "optimization", "repeat",
)

CAMPAIGN_OUTPUT_FIELDS: tuple[str, ...] = (
    "campaign_objective", "target_audience", "channel_plan", "hook_and_message_angle",
    "assets_to_produce", "publishing_sequence", "kpi_targets", "risks_and_constraints",
    "experiment_plan", "weekly_review_and_optimization_recommendations",
)


@dataclass(frozen=True)
class MarketingBot:
    """Specialist bot definition with explicit inputs, outputs, and KPIs."""

    key: str
    name: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    kpis: tuple[str, ...]
    escalates_when: tuple[str, ...]


MARKETING_BOTS: dict[str, MarketingBot] = {
    bot.key: bot
    for bot in (
        MarketingBot(
            "market_intelligence", "Market Intelligence Bot",
            ("audience", "competitors", "search demand", "social signals", "sales notes"),
            ("audience segments", "pain points", "keyword map", "demand signals"),
            ("evidence coverage", "keyword opportunity", "segment confidence"),
            ("no current evidence", "competitor claim cannot be verified"),
        ),
        MarketingBot(
            "strategy", "Strategy Bot",
            ("research brief", "business objective", "offer constraints"),
            ("positioning", "channel strategy", "offer", "campaign plan"),
            ("pipeline fit", "offer clarity", "channel-priority score"),
            ("objective conflicts with brand", "offer needs executive approval"),
        ),
        MarketingBot(
            "content", "Content Bot",
            ("positioning", "technical source material", "brand voice"),
            ("blog drafts", "landing pages", "email sequences", "social copy", "scripts"),
            ("asset completion", "message consistency", "CTA coverage"),
            ("technical claim lacks source", "customer-visible claim is high risk"),
        ),
        MarketingBot(
            "seo", "SEO Bot",
            ("topic map", "draft assets", "site inventory"),
            ("metadata", "schema plan", "internal links", "search-intent alignment"),
            ("organic reach", "indexability", "SERP intent match"),
            ("keyword stuffing risk", "canonical conflict"),
        ),
        MarketingBot(
            "distribution", "Distribution Bot",
            ("approved assets", "channel constraints", "publishing calendar"),
            ("repurposed posts", "email sends", "blog schedule", "short-form variants"),
            ("publish consistency", "CTR", "qualified engagement"),
            ("mass outbound", "unapproved regulated claim"),
        ),
        MarketingBot(
            "lead", "Lead Bot",
            ("offer", "audience", "qualification criteria"),
            ("lead magnets", "landing funnel", "CTAs", "nurture sequence", "lead scoring"),
            ("MQL quality", "conversion rate", "sales acceptance"),
            ("pricing/payment change", "PII collection change"),
        ),
        MarketingBot(
            "analytics", "Analytics Bot",
            ("campaign events", "UTMs", "CRM data", "pipeline outcomes"),
            ("performance report", "attribution view", "retention signals"),
            ("CAC", "LTV", "pipeline influence", "conversion rate"),
            ("tracking gap", "privacy boundary uncertainty"),
        ),
        MarketingBot(
            "optimization", "Optimization Bot",
            ("performance report", "experiment history", "failure log"),
            ("variant comparison", "bottleneck diagnosis", "next best action"),
            ("lift", "learning velocity", "cycle time"),
            ("sample size too small", "risk of optimizing vanity metrics"),
        ),
        MarketingBot(
            "compliance", "Compliance Bot",
            ("all proposed assets", "source pack", "policy constraints"),
            ("brand review", "factuality check", "legal-risk notes", "approval decision"),
            ("claim accuracy", "policy pass rate", "rework rate"),
            ("unsupported factual claim", "legal or platform-policy risk"),
        ),
    )
}


@dataclass
class MarketingMemory:
    """Common memory schema shared by all marketing bots."""

    audience_insights: list[str] = field(default_factory=list)
    past_campaigns: list[str] = field(default_factory=list)
    top_hooks: list[str] = field(default_factory=list)
    failed_experiments: list[str] = field(default_factory=list)
    objections: list[str] = field(default_factory=list)
    conversion_data: dict[str, float] = field(default_factory=dict)
    content_inventory: list[str] = field(default_factory=list)


@dataclass
class CampaignBrief:
    """Minimal operator input required to generate an executable campaign plan."""

    objective: str
    product: str
    audience: str
    theme: str
    evidence: tuple[str, ...] = ()
    primary_channels: tuple[str, ...] = ("LinkedIn", "blog", "email")


@dataclass
class CampaignPlan:
    """The ten required outputs for every ClearGlass Marketing OS campaign."""

    campaign_objective: str
    target_audience: str
    channel_plan: list[str]
    hook_and_message_angle: str
    assets_to_produce: list[str]
    publishing_sequence: list[str]
    kpi_targets: dict[str, str]
    risks_and_constraints: list[str]
    experiment_plan: list[str]
    weekly_review_and_optimization_recommendations: list[str]
    bot_handoffs: list[dict[str, object]]
    governance: list[dict[str, object]]
    missing_inputs: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class MarketingOS:
    """Orchestrates governed marketing bots into a weekly campaign plan."""

    loop = MARKETING_LOOP
    bots = MARKETING_BOTS

    def build_campaign(self, brief: CampaignBrief, memory: MarketingMemory | None = None) -> CampaignPlan:
        memory = memory or MarketingMemory()
        missing = self._missing_inputs(brief, memory)
        start = date.today()

        handoffs = [
            {"bot": bot.name, "inputs": list(bot.inputs), "outputs": list(bot.outputs), "kpis": list(bot.kpis)}
            for bot in MARKETING_BOTS.values()
        ]
        governance = [
            score_action("draft_campaign", {"product": brief.product}, confidence=0.82, has_evidence=bool(brief.evidence)).to_dict(),
            score_action("publish_content", {"channels": list(brief.primary_channels)}, confidence=0.78, has_evidence=bool(brief.evidence)).to_dict(),
            score_action("send_outbound", {"audience": brief.audience}, confidence=0.74, has_evidence=bool(brief.evidence)).to_dict(),
        ]

        return CampaignPlan(
            campaign_objective=f"Grow qualified demand for {brief.product}: {brief.objective}",
            target_audience=brief.audience,
            channel_plan=[f"{channel}: evidence-backed authority asset plus conversion CTA" for channel in brief.primary_channels],
            hook_and_message_angle=(
                f"{brief.theme}: position ClearGlassInc Artemis as the premium governed intelligence system "
                "for teams that need speed, technical depth, and auditable control."
            ),
            assets_to_produce=[
                "pillar technical article", "executive landing page", "5-post LinkedIn sequence",
                "3-email nurture sequence", "lead magnet checklist", "demo qualification form",
            ],
            publishing_sequence=[
                f"{start.isoformat()}: compliance review source pack and claims matrix",
                f"{(start + timedelta(days=1)).isoformat()}: publish pillar article and landing page draft",
                f"{(start + timedelta(days=2)).isoformat()}: release LinkedIn post 1 and email 1",
                f"{(start + timedelta(days=4)).isoformat()}: publish proof/objection post and retargeting audience",
                f"{(start + timedelta(days=7)).isoformat()}: weekly review, variant decision, next sprint plan",
            ],
            kpi_targets={
                "qualified leads": "+15% week-over-week from target accounts",
                "landing conversion": "4-8% visitor-to-qualified-inquiry",
                "organic engagement": "save/comment/share quality over raw impressions",
                "sales acceptance": ">70% of MQLs accepted or routed with reason codes",
            },
            risks_and_constraints=[
                "Customer-visible publishing and outbound sends require human approval.",
                "Technical/security claims require source evidence and Compliance Bot sign-off.",
                "Do not optimize for vanity reach unless it improves qualified demand or authority.",
            ],
            experiment_plan=[
                "A/B test authority hook vs. operational-pain hook on LinkedIn and landing hero.",
                "Compare demo CTA vs. checklist lead magnet CTA by lead quality, not volume alone.",
                "Route low-confidence findings to research instead of inventing missing evidence.",
            ],
            weekly_review_and_optimization_recommendations=[
                "Review CTR, conversion, lead qualification, source objections, and pipeline movement.",
                "Promote winning hooks into shared memory and retire losing variants with reason codes.",
                "Propose prompt/workflow updates only as drafts requiring human approval before rollout.",
            ],
            bot_handoffs=handoffs,
            governance=governance,
            missing_inputs=missing,
        )

    @staticmethod
    def _missing_inputs(brief: CampaignBrief, memory: MarketingMemory) -> list[str]:
        missing: list[str] = []
        if not brief.evidence:
            missing.append("source evidence for technical, competitor, and demand claims")
        if not memory.conversion_data:
            missing.append("baseline conversion data for KPI calibration")
        if not memory.content_inventory:
            missing.append("content inventory for internal linking and repurposing")
        return missing

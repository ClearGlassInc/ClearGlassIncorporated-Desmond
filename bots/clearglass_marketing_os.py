# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""ClearGlass Marketing OS campaign planner.

This module provides a deterministic, repo-ready implementation skeleton for a
multi-agent marketing command system. It is intentionally stdlib-only so it can
run in CI, GitHub Actions, or local operator workstations without extra setup.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "marketing" / "os"


@dataclass(frozen=True)
class BotSpec:
    name: str
    responsibility: str
    inputs: list[str]
    outputs: list[str]
    kpis: list[str]


@dataclass
class MarketingMemory:
    audience_insights: list[dict[str, Any]] = field(default_factory=list)
    past_campaigns: list[dict[str, Any]] = field(default_factory=list)
    top_performing_hooks: list[str] = field(default_factory=list)
    failed_experiments: list[dict[str, Any]] = field(default_factory=list)
    objections: list[str] = field(default_factory=list)
    conversion_data: list[dict[str, Any]] = field(default_factory=list)
    content_inventory: list[dict[str, Any]] = field(default_factory=list)
    compliance_notes: list[str] = field(default_factory=list)
    approved_claims: list[str] = field(default_factory=list)


BOT_ROSTER: list[BotSpec] = [
    BotSpec(
        "Market Intelligence Bot",
        "Research audience segments, pain points, competitors, keywords, and demand signals.",
        ["business_goal", "target_audience", "market_notes", "customer_evidence"],
        ["audience_map", "competitor_gaps", "demand_signals", "keyword_themes"],
        ["evidence_quality", "icp_clarity", "opportunity_score"],
    ),
    BotSpec(
        "Strategy Bot",
        "Translate research into channel strategy, positioning, offers, and campaign plans.",
        ["intelligence_brief", "revenue_target", "constraints"],
        ["campaign_thesis", "channel_plan", "offer", "sequence"],
        ["strategic_fit", "pipeline_relevance", "feasibility"],
    ),
    BotSpec(
        "Content Bot",
        "Write long-form posts, landing pages, email sequences, social posts, and scripts.",
        ["strategy_brief", "brand_voice", "proof_points"],
        ["asset_briefs", "draft_copy", "creative_variants"],
        ["technical_accuracy", "hook_strength", "conversion_intent"],
    ),
    BotSpec(
        "SEO Bot",
        "Optimize topics, structure, internal linking, metadata, schema, and search intent.",
        ["content_drafts", "keyword_themes", "site_inventory"],
        ["seo_brief", "metadata", "faq_schema", "internal_links"],
        ["organic_reach", "intent_match", "serp_competitiveness"],
    ),
    BotSpec(
        "Distribution Bot",
        "Repurpose content for LinkedIn, X, email, blog, and short-form channels.",
        ["approved_content", "channel_rules"],
        ["publishing_pack", "repurposed_assets", "schedule"],
        ["qualified_reach", "engagement_rate", "click_through_rate"],
    ),
    BotSpec(
        "Lead Bot",
        "Create lead magnets, funnels, CTAs, nurture sequences, and qualification logic.",
        ["offer", "icp", "content_assets"],
        ["funnel_map", "cta_matrix", "qualification_rubric"],
        ["mql_rate", "demo_requests", "lead_quality"],
    ),
    BotSpec(
        "Analytics Bot",
        "Track performance, attribution, CTR, conversion, retention, and pipeline impact.",
        ["campaign_links", "event_stream", "crm_outcomes"],
        ["performance_report", "attribution_notes", "bottleneck_list"],
        ["conversion_rate", "sourced_pipeline", "attribution_confidence"],
    ),
    BotSpec(
        "Optimization Bot",
        "Run experiments, compare variants, identify bottlenecks, and recommend next action.",
        ["performance_report", "experiment_history"],
        ["test_backlog", "winner_recommendation", "next_best_action"],
        ["lift", "learning_velocity", "regression_avoidance"],
    ),
    BotSpec(
        "Compliance Bot",
        "Check brand voice, factual accuracy, legal risk, and policy constraints.",
        ["outbound_assets", "claim_register", "platform_policies"],
        ["approval_status", "required_edits", "escalations"],
        ["unsupported_claims", "policy_violations", "brand_consistency"],
    ),
]


def build_campaign(goal: str, audience: str, theme: str, memory: MarketingMemory | None = None) -> dict[str, Any]:
    memory = memory or MarketingMemory()
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    hook = f"{theme}: the hidden operating gap costing {audience} speed, trust, and revenue"
    return {
        "generated_at": now,
        "organization": "ClearGlassInc",
        "system": "ClearGlass Marketing OS",
        "operating_loop": ["research", "strategy", "creation", "seo", "compliance", "distribution", "measurement", "optimization"],
        "bot_tasks": [asdict(bot) for bot in BOT_ROSTER],
        "shared_memory_schema": asdict(memory),
        "campaign": {
            "campaign_objective": goal,
            "target_audience": audience,
            "channel_plan": {
                "website": "Publish a technical pillar page with proof, CTAs, FAQ schema, and internal links.",
                "linkedin": "Run executive posts, carousel summaries, and founder-led proof narratives.",
                "x": "Ship concise technical threads with one claim, one proof point, and one CTA per post.",
                "email": "Send a three-email sequence: problem framing, proof, and consultation CTA.",
                "partners": "Package the campaign as a partner briefing for cybersecurity, AI, and OSINT channels.",
            },
            "hook_and_message_angle": hook,
            "assets_to_produce": [
                "Technical pillar page",
                "Executive LinkedIn post",
                "Five-slide LinkedIn carousel outline",
                "Ten-post X thread",
                "Three-email nurture sequence",
                "Lead magnet checklist",
                "Landing page CTA block",
                "Weekly performance report",
            ],
            "publishing_sequence": [
                "Day 1: publish pillar page and analytics events",
                "Day 2: post LinkedIn thesis and X thread",
                "Day 3: send email 1 and launch lead magnet",
                "Day 4: publish carousel and partner briefing",
                "Day 5: send email 2 and review click/conversion data",
                "Day 7: send email 3 and produce optimization report",
            ],
            "kpi_targets": {
                "qualified_demo_requests": 5,
                "lead_magnet_conversion_rate": "3-8%",
                "email_click_rate": "2-5%",
                "linkedin_engagement_rate": "4-8%",
                "organic_keyword_themes": 5,
                "unsupported_claims": 0,
            },
            "risks_and_constraints": [
                "Do not claim unverified platform capabilities or customer outcomes.",
                "Escalate legal, regulated-security, or attribution claims to Compliance Bot.",
                "Separate authority metrics from revenue metrics in reporting.",
            ],
            "experiment_plan": [
                "A/B test contrarian vs. risk-reduction hooks on LinkedIn.",
                "A/B test checklist CTA vs. executive briefing CTA on the landing page.",
                "Compare technical proof-led email subject lines against pain-led subject lines.",
            ],
            "weekly_review_and_optimization_recommendations": [
                "Promote channels that generate qualified conversations, not raw impressions.",
                "Move winning hooks into shared memory and retire losing variants.",
                "Convert objections from sales calls into FAQ, email, and retargeting assets.",
            ],
        },
    }


def write_campaign(plan: dict[str, Any]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "latest_campaign.json"
    path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a ClearGlass Marketing OS campaign plan.")
    parser.add_argument("--goal", default="Grow qualified demand for ClearGlassInc AI, cybersecurity, and OSINT services.")
    parser.add_argument("--audience", default="B2B executives, security leaders, and technical buyers")
    parser.add_argument("--theme", default="Governed AI intelligence systems")
    args = parser.parse_args()
    output_path = write_campaign(build_campaign(args.goal, args.audience, args.theme))
    print(output_path.relative_to(ROOT))


if __name__ == "__main__":
    main()

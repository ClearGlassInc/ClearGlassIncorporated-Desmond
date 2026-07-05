# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""Tests for the Autonomous Agent OS runtime (agent_os/)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_os.governance import ALWAYS_ESCALATE, RiskTier, score_action  # noqa: E402
from agent_os.orchestrator import (  # noqa: E402
    DECISION_FRAMEWORK,
    EXECUTION_LOOP,
    OUTPUT_FIELDS,
    AgentOS,
    ProposedAction,
)
from agent_os.marketing_os import (  # noqa: E402
    CAMPAIGN_OUTPUT_FIELDS,
    MARKETING_BOTS,
    MARKETING_LOOP,
    CampaignBrief,
    MarketingMemory,
    MarketingOS,
)
from agent_os.planning import CycleError, Task, critical_path_minutes, plan_waves  # noqa: E402
from agent_os.roster import ROSTER  # noqa: E402
from agent_os.self_check import governance_selfcheck, main, structural_selfcheck  # noqa: E402


class TestGovernance:
    def test_low_risk_auto_executes(self) -> None:
        a = score_action("read_metrics", {}, confidence=0.9)
        assert a.tier is RiskTier.LOW
        assert a.requires_approval is False

    @pytest.mark.parametrize("action", sorted(ALWAYS_ESCALATE))
    def test_always_escalate_is_gated(self, action: str) -> None:
        assert score_action(action, {}, confidence=0.99).requires_approval is True

    def test_unknown_action_fails_closed(self) -> None:
        a = score_action("totally_unknown_action", {})
        assert a.requires_approval is True
        assert a.tier in (RiskTier.HIGH, RiskTier.CRITICAL)

    def test_missing_confidence_fails_closed(self) -> None:
        assert score_action("read_metrics", {}, confidence=None).requires_approval is True

    def test_missing_evidence_fails_closed(self) -> None:
        assert score_action("generate_copy", {}, has_evidence=False).requires_approval is True

    def test_large_price_delta_raises_score(self) -> None:
        base = score_action("update_catalog", {}, confidence=0.9).score
        bumped = score_action(
            "update_catalog", {"old_price": 100, "new_price": 130}, confidence=0.9
        ).score
        assert bumped > base


class TestPlanning:
    def test_waves_layer_dependencies(self) -> None:
        tasks = [Task("a"), Task("b", ("a",)), Task("c", ("b",)), Task("d", ("a",))]
        waves = plan_waves(tasks)
        assert waves[0] == ["a"]
        assert set(waves[1]) == {"b", "d"}
        assert waves[2] == ["c"]

    def test_cycle_fails_closed(self) -> None:
        tasks = [Task("a", ("b",)), Task("b", ("a",))]
        with pytest.raises(CycleError):
            plan_waves(tasks)

    def test_unknown_dependency_fails_closed(self) -> None:
        with pytest.raises(KeyError):
            plan_waves([Task("a", ("ghost",))])

    def test_critical_path(self) -> None:
        tasks = [Task("a", est_minutes=5), Task("b", ("a",), est_minutes=8)]
        assert critical_path_minutes(tasks) == 13


class TestRoster:
    def test_thirteen_agents(self) -> None:
        assert len(ROSTER) == 13

    def test_each_agent_has_outputs(self) -> None:
        for agent in ROSTER.values():
            assert agent.responsibilities
            assert agent.produces


class TestOrchestrator:
    def test_report_has_all_output_fields(self) -> None:
        report = AgentOS().run_mission("test objective").to_dict()
        for field_name in OUTPUT_FIELDS:
            assert field_name in report

    def test_gated_action_is_not_auto(self) -> None:
        report = AgentOS().run_mission(
            "obj",
            proposed_actions=[
                ProposedAction("generate_copy", confidence=0.9, evidence=("x",)),
                ProposedAction("update_pricing", confidence=0.9, evidence=("x",)),
            ],
        )
        vr = report.validation_results
        assert "update_pricing" in vr["gated_actions"]
        assert "update_pricing" not in vr["auto_actions"]
        assert "generate_copy" in vr["auto_actions"]

    def test_confidence_is_minimum_not_inflated(self) -> None:
        report = AgentOS().run_mission(
            "obj",
            proposed_actions=[
                ProposedAction("generate_copy", confidence=0.9, evidence=("x",)),
                ProposedAction("draft_plan", confidence=0.65, evidence=("y",)),
            ],
        )
        assert report.confidence_score == 0.65

    def test_deterministic(self) -> None:
        r1 = AgentOS().run_mission("same", tasks=[Task("a"), Task("b", ("a",))])
        r2 = AgentOS().run_mission("same", tasks=[Task("a"), Task("b", ("a",))])
        assert r1.to_dict() == r2.to_dict()

    def test_framework_and_loop_lengths(self) -> None:
        assert len(DECISION_FRAMEWORK) == 12
        assert len(EXECUTION_LOOP) == 9


class TestSelfCheck:
    def test_no_governance_violations(self) -> None:
        assert governance_selfcheck() == []

    def test_no_structural_violations(self) -> None:
        assert structural_selfcheck() == []

    def test_main_exits_zero(self) -> None:
        assert main([]) == 0
        assert main(["--json"]) == 0


class TestMarketingOS:
    def test_required_bot_roles_exist(self) -> None:
        assert len(MARKETING_BOTS) == 9
        for key in (
            "market_intelligence", "strategy", "content", "seo", "distribution",
            "lead", "analytics", "optimization", "compliance",
        ):
            assert key in MARKETING_BOTS
            assert MARKETING_BOTS[key].outputs
            assert MARKETING_BOTS[key].kpis

    def test_loop_matches_required_cycle(self) -> None:
        assert MARKETING_LOOP == (
            "research", "strategy", "creation", "distribution", "measurement",
            "optimization", "repeat",
        )

    def test_campaign_plan_has_required_outputs_and_gates_outbound(self) -> None:
        plan = MarketingOS().build_campaign(
            CampaignBrief(
                objective="book executive demos",
                product="ClearGlassInc Artemis",
                audience="CISOs and intelligence leaders",
                theme="governed AI intelligence operations",
                evidence=("approved architecture brief",),
            ),
            MarketingMemory(conversion_data={"landing_conversion": 0.04}, content_inventory=["/artemis-os.html"]),
        ).to_dict()
        for field_name in CAMPAIGN_OUTPUT_FIELDS:
            assert field_name in plan
        send = [g for g in plan["governance"] if g["action"] == "send_outbound"][0]
        assert send["requires_approval"] is True
        assert plan["missing_inputs"] == []

    def test_missing_evidence_is_explicit_not_invented(self) -> None:
        plan = MarketingOS().build_campaign(
            CampaignBrief(
                objective="increase authority",
                product="Artemis",
                audience="security buyers",
                theme="machine-speed operations",
            )
        )
        assert "source evidence for technical, competitor, and demand claims" in plan.missing_inputs

"""Tests for the morning sales-ops briefing — offline, in-memory SQLite, no network.

Proves the briefing computes real figures from seeded rows and never fabricates: with an empty
DB every section is zero/empty, and with seeded orders/payouts/approvals the numbers match.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Approval, Base, Event, Order, Payout
from app.sales_ops_briefing import compute_briefing, render_markdown

NOW = datetime(2026, 6, 15, 13, 0, tzinfo=timezone.utc)
YEST = NOW - timedelta(days=1)


def _session():
    engine = create_engine(
        "sqlite://", future=True, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)()


def test_empty_db_is_all_zero_and_marked_live() -> None:
    s = _session()
    b = compute_briefing(s, NOW, live=True)
    assert b.yesterday_revenue == 0.0
    assert b.mtd_revenue == 0.0
    assert b.new_deals == []
    assert b.stalled_deals == []
    assert b.at_risk_deals == []
    # Live but empty → the "no paid orders yesterday" action fires.
    assert any("No paid orders yesterday" in a for a in b.top_actions)


def test_revenue_and_new_deals_are_computed_from_orders() -> None:
    s = _session()
    # Two paid orders yesterday, one paid earlier this month, one pending (not revenue).
    s.add_all([
        Order(total=Decimal("100.00"), status="paid", source="ads", created_at=YEST),
        Order(total=Decimal("50.00"), status="paid", source="direct", created_at=YEST),
        Order(total=Decimal("25.00"), status="paid", created_at=NOW - timedelta(days=5)),
        Order(total=Decimal("999.00"), status="pending", created_at=YEST),
    ])
    s.commit()

    b = compute_briefing(s, NOW, live=True)
    assert b.yesterday_revenue == 150.0          # only the two paid-yesterday orders
    assert b.yesterday_orders == 2
    assert b.mtd_revenue == 175.0                # + the $25 from earlier this month
    assert len(b.new_deals) == 2
    assert b.new_deals[0]["amount"] == 100.0     # sorted desc
    # The pending order is NOT counted as revenue.
    assert b.mtd_revenue == 175.0


def test_stalled_at_risk_and_crm_issues() -> None:
    s = _session()
    s.add_all([
        Order(total=Decimal("200.00"), status="pending", created_at=NOW - timedelta(hours=48)),
        Order(total=Decimal("75.00"), status="exception", created_at=YEST),
        Payout(stripe_payout_id="po_fail", amount=Decimal("300.00"), status="failed"),
        Approval(action="trigger_refund", status="pending", risk_tier="critical"),
    ])
    s.commit()

    b = compute_briefing(s, NOW, live=True)
    assert len(b.stalled_deals) == 1 and b.stalled_deals[0]["amount"] == 200.0
    reasons = {d["reason"] for d in b.at_risk_deals}
    assert reasons == {"exception", "payout failed"}
    assert any("approval(s) pending" in i for i in b.crm_issues)
    assert any("payout(s) in failed state" in i for i in b.crm_issues)
    # Top actions are bounded to 5 and lead with the approval gate.
    assert len(b.top_actions) <= 5
    assert any("approval gate" in a.lower() for a in b.top_actions)


def test_rep_activity_maps_to_ledger() -> None:
    s = _session()
    s.add_all([
        Event(actor="pricing_agent", action="read_metrics", ts=YEST),
        Event(actor="pricing_agent", action="generate_copy", ts=YEST),
        Event(actor="content_agent", action="generate_copy", ts=YEST),
    ])
    s.commit()

    b = compute_briefing(s, NOW, live=True)
    activity = {a["actor"]: a["actions"] for a in b.rep_activity}
    assert activity == {"pricing_agent": 2, "content_agent": 1}


def test_render_is_brief_markdown_with_all_sections() -> None:
    md = render_markdown(compute_briefing(_session(), NOW, live=False))
    for heading in ("New deals", "Stalled deals", "At-risk deals", "Rep activity",
                    "CRM / data-quality", "Top 5 actions"):
        assert heading in md
    assert "NO LIVE SOURCE" in md   # safe-mode banner present, never fabricated

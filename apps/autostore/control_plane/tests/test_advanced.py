"""Phase-3 advanced features: risk scoring, read-only advisor, idempotency,
metrics — all of which strengthen the rails, never bypass them."""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from autostore.advisor import ReadOnlyAdvisor
from autostore.engine import Engine
from autostore.models import Decision, EventType, Order, PolicyConfig, Product
from autostore.risk import Band, RiskScorer, band_at_least


def _store():
    from autostore.store import InMemoryStore
    s = InMemoryStore(policy=PolicyConfig(max_discount_pct=0.40,
                                          refund_auto_max_cents=5000,
                                          ad_spend_daily_cap_cents=10000))
    s.seed_product(Product("RIDGE", "Ridge Hoodie", 8900, 3200, 4500, 50))
    s.seed_product(Product("LOW", "Low Stock Item", 5000, 2000, 3000, 4))
    s.seed_order(Order("ORD-1", "RIDGE", 1, 8900))
    return s


# ---- risk scoring ----------------------------------------------------------

def test_risk_band_ordering():
    assert band_at_least(Band.HIGH, Band.HIGH)
    assert band_at_least(Band.HIGH, Band.MEDIUM)
    assert not band_at_least(Band.LOW, Band.HIGH)


def test_price_at_cost_is_high_risk():
    rs = RiskScorer().score(EventType.PRICE_RECOMMENDATION,
                            {"sku": "RIDGE", "new_price_cents": 3200}, _store())
    assert rs.band == Band.HIGH
    assert any("margin" in f for f in rs.factors)


def test_small_price_change_is_low_risk():
    rs = RiskScorer().score(EventType.PRICE_RECOMMENDATION,
                            {"sku": "RIDGE", "new_price_cents": 8700}, _store())
    assert rs.band == Band.LOW


def test_full_refund_is_high_risk():
    rs = RiskScorer().score(EventType.REFUND_REQUEST,
                            {"order_id": "ORD-1", "amount_cents": 8900}, _store())
    assert rs.band == Band.HIGH


def test_unknown_sku_is_max_risk():
    rs = RiskScorer().score(EventType.PRICE_RECOMMENDATION,
                            {"sku": "NOPE", "new_price_cents": 100}, _store())
    assert rs.score == 1.0


# ---- risk as an extra guardrail (escalate, never bypass) -------------------

def test_high_risk_allow_is_escalated():
    # Policy ALLOWs an in-bounds inventory adjustment (50 - 45 = 5 >= 0), but a
    # 90%-of-stock swing is HIGH risk -> the engine ESCALATES instead of applying.
    e = Engine(_store(), risk_scorer=RiskScorer())
    r, _ = e.handle(EventType.INVENTORY_EVENT, {"sku": "RIDGE", "delta": -45, "reason": "shrink"})
    assert r.decision is Decision.ESCALATE
    assert any("risk HIGH" in x for x in r.reasons)
    assert e.store.get_product("RIDGE").inventory == 50      # not applied


def test_risk_never_relaxes_a_deny():
    e = Engine(_store(), risk_scorer=RiskScorer())
    r, _ = e.handle(EventType.PRICE_RECOMMENDATION, {"sku": "RIDGE", "new_price_cents": 1000})
    assert r.decision is Decision.DENY                        # below floor stays DENY


def test_low_risk_allow_still_applies():
    e = Engine(_store(), risk_scorer=RiskScorer())
    r, entry = e.handle(EventType.PRICE_RECOMMENDATION, {"sku": "RIDGE", "new_price_cents": 8700})
    assert r.decision is Decision.ALLOW and entry.executed
    assert e.last_risk.band == Band.LOW


# ---- read-only advisor -----------------------------------------------------

def test_advisor_proposes_restock_for_low_stock():
    rep = ReadOnlyAdvisor(_store(), low_stock=10).suggest_for_sku("LOW")
    kinds = {p.event_type for p in rep.proposals}
    assert EventType.INVENTORY_EVENT.value in kinds
    assert all(p.advisory_only for p in rep.proposals)


def test_advisor_never_proposes_below_floor():
    s = _store()
    # cost 2000, target margin 45% -> ~3636; floor 3000 -> allowed. Make floor high:
    s.seed_product(Product("HIFLOOR", "x", 9000, 2000, 8000, 100))
    rep = ReadOnlyAdvisor(s).suggest_for_sku("HIFLOOR")
    for p in rep.proposals:
        if p.event_type == EventType.PRICE_RECOMMENDATION.value:
            assert p.payload["new_price_cents"] >= 8000
    assert any("below floor" in n for n in rep.notes) or rep.proposals


def test_advisor_is_inert_does_not_mutate_store():
    s = _store()
    before = s.get_product("LOW").inventory
    ReadOnlyAdvisor(s).suggest_for_sku("LOW")
    assert s.get_product("LOW").inventory == before          # advisor never acts


# ---- idempotency + metrics -------------------------------------------------

def test_idempotent_submission_acts_once():
    e = Engine(_store())
    r1, e1 = e.handle(EventType.PRICE_RECOMMENDATION, {"sku": "RIDGE", "new_price_cents": 8700},
                      idempotency_key="key-1")
    r2, e2 = e.handle(EventType.PRICE_RECOMMENDATION, {"sku": "RIDGE", "new_price_cents": 8700},
                      idempotency_key="key-1")
    assert e1.id == e2.id                                     # same decision returned
    assert e.metrics()["events"] == 1                         # only ingested once


def test_metrics_shape():
    e = Engine(_store())
    e.handle(EventType.PRICE_RECOMMENDATION, {"sku": "RIDGE", "new_price_cents": 8700})
    e.handle(EventType.PRICE_RECOMMENDATION, {"sku": "RIDGE", "new_price_cents": 100})  # DENY
    m = e.metrics()
    assert m["events"] == 2
    assert m["by_decision"]["ALLOW"] == 1 and m["by_decision"]["DENY"] == 1
    assert m["audit_intact"] is True

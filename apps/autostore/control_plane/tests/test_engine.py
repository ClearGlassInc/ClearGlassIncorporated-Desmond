"""Trust-loop tests — every guardrail proven before deploy."""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from autostore.engine import Engine
from autostore.models import Decision, EventType, Order, PolicyConfig, Product
from autostore.store import InMemoryStore


def _seed() -> InMemoryStore:
    s = InMemoryStore(policy=PolicyConfig(
        max_discount_pct=0.25,           # 25 % max auto-discount
        refund_auto_max_cents=5000,      # $50
        ad_spend_daily_cap_cents=10000,  # $100/day
    ))
    s.seed_product(Product("RIDGE", "Ridge Hoodie", 8900, 3200, 4500, 50))
    s.seed_order(Order("ORD-1", "RIDGE", qty=1, price_cents=8900))
    return s


def test_price_within_lock_is_allowed_and_executed():
    e = Engine(_seed())
    r, entry = e.handle(EventType.PRICE_RECOMMENDATION,
                        {"sku": "RIDGE", "new_price_cents": 7900})
    assert r.decision is Decision.ALLOW and entry.executed
    assert e.store.get_product("RIDGE").price_cents == 7900


def test_price_below_floor_is_denied():
    e = Engine(_seed())
    r, _ = e.handle(EventType.PRICE_RECOMMENDATION,
                    {"sku": "RIDGE", "new_price_cents": 4000})
    assert r.decision is Decision.DENY
    assert e.store.get_product("RIDGE").price_cents == 8900   # unchanged


def test_deep_discount_escalates_then_approves():
    e = Engine(_seed())
    r, _ = e.handle(EventType.PRICE_RECOMMENDATION,
                    {"sku": "RIDGE", "new_price_cents": 5000})       # ~44 % off
    assert r.decision is Decision.ESCALATE and e.pending
    pid = e.pending[0].id
    entry = e.approve(pid, "ops-lead")
    assert entry.executed and entry.decision is Decision.ALLOW
    assert e.store.get_product("RIDGE").price_cents == 5000


def test_refund_within_cap_allowed():
    e = Engine(_seed())
    r, entry = e.handle(EventType.REFUND_REQUEST,
                        {"order_id": "ORD-1", "amount_cents": 2000})
    assert r.decision is Decision.ALLOW and entry.executed


def test_refund_over_cap_escalates():
    e = Engine(_seed())
    r, _ = e.handle(EventType.REFUND_REQUEST,
                    {"order_id": "ORD-1", "amount_cents": 7000})
    assert r.decision is Decision.ESCALATE


def test_refund_over_order_total_denied():
    e = Engine(_seed())
    r, _ = e.handle(EventType.REFUND_REQUEST,
                    {"order_id": "ORD-1", "amount_cents": 9000})
    assert r.decision is Decision.DENY


def test_refund_unknown_order_denied():
    e = Engine(_seed())
    r, _ = e.handle(EventType.REFUND_REQUEST,
                    {"order_id": "MISSING", "amount_cents": 1000})
    assert r.decision is Decision.DENY


def test_ad_spend_cap_enforced_across_requests():
    e = Engine(_seed())
    r1, _ = e.handle(EventType.AD_SPEND_REQUEST, {"amount_cents": 8000})
    r2, _ = e.handle(EventType.AD_SPEND_REQUEST, {"amount_cents": 3000})
    assert r1.decision is Decision.ALLOW
    assert r2.decision is Decision.DENY                       # would exceed cap
    assert e.store.ad_spend_today_cents() == 8000


def test_inventory_cannot_go_negative():
    e = Engine(_seed())
    r, _ = e.handle(EventType.INVENTORY_EVENT,
                    {"sku": "RIDGE", "delta": -1000, "reason": "shrink"})
    assert r.decision is Decision.DENY
    assert e.store.get_product("RIDGE").inventory == 50       # unchanged


def test_unknown_sku_denied():
    e = Engine(_seed())
    r, _ = e.handle(EventType.PRICE_RECOMMENDATION,
                    {"sku": "NOPE", "new_price_cents": 1000})
    assert r.decision is Decision.DENY


def test_invalid_payload_denied_not_raised():
    e = Engine(_seed())
    r, _ = e.handle(EventType.PRICE_RECOMMENDATION, {"sku": "RIDGE"})
    assert r.decision is Decision.DENY


def test_unknown_event_type_denied():
    from autostore.policy import evaluate
    r = evaluate("not_a_type", {}, _seed())  # type: ignore[arg-type]
    assert r.decision is Decision.DENY


def test_audit_chain_is_tamper_evident():
    e = Engine(_seed())
    e.handle(EventType.PRICE_RECOMMENDATION, {"sku": "RIDGE", "new_price_cents": 7900})
    e.handle(EventType.REFUND_REQUEST, {"order_id": "ORD-1", "amount_cents": 2000})
    assert e.ledger.verify() is True
    # tamper -> chain must break
    e.ledger._entries[0].reasons.append("tampered")  # type: ignore[attr-defined]
    assert e.ledger.verify() is False


def test_deny_path_on_approval_queue():
    e = Engine(_seed())
    e.handle(EventType.PRICE_RECOMMENDATION,
             {"sku": "RIDGE", "new_price_cents": 5000})
    pid = e.pending[0].id
    entry = e.deny(pid, "ops-lead")
    assert entry.decision is Decision.DENY
    assert e.store.get_product("RIDGE").price_cents == 8900   # never executed

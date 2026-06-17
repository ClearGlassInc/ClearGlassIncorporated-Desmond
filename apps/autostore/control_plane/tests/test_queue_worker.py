"""Queue-mode + worker tests: authorization and execution are decoupled."""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from autostore.engine import Engine
from autostore.models import Decision, EventType, Order, PolicyConfig, Product
from autostore.queue import InMemoryQueue, make_packet
from autostore.store import InMemoryStore
from autostore.worker import Worker


def _store() -> InMemoryStore:
    s = InMemoryStore(policy=PolicyConfig(max_discount_pct=0.25,
                                          refund_auto_max_cents=5000,
                                          ad_spend_daily_cap_cents=10000))
    s.seed_product(Product("RIDGE", "Ridge Hoodie", 8900, 3200, 4500, 50))
    s.seed_order(Order("ORD-1", "RIDGE", 1, 8900))
    return s


def test_allow_in_queue_mode_does_not_apply_inline():
    store = _store()
    q = InMemoryQueue()
    e = Engine(store, queue=q)
    r, entry = e.handle(EventType.PRICE_RECOMMENDATION,
                        {"sku": "RIDGE", "new_price_cents": 7900})
    assert r.decision is Decision.ALLOW
    assert entry.executed is False                  # dispatched, not applied
    assert "dispatched to worker queue" in r.reasons
    assert len(q) == 1
    assert store.get_product("RIDGE").price_cents == 8900   # unchanged until worker runs


def test_worker_applies_packet_and_audits():
    store = _store()
    q = InMemoryQueue()
    e = Engine(store, queue=q)
    e.handle(EventType.PRICE_RECOMMENDATION, {"sku": "RIDGE", "new_price_cents": 7900})

    w = Worker(store, q)
    processed = w.run_once()
    assert processed is not None
    assert store.get_product("RIDGE").price_cents == 7900   # applied by worker
    assert w.ledger.entries[-1].action.endswith("_applied")
    assert w.ledger.verify() is True
    assert w.run_once() is None                     # queue drained


def test_deny_never_enqueues():
    store = _store()
    q = InMemoryQueue()
    e = Engine(store, queue=q)
    e.handle(EventType.PRICE_RECOMMENDATION, {"sku": "RIDGE", "new_price_cents": 4000})
    assert len(q) == 0                              # below floor -> never queued


def test_worker_drain_counts():
    store = _store()
    q = InMemoryQueue()
    e = Engine(store, queue=q)
    e.handle(EventType.INVENTORY_EVENT, {"sku": "RIDGE", "delta": 10, "reason": "restock"})
    e.handle(EventType.AD_SPEND_REQUEST, {"amount_cents": 2000})
    w = Worker(store, q)
    assert w.drain() == 2
    assert store.get_product("RIDGE").inventory == 60
    assert store.ad_spend_today_cents() == 2000


def test_make_packet_shape():
    p = make_packet(event_id=3, action="price_change", audit_ref="AS-X",
                    payload={"sku": "RIDGE"})
    assert p == {"event_id": 3, "action": "price_change", "audit_ref": "AS-X",
                 "payload": {"sku": "RIDGE"}}


def test_inline_mode_unchanged():
    """Without a queue, behaviour is the original inline apply."""
    store = _store()
    e = Engine(store)                               # no queue
    r, entry = e.handle(EventType.PRICE_RECOMMENDATION,
                        {"sku": "RIDGE", "new_price_cents": 7900})
    assert r.decision is Decision.ALLOW and entry.executed is True
    assert store.get_product("RIDGE").price_cents == 7900

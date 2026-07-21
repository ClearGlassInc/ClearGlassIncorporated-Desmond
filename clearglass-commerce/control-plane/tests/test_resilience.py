"""Resilience & abuse-control tests — rate limiting, webhook idempotency, the
readiness probe, and security response headers. Offline: SQLite in-memory, no network.

Complements tests/test_security.py, which unit-tests the admin-auth guard itself.
"""
from __future__ import annotations

import json
import os

# Pin to an in-memory SQLite engine before importing app.db (which builds the engine at import).
os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import db as db_module
from app import payments
from app import security as security_module
from app.config import get_settings
from app.main import create_app
from app.models import Approval, Base, Order
from app.security import SlidingWindowLimiter


@pytest.fixture()
def harness(monkeypatch):
    """Fresh app + DB + rate limiter per test; clears the settings cache on both sides."""
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test_123")
    monkeypatch.setattr(security_module, "_limiter", SlidingWindowLimiter())

    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_session():
        session = TestingSession()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def build():
        get_settings.cache_clear()
        app = create_app()
        app.dependency_overrides[db_module.get_session] = override_session
        return TestClient(app)

    yield build, TestingSession, monkeypatch
    get_settings.cache_clear()


def test_limiter_allows_within_window_and_blocks_over() -> None:
    limiter = SlidingWindowLimiter()
    assert all(limiter.allow("k", 3) for _ in range(3))
    assert limiter.allow("k", 3) is False
    assert limiter.allow("other", 3) is True   # independent keys


def test_checkout_rate_limit_returns_429(harness) -> None:
    build, _, monkeypatch = harness
    monkeypatch.setenv("RATE_LIMIT_CHECKOUT_PER_MINUTE", "2")
    client = build()
    body = {"items": [{"name": "Glass", "amount": 1000, "quantity": 1}]}
    codes = [client.post("/checkout/session", json=body).status_code for _ in range(3)]
    assert codes[:2] == [200, 200]
    assert codes[-1] == 429


def test_decision_rate_limit_returns_429(harness) -> None:
    build, TestingSession, monkeypatch = harness
    monkeypatch.setenv("RATE_LIMIT_DECISIONS_PER_MINUTE", "3")
    client = build()
    with TestingSession() as s:
        approval = Approval(action="update_pricing", risk_score=80, risk_tier="high")
        s.add(approval)
        s.commit()
        approval_id = approval.id
    decision = {"decided_by": "desmond", "note": "throttle test"}
    codes = [
        client.post(f"/approvals/{approval_id}/reject", json=decision).status_code
        for _ in range(4)
    ]
    assert codes[-1] == 429


def test_rate_limit_zero_disables_throttle(harness) -> None:
    build, _, monkeypatch = harness
    monkeypatch.setenv("RATE_LIMIT_CHECKOUT_PER_MINUTE", "0")
    client = build()
    body = {"items": [{"name": "Glass", "amount": 1000, "quantity": 1}]}
    codes = [client.post("/checkout/session", json=body).status_code for _ in range(5)]
    assert 429 not in codes


def _paid_checkout_event(session_id: str) -> bytes:
    event = {
        "type": "checkout.session.completed",
        "data": {"object": {"id": session_id, "amount_total": 12500, "currency": "cad"}},
    }
    return json.dumps(event).encode()


def test_webhook_redelivery_creates_single_order(harness) -> None:
    build, TestingSession, _ = harness
    client = build()
    body = _paid_checkout_event("cs_test_abc")
    header = payments.sign_payload(body, "whsec_test_123")
    for _ in range(3):
        resp = client.post("/webhooks/stripe", content=body, headers={"stripe-signature": header})
        assert resp.status_code == 200
    with TestingSession() as s:
        orders = list(s.scalars(select(Order)).all())
    assert len(orders) == 1
    assert orders[0].external_ref == "cs_test_abc"
    assert str(orders[0].total) == "125.00"


def test_webhook_distinct_sessions_create_distinct_orders(harness) -> None:
    build, TestingSession, _ = harness
    client = build()
    for sid in ("cs_one", "cs_two"):
        body = _paid_checkout_event(sid)
        header = payments.sign_payload(body, "whsec_test_123")
        assert client.post(
            "/webhooks/stripe", content=body, headers={"stripe-signature": header}
        ).status_code == 200
    with TestingSession() as s:
        assert len(list(s.scalars(select(Order)).all())) == 2


def test_ready_probe_reports_database_ok(harness) -> None:
    build, _, _ = harness
    client = build()
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json()["database"] == "ok"


def test_security_headers_present(harness) -> None:
    build, _, _ = harness
    client = build()
    resp = client.get("/health")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

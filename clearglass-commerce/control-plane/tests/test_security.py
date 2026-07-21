"""Security hardening tests — admin auth on the approval gate, rate limiting,
webhook idempotency, and the readiness probe. Offline: SQLite in-memory, no network.
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
    """Fresh app + DB + rate-limiter per test; clears the settings cache on both sides."""
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


def _pending_approval(TestingSession) -> int:
    with TestingSession() as s:
        approval = Approval(action="update_pricing", risk_score=80, risk_tier="high")
        s.add(approval)
        s.commit()
        return approval.id


DECISION = {"decided_by": "desmond", "note": "ok"}


def test_decisions_open_in_dev_when_no_token(harness) -> None:
    build, TestingSession, _ = harness
    client = build()
    approval_id = _pending_approval(TestingSession)
    resp = client.post(f"/approvals/{approval_id}/approve", json=DECISION)
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"


def test_decisions_require_token_when_configured(harness) -> None:
    build, TestingSession, monkeypatch = harness
    monkeypatch.setenv("ADMIN_API_TOKEN", "sekrit-token")
    client = build()
    approval_id = _pending_approval(TestingSession)

    assert client.post(f"/approvals/{approval_id}/approve", json=DECISION).status_code == 401
    assert (
        client.post(
            f"/approvals/{approval_id}/approve",
            json=DECISION,
            headers={"Authorization": "Bearer wrong"},
        ).status_code
        == 401
    )
    # Nothing was decided by the rejected calls.
    with TestingSession() as s:
        assert s.get(Approval, approval_id).status == "pending"

    ok = client.post(
        f"/approvals/{approval_id}/approve",
        json=DECISION,
        headers={"Authorization": "Bearer sekrit-token"},
    )
    assert ok.status_code == 200
    assert ok.json()["status"] == "approved"


def test_decisions_fail_closed_in_production_without_token(harness) -> None:
    build, TestingSession, monkeypatch = harness
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("ADMIN_API_TOKEN", raising=False)
    client = build()
    approval_id = _pending_approval(TestingSession)
    resp = client.post(f"/approvals/{approval_id}/approve", json=DECISION)
    assert resp.status_code == 503
    with TestingSession() as s:
        assert s.get(Approval, approval_id).status == "pending"


def test_decision_rate_limit_returns_429(harness) -> None:
    build, TestingSession, monkeypatch = harness
    monkeypatch.setenv("RATE_LIMIT_DECISIONS_PER_MINUTE", "3")
    client = build()
    approval_id = _pending_approval(TestingSession)
    codes = [
        client.post(f"/approvals/{approval_id}/reject", json=DECISION).status_code
        for _ in range(4)
    ]
    assert codes[-1] == 429


def test_checkout_rate_limit_returns_429(harness) -> None:
    build, _, monkeypatch = harness
    monkeypatch.setenv("RATE_LIMIT_CHECKOUT_PER_MINUTE", "2")
    client = build()
    body = {"items": [{"name": "Glass", "amount": 1000, "quantity": 1}]}
    codes = [client.post("/checkout/session", json=body).status_code for _ in range(3)]
    assert codes[-1] == 429
    assert 429 not in codes[:-1]


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

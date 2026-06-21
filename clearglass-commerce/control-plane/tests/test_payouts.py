"""Tests for payout tracking — offline, no Stripe key, no network.

Covers the pure normalization helper and the full webhook -> DB -> GET /payouts path with
signature verification enforced.
"""
from __future__ import annotations

import json
import os

# Pin to an in-memory SQLite engine before importing app.db (which builds the engine at import).
os.environ.setdefault("DATABASE_URL", "sqlite://")

from decimal import Decimal

import pytest

from app import payments

try:
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app import db as db_module
    from app.main import create_app
    from app.models import Base

    _HAS_WEB_STACK = True
except ImportError:  # pragma: no cover - lets the helper tests run in a minimal env
    _HAS_WEB_STACK = False


def test_parse_payout_converts_cents_and_arrival() -> None:
    obj = {
        "id": "po_test_123",
        "amount": 125000,            # $1,250.00 in cents
        "currency": "cad",
        "status": "paid",
        "destination": "ba_opaque_token",
        "arrival_date": 1_700_000_000,
    }
    parsed = payments.parse_payout(obj)
    assert parsed["stripe_payout_id"] == "po_test_123"
    assert parsed["amount"] == Decimal("1250.00")
    assert parsed["currency"] == "CAD"
    assert parsed["status"] == "paid"
    assert parsed["destination"] == "ba_opaque_token"
    assert parsed["arrival_date"].year == 2023


def test_parse_payout_keeps_only_destination_token_not_bank_details() -> None:
    """Even if Stripe expands `destination`, we persist only its id token — never digits."""
    obj = {
        "id": "po_x",
        "amount": 100,
        "currency": "usd",
        "destination": {"id": "ba_token", "last4": "9464", "routing_number": "000111222"},
    }
    parsed = payments.parse_payout(obj)
    assert parsed["destination"] == "ba_token"
    serialized = json.dumps(parsed, default=str)
    assert "9464" not in serialized
    assert "000111222" not in serialized


@pytest.fixture()
def client(monkeypatch):
    if not _HAS_WEB_STACK:
        pytest.skip("fastapi/sqlalchemy not installed")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test_123")

    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,   # one shared in-memory connection across sessions
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

    app = create_app()
    app.dependency_overrides[db_module.get_session] = override_session
    return TestClient(app)


def _post_payout(client, etype: str, *, payout_id: str, amount: int, status: str, account=None):
    event = {"type": etype, "account": account, "data": {"object": {
        "id": payout_id, "amount": amount, "currency": "cad",
        "status": status, "destination": "ba_token", "arrival_date": 1_700_000_000,
    }}}
    body = json.dumps(event).encode()
    header = payments.sign_payload(body, "whsec_test_123")
    return client.post("/webhooks/stripe", content=body, headers={"stripe-signature": header})


def test_payout_webhook_records_and_lists(client) -> None:
    resp = _post_payout(client, "payout.created", payout_id="po_1", amount=50000, status="in_transit")
    assert resp.status_code == 200
    assert resp.json()["verified"] is True

    listing = client.get("/payouts").json()
    assert len(listing) == 1
    assert listing[0]["stripe_payout_id"] == "po_1"
    assert listing[0]["amount"] == 500.0
    assert listing[0]["status"] == "in_transit"


def test_payout_paid_updates_existing_row_no_duplicate(client) -> None:
    _post_payout(client, "payout.created", payout_id="po_2", amount=50000, status="in_transit")
    _post_payout(client, "payout.paid", payout_id="po_2", amount=50000, status="paid")

    listing = client.get("/payouts").json()
    assert len(listing) == 1                    # idempotent: same payout id -> one row
    assert listing[0]["status"] == "paid"


def test_payouts_filter_by_tenant(client) -> None:
    _post_payout(client, "payout.paid", payout_id="po_a", amount=100, status="paid", account="acct_A")
    _post_payout(client, "payout.paid", payout_id="po_b", amount=200, status="paid", account="acct_B")

    only_a = client.get("/payouts", params={"tenant_id": "acct_A"}).json()
    assert [p["stripe_payout_id"] for p in only_a] == ["po_a"]


def test_payout_webhook_rejects_bad_signature(client) -> None:
    body = json.dumps({"type": "payout.paid", "data": {"object": {"id": "po_z"}}}).encode()
    resp = client.post("/webhooks/stripe", content=body, headers={"stripe-signature": "t=1,v1=bad"})
    assert resp.status_code == 400
    assert client.get("/payouts").json() == []   # nothing written on rejection

"""The browser must never be able to choose what it pays.

`/checkout/session` hands its line items to Stripe, so whatever sets ``amount``
decides the charge. Before the price book that was the request body: a buyer could
post ``amount: 1`` and take a CAD $2,500 engagement for a cent. These tests pin the
amount to the server-side price book and fail if a price-shaped field ever finds its
way back into the checkout contract.
"""
from __future__ import annotations

import json
import os

# Pin to an in-memory SQLite engine before importing app.db (which builds the engine at import).
os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest

from app import pricebook

try:
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app import db as db_module
    from app.main import create_app
    from app.models import Base

    _HAS_WEB_STACK = True
except (ImportError, RuntimeError):  # pragma: no cover - minimal env runs the pure tests only
    _HAS_WEB_STACK = False


QUICK_AUDIT_CENTS = 24900


# --------------------------------------------------------------------------- pure


def test_resolve_prices_from_the_book() -> None:
    items, mode = pricebook.resolve_line_items([{"sku": "quick-audit", "quantity": 1}])
    assert mode == "payment"
    assert items[0]["amount"] == QUICK_AUDIT_CENTS
    assert items[0]["currency"] == "cad"


def test_client_supplied_amount_is_ignored_entirely() -> None:
    """The core guarantee: extra price-shaped keys change nothing about the charge."""
    items, _ = pricebook.resolve_line_items(
        [{"sku": "quick-audit", "quantity": 1, "amount": 1, "currency": "usd", "name": "Free"}]
    )
    assert items[0]["amount"] == QUICK_AUDIT_CENTS
    assert items[0]["currency"] == "cad"
    assert items[0]["name"] == "Security Quick-Audit"


def test_unknown_sku_is_refused() -> None:
    with pytest.raises(pricebook.PricebookError, match="unknown sku"):
        pricebook.resolve_line_items([{"sku": "not-a-real-service", "quantity": 1}])


def test_quantity_above_the_offer_maximum_is_refused() -> None:
    with pytest.raises(pricebook.PricebookError, match="exceeds the maximum"):
        pricebook.resolve_line_items([{"sku": "quick-audit", "quantity": 99}])


def test_empty_cart_is_refused() -> None:
    with pytest.raises(pricebook.PricebookError):
        pricebook.resolve_line_items([])


def test_recurring_offer_selects_subscription_mode() -> None:
    items, mode = pricebook.resolve_line_items([{"sku": "monitoring", "quantity": 1}])
    assert mode == "subscription"
    assert items[0]["interval"] == "month"


def test_mixing_recurring_and_one_time_is_refused() -> None:
    """Stripe bills a session once or on a schedule — never both."""
    with pytest.raises(pricebook.PricebookError, match="mix recurring and one-time"):
        pricebook.resolve_line_items(
            [{"sku": "monitoring", "quantity": 1}, {"sku": "quick-audit", "quantity": 1}]
        )


def test_every_offer_is_priced_and_well_formed() -> None:
    offers = pricebook.all_offers()
    assert offers, "price book is empty"
    for offer in offers:
        assert offer.amount > 0, f"{offer.sku} has no price"
        assert offer.currency == offer.currency.lower(), "Stripe expects lowercase currency"
        assert offer.tax_behavior in {"inclusive", "exclusive"}, offer.sku
        if offer.recurring:
            assert offer.interval, f"{offer.sku} recurs but has no interval"


# ------------------------------------------------------------------------ the API


@pytest.fixture()
def client():
    if not _HAS_WEB_STACK:
        pytest.skip("fastapi/sqlalchemy not installed")

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

    app = create_app()
    app.dependency_overrides[db_module.get_session] = override_session
    return TestClient(app)


def test_checkout_charges_the_book_price_not_the_posted_one(client) -> None:
    """The regression this whole module exists for."""
    response = client.post(
        "/checkout/session",
        json={"items": [{"sku": "quick-audit", "quantity": 1, "amount": 1}]},
    )
    assert response.status_code == 200
    assert response.json()["amount_total"] == QUICK_AUDIT_CENTS


def test_checkout_rejects_an_unknown_sku(client) -> None:
    response = client.post(
        "/checkout/session", json={"items": [{"sku": "free-stuff", "quantity": 1}]}
    )
    assert response.status_code == 400
    assert "unknown sku" in response.json()["detail"]


def test_checkout_rejects_an_item_with_no_sku(client) -> None:
    """A payload in the old price-carrying shape must fail, not fall back to a default."""
    response = client.post(
        "/checkout/session", json={"items": [{"name": "Glass", "amount": 1000, "quantity": 1}]}
    )
    assert response.status_code == 422


def test_offers_endpoint_advertises_the_same_prices(client) -> None:
    response = client.get("/offers")
    assert response.status_code == 200
    offers = {o["sku"]: o for o in response.json()}
    assert offers["quick-audit"]["amount"] == QUICK_AUDIT_CENTS
    assert offers["monitoring"]["interval"] == "month"


def test_checkout_contract_exposes_no_price_field(client) -> None:
    """Coverage drift guard: if a price-shaped field returns to the request schema,
    the browser can set it again. Fail here rather than in production."""
    schema = client.get("/openapi.json").json()
    item = schema["components"]["schemas"]["CheckoutLineItem"]["properties"]
    assert set(item) == {"sku", "quantity"}, f"CheckoutLineItem gained fields: {sorted(item)}"


def test_subscription_sku_produces_a_subscription_session(client) -> None:
    response = client.post(
        "/checkout/session", json={"items": [{"sku": "monitoring", "quantity": 1}]}
    )
    assert response.status_code == 200
    assert response.json()["checkout_mode"] == "subscription"


def test_price_tampering_is_recorded_in_the_audit_trail(client) -> None:
    """A refused checkout must survive its own 400.

    `get_session` rolls back when the handler raises, so the rejection has to be
    committed before the HTTPException or the evidence of someone probing the
    checkout disappears with the failed request. (The ledger's read model omits
    payloads on purpose, so this asserts on the record, not its contents.)
    """
    client.post("/checkout/session", json={"items": [{"sku": "free-stuff", "quantity": 1}]})
    events = client.get("/events").json()
    rejected = [
        e
        for e in events
        if e.get("result") == "rejected" and e.get("action") == "create_checkout_session"
    ]
    assert rejected, f"a refused checkout must leave an audit record; got {json.dumps(events)}"

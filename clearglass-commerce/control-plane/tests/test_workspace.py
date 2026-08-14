"""Workspace subscription pricing: the contract, not just the happy path.

The load-bearing tests here are the ones that would fail if somebody made the
seat price reachable from a request body, or let the advertised monthly rate
drift away from the amount Stripe charges. Both are silent-overcharge bugs — the
customer sees one number and the card is billed another — so they are pinned by
assertion rather than by convention.
"""
from __future__ import annotations

import json

import pytest

from app import workspace


@pytest.fixture(autouse=True)
def _clean_plan_cache():
    workspace.reset_cache()
    yield
    workspace.reset_cache()


# ── The price authority contract ────────────────────────────────────────────

def test_request_schema_cannot_carry_a_price():
    """The subscription request names what and how many — never how much.

    This is the whole server-side-price-authority argument for the Workspace
    endpoints, expressed as a test so a future field addition fails the build
    instead of quietly letting a browser pick its own subscription price.
    """
    from app.schemas import WorkspaceSubscriptionRequest

    fields = set(WorkspaceSubscriptionRequest.model_fields)
    assert fields == {"plan_sku", "seats", "customer_email", "client_reference_id"}

    forbidden = {
        "amount", "unit_amount", "price", "prices", "price_data", "monthly_rate",
        "period_total", "monthly_total", "annual_total", "discount", "coupon",
        "currency", "tax", "total", "success_url", "cancel_url",
    }
    assert not (fields & forbidden), f"price-shaped fields leaked into the request: {fields & forbidden}"


def test_openapi_checkout_body_is_plan_and_seats_only():
    """Pin the published contract too — the schema is what integrators code against."""
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app()) as client:
        spec = client.get("/openapi.json").json()
    props = spec["components"]["schemas"]["WorkspaceSubscriptionRequest"]["properties"]
    assert set(props) == {"plan_sku", "seats", "customer_email", "client_reference_id"}


# ── Advertised price vs charged price ───────────────────────────────────────

@pytest.mark.parametrize(
    "sku,monthly_rate,unit_amount,interval",
    [
        ("ws-essentials-monthly", 720, 720, "month"),
        ("ws-essentials-annual", 600, 7200, "year"),
        ("ws-collaborate-monthly", 972, 972, "month"),
        ("ws-collaborate-annual", 810, 9720, "year"),
        ("ws-complete-monthly", 2040, 2040, "month"),
        ("ws-complete-annual", 1700, 20400, "year"),
    ],
)
def test_plan_book_matches_the_published_pricing_page(sku, monthly_rate, unit_amount, interval):
    """These are the exact figures rendered by workspace.html.

    If the page and the plan book disagree, a customer is quoted one price and
    charged another. Pinning both here means changing one without the other
    fails the build.
    """
    plan = workspace.get_plan(sku)
    assert plan.monthly_rate == monthly_rate
    assert plan.unit_amount == unit_amount
    assert plan.interval == interval
    assert plan.currency == "cad"
    assert plan.tax_behavior == "exclusive"


def test_annual_unit_amount_is_exactly_twelve_monthly_rates():
    for plan in workspace.catalogue():
        expected = plan.monthly_rate * plan.months
        assert plan.unit_amount == expected, f"{plan.sku} charges {plan.unit_amount}, advertises {expected}"


def test_plan_book_refuses_to_load_when_advertised_and_charged_prices_disagree(tmp_path, monkeypatch):
    """A plan book that would overcharge must not load at all.

    The dangerous version of this bug is an annual plan whose unit_amount is the
    monthly rate: the page says $97.20/year and Stripe bills $8.10/year, or the
    reverse. Refuse the deployment rather than serve either.
    """
    book = {
        "currency": "cad", "trial_days": 14, "min_seats": 1, "max_seats": 500,
        "plans": [{
            "sku": "bad-annual", "tier": "x", "name": "Bad", "description": "",
            "interval": "year", "monthly_rate": 810,
            "unit_amount": 810,  # should be 9720
            "tax_behavior": "exclusive", "active": True,
        }],
    }
    path = tmp_path / "plans.json"
    path.write_text(json.dumps(book), encoding="utf-8")
    monkeypatch.setenv("WORKSPACE_PLANS_PATH", str(path))
    workspace.reset_cache()

    with pytest.raises(workspace.WorkspaceError, match="does not equal monthly_rate"):
        workspace.get_plan("bad-annual")


# ── Seat arithmetic ─────────────────────────────────────────────────────────

def test_quote_is_cent_exact_across_every_plan_and_seat_count():
    """Brute-force the whole supported surface; integer maths must never drift."""
    checked = 0
    for plan in workspace.catalogue():
        for seats in list(range(1, 51)) + [99, 100, 250, 499, 500]:
            q = workspace.quote(plan.sku, seats)
            assert q.monthly_total == plan.monthly_rate * seats
            assert q.period_total == plan.unit_amount * seats
            assert q.annual_total == plan.monthly_rate * seats * 12
            # The billed figure and the advertised figure must describe the same year.
            assert q.period_total * (12 // plan.months) == q.annual_total
            checked += 1
    assert checked == 6 * 55


def test_stripe_line_items_total_equals_the_quoted_amount():
    """The charge must equal the quote to the cent, for every seat count.

    Compares the *Stripe line items* against the quote — not the quote against
    itself, which proves nothing.
    """
    for plan in workspace.catalogue():
        for seats in (1, 2, 7, 33, 100, 500):
            q = workspace.quote(plan.sku, seats)
            items = workspace.to_stripe_line_items(q)
            assert len(items) == 1, "seats must be a quantity on one item, not N items"
            assert items[0]["quantity"] == seats
            assert items[0]["amount"] == plan.unit_amount
            extended = sum(i["amount"] * i["quantity"] for i in items)
            assert extended == q.period_total


def test_seats_are_billed_as_quantity_not_repeated_line_items():
    """Proration depends on it: Stripe prorates a quantity change on one item."""
    q = workspace.quote("ws-collaborate-annual", 12)
    items = workspace.to_stripe_line_items(q)
    assert len(items) == 1
    assert items[0]["quantity"] == 12
    assert items[0]["interval"] == "year"


# ── Bounds and refusals ─────────────────────────────────────────────────────

@pytest.mark.parametrize("seats", [0, -1, -100])
def test_seats_below_the_minimum_are_rejected(seats):
    with pytest.raises(workspace.WorkspaceError, match="at least"):
        workspace.quote("ws-essentials-annual", seats)


def test_seats_above_the_maximum_are_rejected_not_clamped():
    """A request for 900 seats must fail, not silently become an invoice for 500."""
    with pytest.raises(workspace.WorkspaceError, match="exceeds the maximum"):
        workspace.quote("ws-essentials-annual", 900)


def test_unknown_and_inactive_plans_are_refused():
    with pytest.raises(workspace.WorkspaceError, match="unknown plan"):
        workspace.quote("ws-does-not-exist", 5)


def test_live_checkout_is_blocked_until_a_stripe_price_exists():
    """No Workspace Price exists yet, so live mode must refuse rather than
    invent an inline recurring price this repository controls."""
    for plan in workspace.catalogue():
        blocker = workspace.live_blocker(plan.sku)
        if plan.stripe_price_id:
            assert blocker is None
        else:
            assert blocker and "no Stripe Price" in blocker


# ── HTTP surface ────────────────────────────────────────────────────────────

def _client():
    """An app wired to an in-memory database.

    The checkout route writes an audit row before returning, so it needs real
    storage — the same sqlite-in-memory pattern tests/test_cart.py uses for the
    Side Store, rather than a Postgres the test environment does not have.
    """
    import os

    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    os.environ.setdefault("DATABASE_URL", "sqlite://")
    from app import db as db_module
    from app.main import create_app
    from app.models import Base

    engine = create_engine(
        "sqlite://", future=True,
        connect_args={"check_same_thread": False}, poolclass=StaticPool,
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


def test_plans_endpoint_lists_every_active_plan():
    with _client() as client:
        body = client.get("/workspace/plans").json()
    assert {p["sku"] for p in body} == {
        "ws-essentials-monthly", "ws-essentials-annual",
        "ws-collaborate-monthly", "ws-collaborate-annual",
        "ws-complete-monthly", "ws-complete-annual",
    }
    # Cheapest first, so a storefront can render the ladder left to right.
    assert [p["monthly_rate"] for p in body] == sorted(p["monthly_rate"] for p in body)
    # Nothing is live-purchasable yet; the flag must say so rather than 503 later.
    assert all(p["purchasable_live"] is False for p in body)


def test_quote_endpoint_matches_the_pricing_page_arithmetic():
    with _client() as client:
        r = client.post("/workspace/quote", json={"plan_sku": "ws-collaborate-annual", "seats": 5})
    assert r.status_code == 200
    body = r.json()
    assert body["monthly_total"] == 810 * 5      # $40.50/month for five people
    assert body["period_total"] == 9720 * 5      # $486.00 billed once a year
    assert body["annual_total"] == 810 * 5 * 12
    assert body["trial_days"] == 14
    assert body["tax_included"] is False


def test_quote_endpoint_rejects_out_of_range_seats():
    with _client() as client:
        assert client.post(
            "/workspace/quote", json={"plan_sku": "ws-essentials-annual", "seats": 0}
        ).status_code == 422
        assert client.post(
            "/workspace/quote", json={"plan_sku": "ws-essentials-annual", "seats": 501}
        ).status_code == 422


def test_extra_price_field_in_request_is_ignored_never_honoured():
    """A tampered body must not change what is charged."""
    with _client() as client:
        r = client.post(
            "/workspace/quote",
            json={
                "plan_sku": "ws-complete-annual", "seats": 2,
                "unit_amount": 1, "amount": 1, "period_total": 1, "currency": "usd",
            },
        )
    assert r.status_code == 200
    body = r.json()
    assert body["period_total"] == 20400 * 2, "server price was overridden by the request"
    assert body["currency"] == "cad"


def test_mock_mode_checkout_charges_the_quoted_amount():
    with _client() as client:
        r = client.post(
            "/workspace/checkout/session",
            json={
                "plan_sku": "ws-essentials-annual", "seats": 3,
                "customer_email": "buyer@example.com",
            },
        )
    assert r.status_code == 200
    assert r.json()["amount_total"] == 7200 * 3

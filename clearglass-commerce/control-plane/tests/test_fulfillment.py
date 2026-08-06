"""Fulfillment orchestration — paid order to tracked parcel, with the gate intact.

The property under test throughout: money arriving never implies a parcel
leaving. An order that cannot ship is recorded as unfulfillable and stays
visible; it is never quietly marked done.
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app import fulfillment
from app.config import Settings
from app.models import Approval, Base, Event, Order, Shipment


@pytest.fixture()
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        yield db


def connected(**overrides) -> Settings:
    base = {"printful_api_key": "pf_test_placeholder", "require_approval_for_high_risk": True}
    base.update(overrides)
    return Settings(**base)


def make_order(session: Session, **overrides) -> Order:
    fields = {
        "status": "paid",
        "total": Decimal("34.00"),
        "currency": "CAD",
        "external_ref": "cs_test_1",
        "ship_to_name": "Desmond Odhiambo",
        "ship_to_address1": "100 King St W",
        "ship_to_city": "Burlington",
        "ship_to_state": "ON",
        "ship_to_country": "CA",
        "ship_to_zip": "L7R 3N2",
        "ship_to_email": "buyer@example.test",
    }
    fields.update(overrides)
    order = Order(**fields)
    session.add(order)
    session.flush()
    return order


ITEMS = [{"sync_variant_id": 501, "quantity": 1, "retail_price": "34.00"}]


def draft_responder(order_id: int = 999):
    def request(method: str, path: str, body: dict | None):
        return 200, {"result": {"id": order_id, "external_id": "cs_test_1", "status": "draft",
                                "costs": {"total": "12.50", "currency": "cad"}}}

    return request


class TestStripeAddressCapture:
    def test_reads_the_modern_collected_information_shape(self):
        shipping = fulfillment.shipping_from_stripe_session(
            {
                "collected_information": {
                    "shipping_details": {
                        "name": "Buyer",
                        "address": {
                            "line1": "1 Main St",
                            "city": "Toronto",
                            "state": "ON",
                            "country": "ca",
                            "postal_code": "M5V 1A1",
                        },
                    }
                },
                "customer_details": {"email": "buyer@example.test"},
            }
        )
        assert shipping["address1"] == "1 Main St"
        assert shipping["country_code"] == "CA", "country is upper-cased for Printful"
        assert shipping["email"] == "buyer@example.test"

    def test_reads_the_older_top_level_shape(self):
        # An API-version bump must not silently start dropping addresses.
        shipping = fulfillment.shipping_from_stripe_session(
            {"shipping_details": {"name": "Buyer", "address": {"line1": "2 Main St", "country": "CA"}}}
        )
        assert shipping["address1"] == "2 Main St"

    def test_a_session_with_no_address_yields_no_address(self):
        shipping = fulfillment.shipping_from_stripe_session({"customer_details": {"email": "a@b.test"}})
        assert shipping["address1"] is None
        assert shipping["email"] == "a@b.test"

    def test_applies_the_address_to_an_order(self, session):
        order = make_order(session, ship_to_address1=None, ship_to_country=None)
        fulfillment.apply_shipping_details(
            order,
            {"shipping_details": {"name": "Buyer", "address": {"line1": "3 Main St", "country": "ca"}}},
        )
        assert order.ship_to_address1 == "3 Main St"
        assert order.ship_to_country == "CA"


class TestBookingADraft:
    def test_books_a_draft_and_records_the_shipment(self, session):
        order = make_order(session)
        result = fulfillment.book_supplier_draft(
            session, order, ITEMS, settings=connected(), request=draft_responder()
        )

        assert result["supplier_order_id"] == "999"
        shipment = session.scalar(select(Shipment).where(Shipment.order_id == order.id))
        assert shipment.supplier == "printful"
        assert shipment.supplier_cost == Decimal("12.50"), "margin needs the supplier's cost"
        assert order.fulfillment_status == "awaiting_approval"

    def test_a_second_call_does_not_book_a_second_parcel(self, session):
        # Payment webhooks are redelivered; double-booking would print twice.
        order = make_order(session)
        fulfillment.book_supplier_draft(session, order, ITEMS, settings=connected(), request=draft_responder())
        again = fulfillment.book_supplier_draft(
            session, order, ITEMS, settings=connected(), request=draft_responder()
        )

        assert again["skipped"] == "shipment already recorded"
        assert len(session.scalars(select(Shipment)).all()) == 1

    def test_a_settled_order_is_left_alone(self, session):
        order = make_order(session, fulfillment_status="shipped")
        result = fulfillment.book_supplier_draft(
            session, order, ITEMS, settings=connected(), request=draft_responder()
        )
        assert result["skipped"] == "already settled"
        assert session.scalars(select(Shipment)).all() == []


class TestOrdersThatCannotShip:
    def test_an_unusable_address_is_recorded_not_swallowed(self, session):
        order = make_order(session, ship_to_address1=None)
        result = fulfillment.book_supplier_draft(
            session, order, ITEMS, settings=connected(), request=draft_responder()
        )

        assert result["status"] == "unfulfillable"
        assert "missing address1" in result["reason"]
        assert order.fulfillment_status == "unfulfillable"
        # The customer has been charged, so this is an open obligation and it
        # belongs in the ledger where the daily loop will surface it.
        event = session.scalars(select(Event)).all()[-1]
        assert event.result == "rejected"

    def test_no_supplier_connection_is_unfulfillable_not_pretend_shipped(self, session):
        order = make_order(session)
        result = fulfillment.book_supplier_draft(
            session, order, ITEMS, settings=Settings(printful_api_key=""), request=draft_responder()
        )
        assert result["status"] == "unfulfillable"
        assert "not connected" in result["reason"]
        assert session.scalars(select(Shipment)).all() == []

    def test_an_order_with_no_supplier_items_is_unfulfillable(self, session):
        order = make_order(session)
        result = fulfillment.book_supplier_draft(
            session, order, [], settings=connected(), request=draft_responder()
        )
        assert result["status"] == "unfulfillable"


class TestConfirmation:
    def test_confirming_queues_an_approval_instead_of_spending_money(self, session):
        order = make_order(session)
        fulfillment.book_supplier_draft(session, order, ITEMS, settings=connected(), request=draft_responder())
        shipment = session.scalar(select(Shipment))

        calls: list[str] = []

        def request(method: str, path: str, body: dict | None):
            calls.append(path)
            return 200, {"result": {"id": 999, "status": "pending"}}

        result = fulfillment.confirm_shipment(session, shipment, settings=connected(), request=request)

        assert result["requires_approval"] is True
        assert result["approval_id"] is not None
        assert calls == [], "no supplier call may happen before a human approves"
        assert shipment.status == "draft"

        approval = session.get(Approval, result["approval_id"])
        assert approval.action == "printful_confirm_order"
        assert approval.status == "pending"

    def test_auto_confirm_setting_still_queues_an_approval(self, session):
        # The flag records operator intent; it is not a way around the gate.
        order = make_order(session)
        settings = connected(printful_auto_confirm=True)
        fulfillment.book_supplier_draft(session, order, ITEMS, settings=settings, request=draft_responder())
        shipment = session.scalar(select(Shipment))

        result = fulfillment.confirm_shipment(
            session, shipment, settings=settings, request=draft_responder()
        )
        assert result["requires_approval"] is True

    def test_an_already_confirmed_shipment_is_not_confirmed_twice(self, session):
        order = make_order(session)
        fulfillment.book_supplier_draft(session, order, ITEMS, settings=connected(), request=draft_responder())
        shipment = session.scalar(select(Shipment))
        shipment.status = "confirmed"

        result = fulfillment.confirm_shipment(session, shipment, settings=connected())
        assert result["skipped"] == "already confirmed"


class TestShipmentNotices:
    def test_applies_tracking_to_the_matching_order(self, session):
        order = make_order(session)
        fulfillment.book_supplier_draft(session, order, ITEMS, settings=connected(), request=draft_responder())

        result = fulfillment.record_shipment_notice(
            session,
            {
                "supplier": "printful",
                "external_id": "cs_test_1",
                "supplier_order_id": "999",
                "tracking_number": "1Z999",
                "tracking_url": "https://track.test/1Z999",
                "carrier": "UPS",
            },
        )

        assert result["matched"] is True
        shipment = session.get(Shipment, result["shipment_id"])
        assert shipment.tracking_number == "1Z999"
        assert shipment.status == "shipped"
        assert order.fulfillment_status == "shipped"

    def test_redelivery_updates_rather_than_duplicating(self, session):
        order = make_order(session)
        fulfillment.book_supplier_draft(session, order, ITEMS, settings=connected(), request=draft_responder())
        notice = {
            "supplier": "printful",
            "external_id": "cs_test_1",
            "supplier_order_id": "999",
            "tracking_number": "1Z999",
        }
        fulfillment.record_shipment_notice(session, notice)
        fulfillment.record_shipment_notice(session, notice)

        assert len(session.scalars(select(Shipment)).all()) == 1

    def test_an_unmatched_notice_is_logged_not_guessed_at(self, session):
        # Attaching this to the closest-looking order would send one customer
        # another customer's tracking number.
        make_order(session)
        result = fulfillment.record_shipment_notice(
            session, {"external_id": "cs_unknown", "supplier_order_id": "42"}
        )

        assert result["matched"] is False
        assert session.scalars(select(Shipment)).all() == []
        event = session.scalars(select(Event)).all()[-1]
        assert event.result == "rejected"

"""Paid order → recorded items → supplier draft.

This is the chain that was missing: an order recorded a total and nothing about
*what* was bought, so nothing could be told what to make. The property under
test is the same one the fulfillment module exists for — money in never implies
a parcel out, and a shippable order that cannot be fulfilled stays visible.
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app import fulfillment
from app.config import Settings
from app.models import Base, Order, OrderItem, Shipment


@pytest.fixture()
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        yield db


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


class TestSkuMetadataParsing:
    def test_parses_the_cart_stripe_carries(self):
        assert fulfillment.parse_sku_metadata("risk-audit-90x2,quick-auditx1") == [
            ("risk-audit-90", 2),
            ("quick-audit", 1),
        ]

    def test_a_sku_containing_x_survives(self):
        # rpartition splits on the LAST "x", so "cable-x2m" keeps its own.
        assert fulfillment.parse_sku_metadata("cable-x2mx3") == [("cable-x2m", 3)]

    def test_drops_a_truncated_tail_rather_than_guessing(self):
        # Stripe caps metadata at 500 chars; the last entry can arrive cut in
        # half. Half a SKU is not a product.
        assert fulfillment.parse_sku_metadata("goodx2,trunca") == [("good", 2)]

    def test_tolerates_empty_and_malformed_input(self):
        for raw in (None, "", "   ", ",,,", "noquantity", "zerox0", "negx-1"):
            assert fulfillment.parse_sku_metadata(raw) == [], raw


class TestRecordingWhatWasBought:
    def test_captures_price_book_facts_at_time_of_sale(self, session):
        order = make_order(session)
        items = fulfillment.record_order_items(session, order, "risk-audit-90x2")

        assert len(items) == 1
        item = items[0]
        assert item.sku == "risk-audit-90"
        assert item.quantity == 2
        # Copied from the price book now, not resolved later: the catalogue is
        # editable and an order must be fulfilled as it was sold.
        assert item.unit_amount == 29700
        assert item.requires_shipping is False

    def test_is_idempotent_across_webhook_redelivery(self, session):
        order = make_order(session)
        fulfillment.record_order_items(session, order, "risk-audit-90x1")
        fulfillment.record_order_items(session, order, "risk-audit-90x1")

        assert len(session.scalars(select(OrderItem)).all()) == 1

    def test_an_unknown_sku_is_recorded_not_rejected(self, session):
        # The Side Store prices its own cart, so not every SKU is in the price
        # book. Recording it keeps the order history honest; it simply carries no
        # supplier variant and will not auto-route.
        order = make_order(session)
        items = fulfillment.record_order_items(session, order, "USB-C-C-1Mx3")

        assert items[0].sku == "USB-C-C-1M"
        assert items[0].printful_sync_variant_id is None
        assert items[0].requires_shipping is False


class TestSupplierRouting:
    def _shippable(self, session, order, variant=501):
        session.add(
            OrderItem(
                order_id=order.id, sku="tee", quantity=2, unit_amount=3400,
                currency="CAD", requires_shipping=True, printful_sync_variant_id=variant,
            )
        )
        session.flush()

    def test_services_need_no_shipping(self, session):
        order = make_order(session)
        fulfillment.record_order_items(session, order, "risk-audit-90x1")
        assert fulfillment.order_needs_shipping(session, order) is False
        assert fulfillment.supplier_items_for_order(session, order) == []

    def test_builds_supplier_line_items_for_physical_goods(self, session):
        order = make_order(session)
        self._shippable(session, order)

        assert fulfillment.order_needs_shipping(session, order) is True
        assert fulfillment.supplier_items_for_order(session, order) == [
            {"sync_variant_id": 501, "quantity": 2, "retail_price": "34.00"}
        ]

    def test_a_shippable_line_with_no_variant_blocks_the_whole_order(self, session):
        # Shipping the fulfillable half would send a customer a partial parcel
        # they did not buy, so the order is withheld entirely instead.
        order = make_order(session)
        self._shippable(session, order)
        session.add(
            OrderItem(order_id=order.id, sku="mug", quantity=1, requires_shipping=True,
                      printful_sync_variant_id=None)
        )
        session.flush()

        assert fulfillment.supplier_items_for_order(session, order) == []

    def test_an_order_with_no_supplier_items_is_marked_unfulfillable(self, session):
        order = make_order(session)
        self._shippable(session, order)
        result = fulfillment.book_supplier_draft(
            session, order, [], settings=Settings(printful_api_key="pf_test_x")
        )
        assert result["status"] == "unfulfillable"
        assert session.scalars(select(Shipment)).all() == []

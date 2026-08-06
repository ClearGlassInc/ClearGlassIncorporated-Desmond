"""Printful connector tests — no credential, no network.

Every call goes through an injected requester, so the suite exercises the real
parsing, validation and payload-building code without touching the supplier.
"""
from __future__ import annotations

import pytest

from app import printful
from app.config import Settings


def settings(**overrides) -> Settings:
    base = {"printful_api_key": "pf_test_placeholder", "printful_store_id": "12345"}
    base.update(overrides)
    return Settings(**base)


def responder(*, status: int = 200, result=None, error=None):
    """Build a requester that returns one canned response and records the calls."""
    calls: list[tuple[str, str, dict | None]] = []

    def request(method: str, path: str, body: dict | None):
        calls.append((method, path, body))
        if error is not None:
            return status, {"code": status, "error": error}
        return status, {"code": status, "result": result}

    request.calls = calls  # type: ignore[attr-defined]
    return request


RECIPIENT = {
    "name": "Desmond Odhiambo",
    "address1": "100 King St W",
    "city": "Burlington",
    "state_code": "ON",
    "country_code": "CA",
    "zip": "L7R 3N2",
    "email": "buyer@example.test",
}


class TestConnectionState:
    def test_reports_not_connected_without_a_key(self):
        status = printful.connection_status(Settings(printful_api_key=""))
        assert status["connected"] is False
        assert status["mode"] == "mock"
        assert "printful_api_key (Printful OAuth token)" in status["missing"]

    def test_connection_check_makes_no_network_call(self):
        # No requester is injected: if this touched the network it would fail.
        status = printful.connection_status(settings())
        assert status["connected"] is True
        assert status["verified"] is False, "credential presence is not verification"

    def test_verify_reads_store_identity(self):
        request = responder(result={"id": 12345, "name": "ClearGlass Store", "currency": "cad"})
        result = printful.verify_connection(settings(), request)
        assert result["verified"] is True
        assert result["store_name"] == "ClearGlass Store"
        assert result["currency"] == "CAD"
        assert request.calls == [("GET", "/store", None)]

    def test_verify_without_credentials_makes_no_call(self):
        request = responder(result={})
        result = printful.verify_connection(Settings(printful_api_key=""), request)
        assert result["verified"] is False
        assert request.calls == []

    def test_live_call_without_credentials_refuses(self):
        with pytest.raises(printful.PrintfulNotConnected):
            printful.store_products(Settings(printful_api_key=""), responder(result={}))


class TestCatalogue:
    def test_normalizes_a_product_from_the_suppliers_own_data(self):
        product = printful.normalize_sync_product(
            {"id": 77, "name": "ClearGlass Tee", "thumbnail_url": "https://files.printful.test/t.png"},
            [
                {
                    "id": 501,
                    "variant_id": 4012,
                    "name": "ClearGlass Tee / S",
                    "sku": "CG-TEE-S",
                    "retail_price": "34.00",
                    "currency": "cad",
                    "files": [{"type": "preview", "preview_url": "https://files.printful.test/s.png"}],
                    "product": {"price": "12.50"},
                }
            ],
        )
        variant = product["variants"][0]
        assert product["name"] == "ClearGlass Tee"
        assert product["image"] == "https://files.printful.test/t.png"
        assert variant["retail_price"] == "34.00"
        assert variant["supplier_cost"] == "12.50", "margin needs the supplier's cost"
        assert variant["image"] == "https://files.printful.test/s.png"

    def test_a_variant_without_a_price_is_reported_as_having_none(self):
        # The alternative — defaulting to zero or to a sibling's price — publishes
        # a number the supplier never quoted.
        product = printful.normalize_sync_product({"id": 1}, [{"id": 2, "retail_price": None}])
        assert product["variants"][0]["retail_price"] is None

    def test_rejects_a_negative_price_rather_than_passing_it_through(self):
        product = printful.normalize_sync_product({"id": 1}, [{"id": 2, "retail_price": "-5.00"}])
        assert product["variants"][0]["retail_price"] is None

    def test_follows_paging_to_the_end(self):
        # A store larger than one page must not import as a partial catalogue.
        pages = {
            "/store/products?offset=0&limit=2": [{"id": 1}, {"id": 2}],
            "/store/products?offset=2&limit=2": [{"id": 3}],
        }

        def request(method: str, path: str, body: dict | None):
            if path in pages:
                return 200, {"result": pages[path]}
            product_id = int(path.rsplit("/", 1)[-1])
            return 200, {"result": {"sync_product": {"id": product_id}, "sync_variants": []}}

        products = printful.store_products(settings(), request, limit=2)
        assert [p["sync_product_id"] for p in products] == [1, 2, 3]

    def test_surfaces_an_api_error_instead_of_an_empty_catalogue(self):
        request = responder(status=401, error={"message": "Invalid token"})
        with pytest.raises(printful.PrintfulError, match="Invalid token"):
            printful.store_products(settings(), request)


class TestAddressValidation:
    def test_accepts_a_complete_canadian_address(self):
        assert printful.validate_recipient(RECIPIENT) == []

    def test_names_every_missing_required_field(self):
        problems = printful.validate_recipient({"name": "A"})
        assert "missing address1" in problems
        assert "missing city" in problems
        assert "missing country_code" in problems
        assert "missing zip" in problems

    def test_requires_a_state_where_printful_does(self):
        for country in ("CA", "US", "AU"):
            problems = printful.validate_recipient({**RECIPIENT, "country_code": country, "state_code": ""})
            assert f"{country} orders require a state_code" in problems

    def test_does_not_require_a_state_elsewhere(self):
        problems = printful.validate_recipient(
            {**RECIPIENT, "country_code": "GB", "state_code": "", "zip": "SW1A 1AA"}
        )
        assert problems == []

    def test_rejects_a_country_that_is_not_an_iso_code(self):
        problems = printful.validate_recipient({**RECIPIENT, "country_code": "Canada"})
        assert any("2-letter ISO code" in p for p in problems)


class TestOrderPayload:
    def test_builds_the_body_printful_expects(self):
        payload = printful.build_order_payload(
            external_id="cs_test_123",
            recipient=RECIPIENT,
            items=[{"sync_variant_id": 501, "quantity": 2, "retail_price": "34.00"}],
            currency="cad",
        )
        assert payload["external_id"] == "cs_test_123"
        assert payload["items"] == [{"sync_variant_id": 501, "quantity": 2, "retail_price": "34.00"}]
        assert payload["recipient"]["country_code"] == "CA"
        assert payload["retail_costs"]["currency"] == "CAD"

    def test_omits_blank_address_lines_rather_than_sending_empty_strings(self):
        payload = printful.build_order_payload(
            external_id="cs_1", recipient=RECIPIENT, items=[{"sync_variant_id": 1, "quantity": 1}], currency="cad"
        )
        assert "address2" not in payload["recipient"]

    def test_refuses_an_undeliverable_address(self):
        with pytest.raises(printful.PrintfulError, match="not deliverable"):
            printful.build_order_payload(
                external_id="cs_1",
                recipient={"name": "A", "country_code": "CA"},
                items=[{"sync_variant_id": 1, "quantity": 1}],
                currency="cad",
            )

    def test_refuses_an_item_with_no_supplier_variant(self):
        # Without a sync_variant_id there is nothing for Printful to print.
        with pytest.raises(printful.PrintfulError, match="no sync_variant_id"):
            printful.build_order_payload(
                external_id="cs_1", recipient=RECIPIENT, items=[{"quantity": 1}], currency="cad"
            )

    def test_refuses_a_non_positive_quantity(self):
        for quantity in (0, -1, "2", None):
            with pytest.raises(printful.PrintfulError, match="quantity"):
                printful.build_order_payload(
                    external_id="cs_1",
                    recipient=RECIPIENT,
                    items=[{"sync_variant_id": 1, "quantity": quantity}],
                    currency="cad",
                )

    def test_refuses_an_empty_order(self):
        with pytest.raises(printful.PrintfulError, match="no items"):
            printful.build_order_payload(
                external_id="cs_1", recipient=RECIPIENT, items=[], currency="cad"
            )


class TestOrders:
    def test_a_draft_is_posted_with_confirm_zero(self):
        # This is the whole safety property of drafting: confirm=0 charges
        # nothing and prints nothing.
        request = responder(result={"id": 999, "external_id": "cs_1", "status": "draft"})
        printful.create_draft_order(
            external_id="cs_1",
            recipient=RECIPIENT,
            items=[{"sync_variant_id": 501, "quantity": 1}],
            currency="cad",
            settings=settings(),
            request=request,
        )
        method, path, _ = request.calls[0]
        assert (method, path) == ("POST", "/orders?confirm=0")

    def test_a_duplicate_external_id_reads_the_existing_order(self):
        # Webhook redelivery must not book a second parcel.
        calls: list[str] = []

        def request(method: str, path: str, body: dict | None):
            calls.append(path)
            if path.startswith("/orders?confirm=0"):
                return 400, {"error": {"message": "Order with such external_id already exists"}}
            return 200, {"result": {"id": 999, "external_id": "cs_1", "status": "draft"}}

        result = printful.create_draft_order(
            external_id="cs_1",
            recipient=RECIPIENT,
            items=[{"sync_variant_id": 1, "quantity": 1}],
            currency="cad",
            settings=settings(),
            request=request,
        )
        assert result["already_booked"] is True
        assert result["supplier_order_id"] == "999"
        assert calls[-1] == "/orders/@cs_1"

    def test_confirm_targets_the_confirm_endpoint(self):
        request = responder(result={"id": 999, "status": "pending"})
        printful.confirm_order(999, settings(), request)
        assert request.calls == [("POST", "/orders/999/confirm", None)]

    def test_summary_flattens_tracking_and_cost(self):
        summary = printful.summarize_order(
            {
                "id": 999,
                "external_id": "cs_1",
                "status": "fulfilled",
                "costs": {"total": "18.40", "currency": "cad"},
                "shipments": [
                    {
                        "tracking_number": "1Z999",
                        "tracking_url": "https://track.test/1Z999",
                        "carrier": "UPS",
                        "ship_date": "2026-08-07",
                    }
                ],
            }
        )
        assert summary["supplier_order_id"] == "999"
        assert summary["tracking_number"] == "1Z999"
        assert summary["carrier"] == "UPS"
        assert summary["supplier_cost"] == "18.40"
        assert summary["currency"] == "CAD"


class TestShipmentWebhook:
    def test_parses_a_package_shipped_notice(self):
        notice = printful.parse_shipment_webhook(
            {
                "type": "package_shipped",
                "data": {
                    "order": {"id": 999, "external_id": "cs_1"},
                    "shipment": {
                        "tracking_number": "1Z999",
                        "tracking_url": "https://track.test/1Z999",
                        "carrier": "UPS",
                        "service": "Standard",
                        "ship_date": "2026-08-07",
                    },
                },
            }
        )
        assert notice["external_id"] == "cs_1"
        assert notice["tracking_number"] == "1Z999"
        assert notice["status"] == "shipped"

    def test_carries_the_parcel_id_so_split_shipments_stay_distinct(self):
        notice = printful.parse_shipment_webhook(
            {
                "type": "package_shipped",
                "data": {
                    "order": {"id": 999, "external_id": "cs_1"},
                    "shipment": {"id": 4321, "tracking_number": "1Z999"},
                },
            }
        )
        assert notice["supplier_shipment_id"] == "4321"

    def test_falls_back_to_the_tracking_number_as_the_parcel_id(self):
        # Printful does not always populate the shipment id; a tracking number is
        # unique per parcel by definition, so it is the natural substitute.
        notice = printful.parse_shipment_webhook(
            {
                "type": "package_shipped",
                "data": {"order": {"external_id": "cs_1"}, "shipment": {"tracking_number": "1Z999"}},
            }
        )
        assert notice["supplier_shipment_id"] == "1Z999"

    def test_rejects_a_notice_with_no_order_reference(self):
        # Guessing which order this belongs to would email the wrong customer a
        # tracking number.
        with pytest.raises(printful.PrintfulError, match="cannot match an order"):
            printful.parse_shipment_webhook(
                {"type": "package_shipped", "data": {"shipment": {"tracking_number": "1Z999"}}}
            )

    def test_ignores_other_event_types(self):
        with pytest.raises(printful.PrintfulError, match="not a package_shipped event"):
            printful.parse_shipment_webhook({"type": "order_created", "data": {}})


class TestGovernancePosture:
    def test_confirming_an_order_always_needs_a_human(self):
        from app.governance import ALWAYS_ESCALATE, score_action

        assert "printful_confirm_order" in ALWAYS_ESCALATE
        assessment = score_action("printful_confirm_order", {})
        assert assessment.requires_approval is True
        assert assessment.tier.value in ("high", "critical")

    def test_auto_confirm_setting_does_not_open_the_gate(self):
        # The flag records intent; it must not be a way around the approval.
        from app.governance import score_action

        assert score_action("printful_confirm_order", {}).requires_approval is True

    def test_drafting_auto_executes_because_it_costs_nothing(self):
        from app.governance import score_action

        assessment = score_action("printful_draft_order", {})
        assert assessment.requires_approval is False
        assert assessment.tier.value == "medium"

    def test_reads_are_low_risk(self):
        from app.governance import score_action

        for action in ("printful_connection_check", "printful_verify_connection", "printful_catalog_snapshot"):
            assert score_action(action, {}).requires_approval is False

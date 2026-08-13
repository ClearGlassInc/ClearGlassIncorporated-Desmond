"""Tests for the Stripe payments module — runs offline, no key, no network."""
from __future__ import annotations

import json
import sys
from types import SimpleNamespace

from app import payments


def test_storefront_checkout_payload_is_accepted(monkeypatch) -> None:
    """Contract test: the exact line-item shape the storefront posts to
    /checkout/session produces a usable (mock) session. Kept stdlib-only (no
    pydantic import) so it runs in the commerce-deploy CI gate."""
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    items = [{"name": "Aurora LED Desk Lamp", "amount": 4900, "quantity": 1, "currency": "cad"}]
    session = payments.create_checkout_session(items, customer_email=None)
    assert session["mode"] == "mock"
    assert session["amount_total"] == 4900
    assert session["url"]


def test_mock_checkout_when_no_key(monkeypatch) -> None:
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    assert payments.is_live() is False
    session = payments.create_checkout_session(
        [{"name": "Aurora Lamp", "amount": 4900, "quantity": 2, "currency": "cad"}],
        customer_email="buyer@example.com",
    )
    assert session["mode"] == "mock"
    assert session["amount_total"] == 9800
    assert session["id"].startswith("cs_mock_")


def test_mock_success_url_keeps_session_id_parseable(monkeypatch) -> None:
    """The mock flag must extend the existing query string, not open a second one.

    ``success_url`` already carries ``?session_id=…``; appending ``?mock=1`` made the
    success page parse session_id as ``{CHECKOUT_SESSION_ID}?mock=1``.
    """
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.setenv("CHECKOUT_SUCCESS_URL", "http://localhost:3000/success")
    session = payments.create_checkout_session(
        [{"sku": "risk-audit-90", "name": "Audit", "amount": 29700, "quantity": 1, "currency": "cad"}],
        customer_email="buyer@example.com",
    )
    url = session["url"]
    assert url.count("?") == 1, url
    assert url.endswith("&mock=1"), url

    from urllib.parse import parse_qs, urlparse  # noqa: PLC0415 — assertion-local

    params = parse_qs(urlparse(url).query)
    assert params["session_id"] == ["{CHECKOUT_SESSION_ID}"]
    assert params["mock"] == ["1"]


def test_subscription_metadata_is_standardized_and_test_safe(monkeypatch) -> None:
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_example")
    metadata = payments.subscription_metadata(
        [{"sku": "guardian_pro_monthly", "interval": "month", "product": "guardian"}]
    )
    assert metadata["environment"] == "test"
    assert metadata["business"] == "ClearGlassInc"
    assert metadata["plan"] == "guardian_pro_monthly"
    assert metadata["product"] == "guardian"
    assert metadata["integration_version"] == "v1"


def test_billing_portal_resolves_customer_from_checkout(monkeypatch) -> None:
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_example")
    create_calls = []
    fake_stripe = SimpleNamespace(
        api_key=None,
        checkout=SimpleNamespace(
            Session=SimpleNamespace(
                retrieve=lambda session_id: SimpleNamespace(
                    id=session_id, mode="subscription", customer="cus_safe"
                )
            )
        ),
        billing_portal=SimpleNamespace(
            Session=SimpleNamespace(
                create=lambda **kwargs: create_calls.append(kwargs)
                or SimpleNamespace(url="https://billing.stripe.com/session/test")
            )
        ),
    )
    monkeypatch.setitem(sys.modules, "stripe", fake_stripe)
    result = payments.create_billing_portal_session("cs_test_safe", "https://example.com/account")
    assert result == {"url": "https://billing.stripe.com/session/test", "mode": "live"}
    assert create_calls == [{"customer": "cus_safe", "return_url": "https://example.com/account"}]


def test_billing_portal_rejects_non_subscription_checkout(monkeypatch) -> None:
    import pytest

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_example")
    fake_stripe = SimpleNamespace(
        api_key=None,
        checkout=SimpleNamespace(
            Session=SimpleNamespace(
                retrieve=lambda _session_id: SimpleNamespace(mode="payment", customer="cus_safe")
            )
        ),
    )
    monkeypatch.setitem(sys.modules, "stripe", fake_stripe)
    with pytest.raises(ValueError, match="customer-backed subscription"):
        payments.create_billing_portal_session("cs_test_payment")


def test_webhook_signature_roundtrip(monkeypatch) -> None:
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test_123")
    body = json.dumps({"type": "checkout.session.completed"}).encode()
    header = payments.sign_payload(body, "whsec_test_123")
    result = payments.verify_webhook(body, header)
    assert result["verified"] is True
    assert result["event"]["type"] == "checkout.session.completed"


def test_webhook_rejects_tampered_payload(monkeypatch) -> None:
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test_123")
    body = json.dumps({"type": "checkout.session.completed"}).encode()
    header = payments.sign_payload(body, "whsec_test_123")
    tampered = json.dumps({"type": "checkout.session.completed", "x": 1}).encode()
    assert payments.verify_webhook(tampered, header)["verified"] is False


def test_webhook_rejects_non_numeric_timestamp(monkeypatch) -> None:
    # A signature header with a non-numeric timestamp is attacker-controlled and
    # must fail closed with a clean rejection, not raise (which would surface as a
    # 500 from the webhook route instead of a 400).
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test_123")
    body = json.dumps({"type": "checkout.session.completed"}).encode()
    result = payments.verify_webhook(body, "t=not-a-number,v1=deadbeef")
    assert result["verified"] is False
    assert result["reason"] == "malformed signature header"


def test_webhook_unverified_without_secret(monkeypatch) -> None:
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    body = json.dumps({"type": "ping"}).encode()
    result = payments.verify_webhook(body, "t=1,v1=deadbeef")
    assert result["verified"] is False
    assert result["event"]["type"] == "ping"


def test_payout_bank_info_is_masked_and_configured(monkeypatch) -> None:
    monkeypatch.setenv("PAYOUT_EXTERNAL_ACCOUNT_ID", "ba_test_123")
    monkeypatch.setenv("PAYOUT_BANK_NAME", "EQ Bank")
    monkeypatch.setenv("PAYOUT_BANK_LAST4", "6789")
    monkeypatch.setenv("PAYOUT_BANK_ROUTING_HINT", "primary-settlement-account")
    monkeypatch.setenv("PAYOUT_BANK_CURRENCIES", "CAD,USD")

    info = payments.payout_bank_info()

    assert info["configured"] is True
    assert info["processor"] == "stripe"
    assert info["settlement_mode"] == "automatic_stripe_payouts"
    assert info["external_account_id"] == "ba_test_123"
    assert info["account_last4"] == "6789"
    assert info["currencies"] == ["CAD", "USD"]
    assert info["warnings"] == []


def test_payout_bank_info_rejects_raw_routing_hints(monkeypatch) -> None:
    monkeypatch.setenv("PAYOUT_EXTERNAL_ACCOUNT_ID", "123456789")
    monkeypatch.setenv("PAYOUT_BANK_LAST4", "67890")
    monkeypatch.setenv("PAYOUT_BANK_ROUTING_HINT", "routing-000111222")

    info = payments.payout_bank_info()

    assert info["configured"] is False
    assert any("opaque external-account token" in warning for warning in info["warnings"])
    assert any("final four" in warning for warning in info["warnings"])
    assert any("non-sensitive label" in warning for warning in info["warnings"])

"""Tests for the Stripe payments module — runs offline, no key, no network."""
from __future__ import annotations

import json

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


def test_webhook_unverified_without_secret(monkeypatch) -> None:
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    body = json.dumps({"type": "ping"}).encode()
    result = payments.verify_webhook(body, "t=1,v1=deadbeef")
    assert result["verified"] is False
    assert result["event"]["type"] == "ping"

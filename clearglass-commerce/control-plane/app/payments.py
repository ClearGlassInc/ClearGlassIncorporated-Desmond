"""Stripe payments — checkout sessions, webhook verification, refunds.

Design goals:
- **Import-safe & testable** without the ``stripe`` package or a live key. The module reads
  config from the environment and implements Stripe's webhook-signature scheme with stdlib
  ``hmac`` so it can be unit-tested offline.
- **Mock mode**: when ``STRIPE_SECRET_KEY`` is unset the checkout call returns a deterministic
  mock session instead of hitting the network, so local/dev/CI never require credentials.
- The live path lazily imports ``stripe`` only when a key is present.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

PAYOUT_EVENT_TYPES = frozenset(
    {"payout.created", "payout.updated", "payout.paid", "payout.failed", "payout.canceled"}
)


def _secret_key() -> str:
    return os.environ.get("STRIPE_SECRET_KEY", "")


def _webhook_secret() -> str:
    return os.environ.get("STRIPE_WEBHOOK_SECRET", "")


def is_live() -> bool:
    """True when a real Stripe secret key is configured."""
    return bool(_secret_key())


def webhook_secret_set() -> bool:
    return bool(_webhook_secret())


def create_checkout_session(
    line_items: list[dict[str, Any]],
    *,
    customer_email: str | None = None,
    success_url: str | None = None,
    cancel_url: str | None = None,
) -> dict[str, Any]:
    """Create a Stripe Checkout session, or a deterministic mock when no key is set.

    ``line_items`` use the Stripe shape: each item has ``amount`` (cents), ``currency``,
    ``name`` and ``quantity``.
    """
    amount_total = sum(int(i.get("amount", 0)) * int(i.get("quantity", 1)) for i in line_items)
    success_url = success_url or os.environ.get("CHECKOUT_SUCCESS_URL", "http://localhost:3000/success")
    cancel_url = cancel_url or os.environ.get("CHECKOUT_CANCEL_URL", "http://localhost:3000/cancel")

    if not is_live():
        return {
            "id": f"cs_mock_{abs(hash((amount_total, customer_email))) % 10**10:010d}",
            "url": f"{success_url}?mock=1",
            "mode": "mock",
            "amount_total": amount_total,
            "currency": (line_items[0].get("currency", "cad") if line_items else "cad"),
        }

    import stripe  # noqa: PLC0415 — lazy import; only needed in live mode

    stripe.api_key = _secret_key()
    session = stripe.checkout.Session.create(
        mode="payment",
        customer_email=customer_email,
        success_url=success_url,
        cancel_url=cancel_url,
        line_items=[
            {
                "quantity": int(i.get("quantity", 1)),
                "price_data": {
                    "currency": i.get("currency", "cad"),
                    "unit_amount": int(i.get("amount", 0)),
                    "product_data": {"name": i.get("name", "item")},
                },
            }
            for i in line_items
        ],
    )
    return {
        "id": session.id,
        "url": session.url,
        "mode": "live",
        "amount_total": session.amount_total,
        "currency": session.currency,
    }


def parse_payout(obj: dict[str, Any]) -> dict[str, Any]:
    """Normalize a Stripe ``payout`` object into the fields we persist.

    ``amount`` is converted from Stripe's integer cents to major units (dollars). ``destination``
    is kept as Stripe's opaque external-account token — no account/routing numbers are ever
    extracted or stored. ``arrival_date`` (unix seconds) becomes a tz-aware datetime.
    """
    raw_dest = obj.get("destination")
    # Stripe sometimes expands destination into an object; keep only its id token.
    destination = raw_dest.get("id") if isinstance(raw_dest, dict) else raw_dest

    arrival_ts = obj.get("arrival_date")
    arrival = (
        datetime.fromtimestamp(int(arrival_ts), tz=timezone.utc)
        if isinstance(arrival_ts, (int, float))
        else None
    )

    return {
        "stripe_payout_id": obj.get("id"),
        "amount": Decimal(str(obj.get("amount", 0))) / Decimal("100"),
        "currency": (obj.get("currency") or "cad").upper(),
        "status": obj.get("status") or "pending",
        "destination": destination,
        "arrival_date": arrival,
    }


def sign_payload(payload: bytes, secret: str, timestamp: int | None = None) -> str:
    """Produce a Stripe-style ``Stripe-Signature`` header value (used in tests and dev tooling)."""
    ts = timestamp if timestamp is not None else int(time.time())
    signed = f"{ts}.".encode() + payload
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def verify_webhook(payload: bytes, sig_header: str, *, tolerance: int = 300) -> dict[str, Any]:
    """Verify a Stripe webhook signature and return ``{"verified": bool, "event": dict}``.

    When no webhook secret is configured (dev), the payload is parsed but marked unverified so
    callers can decide whether to accept it.
    """
    try:
        event = json.loads(payload.decode() or "{}")
    except (ValueError, UnicodeDecodeError):
        return {"verified": False, "event": {}, "reason": "unparseable payload"}

    secret = _webhook_secret()
    if not secret:
        return {"verified": False, "event": event, "reason": "no webhook secret configured"}

    parts = dict(p.split("=", 1) for p in sig_header.split(",") if "=" in p)
    ts, given = parts.get("t"), parts.get("v1")
    if not ts or not given:
        return {"verified": False, "event": event, "reason": "malformed signature header"}

    if tolerance and abs(int(time.time()) - int(ts)) > tolerance:
        return {"verified": False, "event": event, "reason": "timestamp outside tolerance"}

    signed = f"{ts}.".encode() + payload
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    verified = hmac.compare_digest(expected, given)
    return {"verified": verified, "event": event, "reason": "ok" if verified else "signature mismatch"}

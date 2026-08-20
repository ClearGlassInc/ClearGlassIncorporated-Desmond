#!/usr/bin/env python3
# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""Register (or verify) the Stripe webhook endpoint this control plane needs.

Without a registered endpoint, Payment Links still charge the customer's card and
the control plane never hears about it: no ``orders`` row, no audit event, no
fulfillment. The money arrives and nothing records it. This script closes that
gap and is safe to re-run.

    python scripts/register_stripe_webhook.py --url https://api.example.com/webhooks/stripe
    python scripts/register_stripe_webhook.py --url ... --apply

Dry run by default, matching every other money-touching tool in this repository.
The signing secret is printed **once** by Stripe at creation time — store it as
``STRIPE_WEBHOOK_SECRET``. Until it is set, ``verify_webhook`` marks deliveries
unverified, which means anyone who can reach the endpoint can post a forged
``checkout.session.completed`` and book a fake paid order.

Stdlib only, so it runs anywhere the repo is checked out without installing the
Stripe SDK.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.stripe.com/v1/webhook_endpoints"

#: The events the control plane actually handles. Subscribing to more just
#: creates deliveries the router ignores; subscribing to fewer loses money
#: events. Mirrors CHECKOUT_SETTLEMENT_EVENTS + ATTENTION_EVENTS in
#: app/routers/payments.py — change one, change both.
EVENTS = [
    "checkout.session.completed",
    "checkout.session.async_payment_succeeded",
    "checkout.session.async_payment_failed",
    "invoice.paid",
    "invoice.payment_failed",
    "charge.refunded",
    "charge.dispute.created",
    "charge.dispute.closed",
    "payment_intent.payment_failed",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "payout.created",
    "payout.paid",
    "payout.failed",
]

SECRET_RE = re.compile(r"\b(?:sk|rk)_(?:test|live)_[A-Za-z0-9]{4,}|whsec_[A-Za-z0-9]{4,}")


def redact(text: str) -> str:
    """Never let a key or signing secret reach a log line."""
    return SECRET_RE.sub("[redacted]", text)


def call(method: str, url: str, key: str, form: list[tuple[str, str]] | None = None) -> dict:
    data = urllib.parse.urlencode(form or []).encode() if form is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", f"Bearer {key}")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - fixed https base
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        body = json.loads(exc.read().decode() or "{}")
        message = (body.get("error") or {}).get("message", "unknown error")
        raise SystemExit(f"Stripe {method} failed (HTTP {exc.code}): {redact(message)}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"could not reach Stripe: {exc.reason}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--url", required=True, help="Public https URL of /webhooks/stripe")
    parser.add_argument("--apply", action="store_true", help="Actually create it (default: dry run)")
    args = parser.parse_args(argv)

    key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    if not key:
        print("STRIPE_SECRET_KEY is not set. Export it; never commit it.", file=sys.stderr)
        return 2
    if not args.url.startswith("https://"):
        # Stripe will not deliver to plaintext http, and a webhook that silently
        # never fires is indistinguishable from having no sales.
        print(f"refusing a non-https endpoint: {args.url}", file=sys.stderr)
        return 2

    mode = "live" if "_live_" in key else "test"
    existing = call("GET", f"{API}?limit=100", key).get("data", [])
    match = next((e for e in existing if e.get("url") == args.url), None)

    if match:
        missing = sorted(set(EVENTS) - set(match.get("enabled_events") or []))
        print(f"[{mode}] endpoint already registered: {match['id']} (status: {match.get('status')})")
        if not missing:
            print("  all required events are subscribed. Nothing to do.")
            return 0
        print(f"  missing events: {', '.join(missing)}")
        if not args.apply:
            print("  re-run with --apply to add them.")
            return 0
        call("POST", f"{API}/{match['id']}", key, [("enabled_events[]", e) for e in EVENTS])
        print("  updated.")
        return 0

    if not args.apply:
        print(f"[{mode}] DRY RUN — would register {args.url}")
        for event in EVENTS:
            print(f"    + {event}")
        print("\nRe-run with --apply to create it.")
        return 0

    created = call(
        "POST",
        API,
        key,
        [("url", args.url), ("description", "ClearGlass commerce control plane")]
        + [("enabled_events[]", e) for e in EVENTS],
    )
    print(f"[{mode}] registered {created['id']}")
    secret = created.get("secret")
    if secret:
        # Stripe shows this once and never again.
        print("\nSet this now — Stripe will not show it again:")
        print(f"    STRIPE_WEBHOOK_SECRET={secret}")
        print("\nUntil it is set, deliveries are accepted but marked unverified,")
        print("which means a forged event could book a fake paid order.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

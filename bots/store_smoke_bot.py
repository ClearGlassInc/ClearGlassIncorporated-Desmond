# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""Storefront smoke bot — deterministic checkout-integrity check for the shop.

This is the "Run daily checkout smoke tests" guardrail from SOUL.md. It is a
*static* check over the shipped `store.html` / `pricing.html` — no network, no
secrets, no flakiness — so it is safe to run on every PR and on a schedule. Live
page availability is already covered by `bots/site_health_bot.py`; this bot
covers the thing that file does not: that the storefront is still *wired
correctly* and that its money-safety guarantees are intact.

Failure policy (any of these flips the smoke result to FAIL):
  * `store.html` missing, or it has no product cards.
  * A product card (`data-sku`) is not wired into every checkout config map
    (CHECKOUT / LABEL / SHORT / ETX_AMOUNT) — a silent broken button or a
    missing Interac e-Transfer flow.
  * A card is missing its buy CTA (`data-buy`) or its price.
  * The Stripe link guard (`https://(buy|book|checkout).stripe.com/`) is gone —
    without it the page would accept an arbitrary checkout URL.
  * The "nothing is auto-charged / auto-sent" guarantee is gone.
  * `pricing.html` and `store.html` disagree on which services (SKUs) exist, or
    `pricing.html` no longer links to the store.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Checkout config maps in store.html that MUST contain every product SKU. Each
# one drives part of the buy experience, so a missing key is a real defect:
#   CHECKOUT   -> Stripe Payment Link (or invoice fallback) per SKU
#   LABEL      -> human label used in the booking email + e-Transfer memo
#   SHORT      -> short name used in the e-Transfer modal
#   ETX_AMOUNT -> amount requested by Interac e-Transfer
REQUIRED_CONFIG_MAPS = ("CHECKOUT", "LABEL", "SHORT", "ETX_AMOUNT")


def extract_card_skus(html: str) -> list[str]:
    """SKUs declared by product cards, e.g. `data-sku="quick-audit"`."""
    return re.findall(r'data-sku="([\w-]+)"', html)


def extract_map_keys(html: str, name: str) -> set[str]:
    """Quoted keys of a flat JS object literal `var NAME = { "k": ... };`."""
    match = re.search(rf"var\s+{re.escape(name)}\s*=\s*\{{(.*?)\}}", html, re.DOTALL)
    if not match:
        return set()
    return set(re.findall(r"""["']([\w-]+)["']\s*:""", match.group(1)))


def check_storefront(html: str) -> list[str]:
    """Return a list of storefront defects (empty list == healthy)."""
    errors: list[str] = []

    skus = extract_card_skus(html)
    if not skus:
        return ["store.html has no product cards (data-sku)"]

    n_buy = len(re.findall(r"data-buy", html))
    n_price = len(re.findall(r'class="price"', html))
    if n_buy < len(skus):
        errors.append(f"only {n_buy} buy CTA(s) for {len(skus)} product card(s)")
    if n_price < len(skus):
        errors.append(f"only {n_price} price element(s) for {len(skus)} product card(s)")

    for name in REQUIRED_CONFIG_MAPS:
        keys = extract_map_keys(html, name)
        if not keys:
            errors.append(f"checkout config map {name} is missing or empty")
            continue
        missing = [sku for sku in skus if sku not in keys]
        if missing:
            errors.append(f"checkout config map {name} is missing SKUs: {missing}")

    # Money-safety invariants. The buy handler only accepts a checkout URL that
    # matches this guard, and the page promises nothing is auto-charged. Either
    # one disappearing is a security/trust regression, not a cosmetic one.
    if "(buy|book|checkout)" not in html or "stripe" not in html.lower():
        errors.append("Stripe checkout-link guard is missing")
    if not re.search(r"auto[- ]?(?:charg|sent)", html, re.IGNORECASE):
        errors.append("'nothing is auto-charged/auto-sent' guarantee is missing")

    return errors


def check_pricing(store_html: str, pricing_html: str) -> list[str]:
    """Cross-page consistency between pricing.html and store.html."""
    errors: list[str] = []
    store_skus = set(extract_card_skus(store_html))
    pricing_skus = set(extract_card_skus(pricing_html))
    if store_skus != pricing_skus:
        only_store = sorted(store_skus - pricing_skus)
        only_pricing = sorted(pricing_skus - store_skus)
        errors.append(
            "pricing.html and store.html disagree on SKUs "
            f"(store-only={only_store}, pricing-only={only_pricing})"
        )
    if "store.html" not in pricing_html:
        errors.append("pricing.html no longer links to store.html")
    return errors


def run(root: Path = ROOT) -> dict:
    """Run the full storefront smoke check and return a report dict."""
    errors: list[str] = []

    store = root / "store.html"
    pricing = root / "pricing.html"

    if not store.exists():
        errors.append("missing store.html")
        store_html = ""
    else:
        store_html = store.read_text(encoding="utf-8", errors="replace")
        errors += check_storefront(store_html)

    if not pricing.exists():
        errors.append("missing pricing.html")
    elif store_html:
        pricing_html = pricing.read_text(encoding="utf-8", errors="replace")
        errors += check_pricing(store_html, pricing_html)

    skus = extract_card_skus(store_html)
    return {
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "healthy": not errors,
        "skus": skus,
        "errors": errors,
    }


def main() -> None:
    report = run()
    status = "PASS" if report["healthy"] else "FAIL"
    print(f"Storefront smoke: {status} — {len(report['skus'])} SKU(s) checked")
    for err in report["errors"]:
        print(f"  - {err}")
    if not report["healthy"]:
        print(json.dumps(report, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()

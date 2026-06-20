# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""Tests for bots/store_smoke_bot.py."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bots.store_smoke_bot import (  # noqa: E402
    REQUIRED_CONFIG_MAPS,
    check_pricing,
    check_storefront,
    extract_card_skus,
    extract_map_keys,
    run,
)

# A minimal but well-formed storefront: two SKUs wired into every config map,
# with the Stripe guard and the no-auto-charge guarantee present.
GOOD_STORE = """
<article class="card" data-sku="alpha"><div class="price">$1</div><a data-buy>Buy</a></article>
<article class="card" data-sku="beta"><div class="price">$2</div><a data-buy>Buy</a></article>
<script>
  var CHECKOUT   = { "alpha": "", "beta": "" };
  var LABEL      = { "alpha": "Alpha", "beta": "Beta" };
  var SHORT      = { "alpha": "A", "beta": "B" };
  var ETX_AMOUNT = { "alpha": "$1", "beta": "$2" };
  if (/^https:\\/\\/(buy|book|checkout)\\.stripe\\.com\\//.test(link)) {}
</script>
<p>Nothing is auto-charged, and no funds are ever auto-sent.</p>
"""

GOOD_PRICING = """
<a href="store.html">Book</a>
<article class="plan" data-sku="alpha"></article>
<article class="plan" data-sku="beta"></article>
"""


class TestExtractCardSkus:
    def test_finds_declared_skus(self) -> None:
        assert extract_card_skus(GOOD_STORE) == ["alpha", "beta"]

    def test_empty_when_no_cards(self) -> None:
        assert extract_card_skus("<html>no products</html>") == []

    def test_real_store_has_expected_skus(self) -> None:
        html = (ROOT / "store.html").read_text(encoding="utf-8")
        assert set(extract_card_skus(html)) == {
            "quick-audit", "hardening", "phipa", "monitoring",
        }


class TestExtractMapKeys:
    def test_reads_flat_object_keys(self) -> None:
        assert extract_map_keys(GOOD_STORE, "CHECKOUT") == {"alpha", "beta"}

    def test_missing_map_returns_empty(self) -> None:
        assert extract_map_keys(GOOD_STORE, "DOES_NOT_EXIST") == set()


class TestCheckStorefront:
    def test_healthy_storefront_has_no_errors(self) -> None:
        assert check_storefront(GOOD_STORE) == []

    def test_no_cards_is_an_error(self) -> None:
        errors = check_storefront("<html>nothing</html>")
        assert errors and "no product cards" in errors[0]

    def test_unwired_sku_is_detected(self) -> None:
        # 'beta' exists as a card but is dropped from CHECKOUT only.
        broken = GOOD_STORE.replace('var CHECKOUT   = { "alpha": "", "beta": "" };',
                                    'var CHECKOUT   = { "alpha": "" };')
        errors = check_storefront(broken)
        assert any("CHECKOUT" in e and "beta" in e for e in errors)

    def test_missing_stripe_guard_is_detected(self) -> None:
        broken = GOOD_STORE.replace("(buy|book|checkout)", "")
        assert any("Stripe checkout-link guard" in e for e in check_storefront(broken))

    def test_missing_no_autocharge_guarantee_is_detected(self) -> None:
        broken = GOOD_STORE.replace("auto-charged", "x").replace("auto-sent", "y")
        assert any("auto-charged" in e for e in check_storefront(broken))

    def test_real_store_html_is_healthy(self) -> None:
        html = (ROOT / "store.html").read_text(encoding="utf-8")
        assert check_storefront(html) == []


class TestCheckPricing:
    def test_consistent_pages_have_no_errors(self) -> None:
        assert check_pricing(GOOD_STORE, GOOD_PRICING) == []

    def test_sku_drift_is_detected(self) -> None:
        drifted = GOOD_PRICING.replace('data-sku="beta"', 'data-sku="gamma"')
        assert any("disagree on SKUs" in e for e in check_pricing(GOOD_STORE, drifted))

    def test_missing_store_link_is_detected(self) -> None:
        no_link = GOOD_PRICING.replace('<a href="store.html">Book</a>', "")
        assert any("links to store.html" in e for e in check_pricing(GOOD_STORE, no_link))

    def test_real_pages_are_consistent(self) -> None:
        store = (ROOT / "store.html").read_text(encoding="utf-8")
        pricing = (ROOT / "pricing.html").read_text(encoding="utf-8")
        assert check_pricing(store, pricing) == []


class TestRun:
    def test_real_repo_storefront_passes(self) -> None:
        report = run()
        assert report["healthy"] is True, report["errors"]
        assert set(report["skus"]) == {"quick-audit", "hardening", "phipa", "monitoring"}

    def test_run_reports_missing_store(self, tmp_path: Path) -> None:
        report = run(root=tmp_path)
        assert report["healthy"] is False
        assert any("store.html" in e for e in report["errors"])


class TestConstants:
    def test_required_config_maps_not_empty(self) -> None:
        assert len(REQUIRED_CONFIG_MAPS) >= 1

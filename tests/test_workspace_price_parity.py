"""Pin the Workspace pricing page to the control plane's plan book.

There are two independent statements of what a Workspace seat costs:

* ``workspace.html`` — the ``PLANS`` array the browser renders and the customer
  reads before deciding to buy;
* ``clearglass-commerce/control-plane/app/data/workspace_plans.json`` — the
  server-side price authority that decides what Stripe actually charges.

Nothing but this test stops them drifting apart, and drift here is not cosmetic:
the customer agrees to one number and their card is billed another. Same reasoning
as ``tests/test_rfed_hash_parity.py``, which pins the two RFED implementations
together — change one, change both.

Stdlib only, so it runs in the root suite without the commerce web stack.
"""
from __future__ import annotations

import json
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE = ROOT / "workspace.html"
PLAN_BOOK = ROOT / "clearglass-commerce" / "control-plane" / "app" / "data" / "workspace_plans.json"

#: How a page tier maps onto the plan book's two SKUs. The page states a monthly
#: rate for each billing choice; the plan book states what Stripe charges per
#: period. For annual that is the monthly rate times twelve.
MONTHS = {"month": 1, "year": 12}


def _page_plans() -> dict[str, dict[str, int]]:
    """Extract ``{tier: {"annual": cents, "monthly": cents}}`` from workspace.html.

    Parsed from the source rather than hardcoded here — a copy of the numbers in
    this file would be a third statement of the price to keep in step, which is
    the problem, not the fix.
    """
    text = PAGE.read_text(encoding="utf-8")
    plans: dict[str, dict[str, int]] = {}
    for m in re.finditer(
        r'\{\s*id:\s*"([a-z]+)"\s*,\s*name:\s*"[^"]*"\s*,\s*annual:\s*(\d+)\s*,\s*monthly:\s*(\d+)',
        text,
    ):
        tier, annual, monthly = m.group(1), int(m.group(2)), int(m.group(3))
        plans[tier] = {"annual": annual, "monthly": monthly}
    return plans


def _book_plans() -> dict[str, dict[str, dict]]:
    raw = json.loads(PLAN_BOOK.read_text(encoding="utf-8"))
    out: dict[str, dict[str, dict]] = {}
    for plan in raw["plans"]:
        out.setdefault(plan["tier"], {})[plan["interval"]] = plan
    return out


def test_both_sources_exist_and_parse():
    """A discovery failure must fail the suite, not silently pass it."""
    assert PAGE.is_file(), f"missing {PAGE}"
    assert PLAN_BOOK.is_file(), f"missing {PLAN_BOOK}"
    page = _page_plans()
    assert page, "could not parse any PLANS entries out of workspace.html — the regex has gone stale"
    assert len(page) == 3, f"expected 3 tiers on the page, parsed {sorted(page)}"


def test_every_page_tier_exists_in_the_plan_book():
    page, book = _page_plans(), _book_plans()
    assert set(page) == set(book), (
        f"tiers differ — page has {sorted(page)}, plan book has {sorted(book)}"
    )
    for tier, intervals in book.items():
        assert set(intervals) == {"month", "year"}, f"{tier}: expected both intervals"


@pytest.mark.parametrize("interval,page_key", [("month", "monthly"), ("year", "annual")])
def test_advertised_monthly_rate_matches_the_plan_book(interval, page_key):
    """The per-person-per-month figure on the page is the one the server holds."""
    page, book = _page_plans(), _book_plans()
    for tier, rates in page.items():
        plan = book[tier][interval]
        assert plan["monthly_rate"] == rates[page_key], (
            f"{tier} {interval}: page advertises {rates[page_key]} cents/seat/month, "
            f"plan book holds {plan['monthly_rate']}"
        )


def test_charged_amount_is_the_advertised_rate_times_the_period():
    """What Stripe bills must reconcile to what the page promised.

    This is the assertion that catches the expensive mistake: an annual plan whose
    ``unit_amount`` was left at the monthly rate bills a twelfth of what the
    customer agreed, and one left at twelve times an already-annual figure bills
    twelve times too much.
    """
    for tier, intervals in _book_plans().items():
        for interval, plan in intervals.items():
            expected = plan["monthly_rate"] * MONTHS[interval]
            assert plan["unit_amount"] == expected, (
                f"{tier} {interval}: charges {plan['unit_amount']} cents/seat/period "
                f"but advertises {plan['monthly_rate']} x {MONTHS[interval]} = {expected}"
            )


def test_annual_billing_is_cheaper_than_monthly_for_every_tier():
    """The page tells customers annual saves about 17%. It has to be true."""
    for tier, intervals in _book_plans().items():
        annual_rate = intervals["year"]["monthly_rate"]
        monthly_rate = intervals["month"]["monthly_rate"]
        assert annual_rate < monthly_rate, f"{tier}: annual is not cheaper than monthly"
        saving = 1 - (annual_rate / monthly_rate)
        assert 0.15 <= saving <= 0.20, (
            f"{tier}: annual saves {saving:.1%}, but the page claims about 17%"
        )


def test_seat_bounds_match_the_pages_input_constraints():
    """The page clamps its seat input to 1..500; the server must accept that range."""
    raw = json.loads(PLAN_BOOK.read_text(encoding="utf-8"))
    text = PAGE.read_text(encoding="utf-8")
    page_min = int(re.search(r'id="seats"[^>]*\bmin="(\d+)"', text).group(1))
    page_max = int(re.search(r'id="seats"[^>]*\bmax="(\d+)"', text).group(1))
    assert raw["min_seats"] == page_min, "server minimum seats disagrees with the page input"
    assert raw["max_seats"] == page_max, "server maximum seats disagrees with the page input"


def test_trial_length_matches_the_page_copy():
    """The page promises a 14-day trial with no card charged; the book must agree."""
    raw = json.loads(PLAN_BOOK.read_text(encoding="utf-8"))
    text = PAGE.read_text(encoding="utf-8")
    assert f"{raw['trial_days']}-day trial" in text, (
        f"plan book says {raw['trial_days']} trial days, which does not appear in workspace.html"
    )


def test_prices_are_quoted_exclusive_of_tax_as_the_page_states():
    """The page says prices exclude GST/HST. Charging tax-inclusive would silently
    absorb the tax out of revenue."""
    raw = json.loads(PLAN_BOOK.read_text(encoding="utf-8"))
    for plan in raw["plans"]:
        assert plan["tax_behavior"] == "exclusive", f"{plan['sku']} is not tax-exclusive"
    assert raw["currency"] == "cad"

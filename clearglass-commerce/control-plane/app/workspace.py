"""Per-seat subscription pricing for ClearGlass Workspace.

The storefront names *which plan* and *how many people*. This module decides what
that costs. Same split as :mod:`app.pricebook`, and for the same reason: a seat
count is safe to accept from a browser, a price is not.

Seat pricing has one wrinkle a flat price book does not. A plan quotes a *monthly
rate per person* on the page, but Stripe charges a *unit amount per billing
period*. For an annual plan those differ by twelve, and conflating them either
bills a customer a twelfth of what they agreed or twelve times it. So the two
numbers are stored separately (``monthly_rate`` for display, ``unit_amount`` for
Stripe) and :func:`quote` proves they agree before anything reaches a card.

Stdlib-only, like ``pricebook.py`` and ``governance.py``, so it imports in the
minimal CI environments that run the governance gate without the web stack.

The plan book ships at ``app/data/workspace_plans.json`` and can be pointed
elsewhere with ``WORKSPACE_PLANS_PATH`` for staging or per-tenant catalogues.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

DEFAULT_PLANS = Path(__file__).parent / "data" / "workspace_plans.json"

#: Billing intervals a Workspace plan may use. Seats are billed per period, and
#: only these two appear on the pricing page.
VALID_INTERVALS = frozenset({"month", "year"})

#: How many months each interval covers. Used to reconcile the per-month rate the
#: customer is shown against the per-period amount Stripe will charge.
MONTHS_PER_INTERVAL = {"month": 1, "year": 12}


class WorkspaceError(ValueError):
    """A subscription request the plan book refuses to price.

    Unknown or inactive plans, seat counts outside the supported range, and plan
    books whose display rate disagrees with the amount Stripe would charge. All
    are caller mistakes or deployment mistakes, never a reason to guess — callers
    translate this into a 400 rather than charging an approximation.
    """


@dataclass(frozen=True)
class Plan:
    """One subscription tier at one billing interval.

    ``unit_amount`` is what Stripe charges for a single seat for a single billing
    period. ``monthly_rate`` is the per-person-per-month figure the pricing page
    advertises. For a monthly plan they are equal; for an annual plan the former
    is twelve times the latter, and :func:`_parse_plan` refuses to load a plan
    where that relationship does not hold.

    ``stripe_price_id`` points at a real Stripe Price when one exists. Until it
    does, live checkout refuses rather than inventing an inline recurring price —
    see :func:`live_blocker`.
    """

    sku: str
    tier: str
    name: str
    description: str
    interval: str        # month | year
    monthly_rate: int    # cents per seat per month — the advertised figure
    unit_amount: int     # cents per seat per billing period — what Stripe charges
    currency: str
    tax_behavior: str    # exclusive | inclusive — required when Stripe Tax is on
    stripe_price_id: str | None = None
    stripe_product_id: str | None = None
    active: bool = True

    @property
    def months(self) -> int:
        return MONTHS_PER_INTERVAL[self.interval]


@dataclass(frozen=True)
class SeatQuote:
    """What a given plan costs for a given number of seats, before tax."""

    sku: str
    tier: str
    name: str
    interval: str
    seats: int
    monthly_rate: int        # cents per seat per month
    unit_amount: int         # cents per seat per billing period
    monthly_total: int       # cents per month for the whole team
    period_total: int        # cents charged per billing period
    annual_total: int        # cents per year at this plan and seat count
    currency: str
    trial_days: int
    tax_behavior: str
    tax_included: bool = False


def _parse_plan(raw: dict[str, Any], currency: str) -> Plan:
    sku = str(raw.get("sku", "")).strip()
    if not sku:
        raise WorkspaceError("plan book entry is missing a sku")

    interval = str(raw.get("interval", ""))
    if interval not in VALID_INTERVALS:
        raise WorkspaceError(f"{sku}: interval must be one of {sorted(VALID_INTERVALS)}")

    monthly_rate = int(raw.get("monthly_rate", 0))
    unit_amount = int(raw.get("unit_amount", 0))
    if monthly_rate <= 0 or unit_amount <= 0:
        raise WorkspaceError(f"{sku}: monthly_rate and unit_amount must be positive cents")

    # The page advertises the monthly rate; Stripe charges the unit amount. If they
    # disagree the customer is billed something other than what they agreed to, so
    # refuse to load the plan at all rather than serve a quote nobody can honour.
    expected = monthly_rate * MONTHS_PER_INTERVAL[interval]
    if unit_amount != expected:
        raise WorkspaceError(
            f"{sku}: unit_amount {unit_amount} does not equal monthly_rate "
            f"{monthly_rate} x {MONTHS_PER_INTERVAL[interval]} months ({expected}); "
            "the advertised price and the charged price must agree"
        )

    return Plan(
        sku=sku,
        tier=str(raw.get("tier", sku)),
        name=str(raw.get("name", sku)),
        description=str(raw.get("description", "")),
        interval=interval,
        monthly_rate=monthly_rate,
        unit_amount=unit_amount,
        currency=str(raw.get("currency", currency)).lower(),
        tax_behavior=str(raw.get("tax_behavior", "exclusive")),
        stripe_price_id=raw.get("stripe_price_id") or None,
        stripe_product_id=raw.get("stripe_product_id") or None,
        active=bool(raw.get("active", True)),
    )


@dataclass(frozen=True)
class PlanBook:
    """The loaded plan catalogue plus the seat and trial policy that governs it."""

    plans: dict[str, Plan]
    currency: str
    trial_days: int
    min_seats: int
    max_seats: int


def _plans_path() -> Path:
    return Path(os.environ.get("WORKSPACE_PLANS_PATH", str(DEFAULT_PLANS)))


@lru_cache(maxsize=4)
def _load(path: str) -> PlanBook:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    currency = str(raw.get("currency", "cad")).lower()
    min_seats = int(raw.get("min_seats", 1))
    max_seats = int(raw.get("max_seats", 500))
    if min_seats < 1 or max_seats < min_seats:
        raise WorkspaceError(f"invalid seat bounds: min={min_seats} max={max_seats}")

    plans: dict[str, Plan] = {}
    for entry in raw.get("plans", []):
        plan = _parse_plan(entry, currency)
        if plan.sku in plans:
            raise WorkspaceError(f"{plan.sku}: duplicate sku in plan book")
        plans[plan.sku] = plan
    if not plans:
        raise WorkspaceError("plan book contains no plans")

    return PlanBook(
        plans=plans,
        currency=currency,
        trial_days=int(raw.get("trial_days", 0)),
        min_seats=min_seats,
        max_seats=max_seats,
    )


def plan_book() -> PlanBook:
    """The active plan book, cached per path."""
    return _load(str(_plans_path()))


def reset_cache() -> None:
    """Drop the cached plan book. For tests that swap WORKSPACE_PLANS_PATH."""
    _load.cache_clear()


def catalogue(*, include_inactive: bool = False) -> list[Plan]:
    """Every plan, cheapest monthly rate first, so a UI can render it in order."""
    book = plan_book()
    plans = [p for p in book.plans.values() if p.active or include_inactive]
    return sorted(plans, key=lambda p: (p.monthly_rate, p.interval))


def get_plan(sku: str) -> Plan:
    """Look up one plan, or explain precisely why it cannot be sold."""
    book = plan_book()
    plan = book.plans.get(str(sku).strip())
    if plan is None:
        raise WorkspaceError(f"unknown plan: {sku!r}")
    if not plan.active:
        raise WorkspaceError(f"{plan.sku}: this plan is no longer available")
    return plan


def quote(sku: str, seats: int) -> SeatQuote:
    """Price ``seats`` of ``sku`` without charging anything.

    Every figure is derived here from the plan book. Nothing the caller sent
    contributes to an amount — only to *which* plan and *how many* seats.
    """
    plan = get_plan(sku)
    book = plan_book()

    try:
        seats = int(seats)
    except (TypeError, ValueError) as exc:
        raise WorkspaceError("seats must be a whole number") from exc

    # Bounds are rejected rather than clamped. The pricing page clamps its input so
    # a stray keystroke never shows a nonsense total, but silently changing what a
    # caller asked to buy is a different thing: a request for 900 seats must fail
    # loudly, not quietly become an invoice for 500.
    if seats < book.min_seats:
        raise WorkspaceError(f"seats must be at least {book.min_seats}, got {seats}")
    if seats > book.max_seats:
        raise WorkspaceError(
            f"seats {seats} exceeds the maximum of {book.max_seats}; "
            "larger teams are quoted individually"
        )

    monthly_total = plan.monthly_rate * seats
    return SeatQuote(
        sku=plan.sku,
        tier=plan.tier,
        name=plan.name,
        interval=plan.interval,
        seats=seats,
        monthly_rate=plan.monthly_rate,
        unit_amount=plan.unit_amount,
        monthly_total=monthly_total,
        period_total=plan.unit_amount * seats,
        annual_total=monthly_total * 12,
        currency=plan.currency,
        trial_days=book.trial_days,
        tax_behavior=plan.tax_behavior,
        tax_included=plan.tax_behavior == "inclusive",
    )


def to_stripe_line_items(q: SeatQuote) -> list[dict[str, Any]]:
    """Render a quote as the single subscription line item Stripe will bill.

    One line item with ``quantity = seats`` — not ``seats`` separate items. That is
    what makes Stripe's own proration arithmetic work when somebody adds or removes
    a person mid-period, and it is why the subscription item quantity is the seat
    count everywhere else in the system.

    The extended total is asserted against the quote before returning. Without that
    check a future change to either side could bill a different number from the one
    the customer was shown, and nothing would notice — the same class of bug the
    Side Store cart guards against.
    """
    plan = get_plan(q.sku)
    line_items = [
        {
            "sku": plan.sku,
            "name": plan.name,
            "description": plan.description,
            "amount": plan.unit_amount,
            "currency": plan.currency,
            "quantity": q.seats,
            "tax_behavior": plan.tax_behavior,
            "interval": plan.interval,
            "stripe_price_id": plan.stripe_price_id,
        }
    ]
    extended = sum(int(i["amount"]) * int(i["quantity"]) for i in line_items)
    if extended != q.period_total:
        raise WorkspaceError(
            f"{plan.sku}: line items total {extended} but the quote said "
            f"{q.period_total}; refusing to charge a number the customer was not shown"
        )
    return line_items


def live_blocker(sku: str) -> str | None:
    """Why live checkout must refuse this plan, or ``None`` if it may proceed.

    Workspace plans have no Stripe Price yet. Live checkout could fall back to an
    inline recurring price, and that is exactly what should not happen: it would
    create subscriptions priced by this repository rather than by the Stripe
    account, so a bad deploy could bill real cards at a number no one approved in
    the Dashboard. Until a Price id exists, live mode fails closed and says why.

    Mock mode is unaffected, so the whole flow stays testable offline.
    """
    plan = get_plan(sku)
    if not plan.stripe_price_id:
        return (
            f"{plan.sku} has no Stripe Price. Create the recurring Price in Stripe, "
            "put its id in app/data/workspace_plans.json, and redeploy. Live "
            "subscription checkout will not price a plan from this repository."
        )
    return None

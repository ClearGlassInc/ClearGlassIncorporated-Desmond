"""ClearGlass Workspace — per-seat subscriptions, priced on the server.

Why this exists rather than a Payment Link: a Workspace subscription's amount
depends on a seat count the customer chooses, and it has to stay one Stripe
subscription *item* with a quantity so that adding or removing a person later
prorates correctly. A Payment Link sells a fixed basket and can express neither.

The safety posture is the Side Store's, applied to recurring money:

* the request names a plan and a seat count, never an amount;
* live checkout fails closed if Stripe Tax is off, because the page quotes
  pre-tax prices and a live charge without tax would under-collect;
* live checkout also fails closed until a real Stripe Price backs the plan, so a
  subscription can never be priced by this repository rather than by the Stripe
  account.

All three refusals are logged with a reason, so a 503 in production is
diagnosable from the audit ledger rather than from guesswork.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import payments, workspace
from ..audit import log_event
from ..db import get_session
from ..schemas import (
    CheckoutSessionOut,
    WorkspacePlanOut,
    WorkspaceQuoteOut,
    WorkspaceSubscriptionRequest,
)
from ..security import rate_limit

router = APIRouter(prefix="/workspace", tags=["workspace"])

_checkout_throttle = rate_limit("workspace_checkout", "rate_limit_checkout_per_minute")


def _quote(plan_sku: str, seats: int) -> workspace.SeatQuote:
    try:
        return workspace.quote(plan_sku, seats)
    except workspace.WorkspaceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _to_quote_out(q: workspace.SeatQuote, *, purchasable_live: bool) -> WorkspaceQuoteOut:
    return WorkspaceQuoteOut(
        sku=q.sku,
        tier=q.tier,
        name=q.name,
        interval=q.interval,
        seats=q.seats,
        monthly_rate=q.monthly_rate,
        unit_amount=q.unit_amount,
        monthly_total=q.monthly_total,
        period_total=q.period_total,
        annual_total=q.annual_total,
        currency=q.currency,
        trial_days=q.trial_days,
        tax_behavior=q.tax_behavior,
        tax_included=q.tax_included,
        purchasable_live=purchasable_live,
    )


@router.get("/plans", response_model=list[WorkspacePlanOut])
def list_plans() -> list[WorkspacePlanOut]:
    """Every plan on sale, at the prices the server will charge.

    ``purchasable_live`` tells a storefront whether this plan can currently take a
    real card, so the UI can offer a consultation instead of a checkout that would
    503. It is derived from whether a Stripe Price exists, not hardcoded.
    """
    return [
        WorkspacePlanOut(
            sku=p.sku,
            tier=p.tier,
            name=p.name,
            description=p.description,
            interval=p.interval,
            monthly_rate=p.monthly_rate,
            unit_amount=p.unit_amount,
            currency=p.currency,
            tax_behavior=p.tax_behavior,
            purchasable_live=bool(p.stripe_price_id),
        )
        for p in workspace.catalogue()
    ]


@router.post("/quote", response_model=WorkspaceQuoteOut)
def quote_subscription(req: WorkspaceSubscriptionRequest) -> WorkspaceQuoteOut:
    """Price a plan and seat count without charging anything.

    Read-only and unauthenticated by design: it is the same arithmetic the pricing
    page already performs in the browser, and letting the page ask the server for
    the authoritative number is how the two stop drifting apart.
    """
    q = _quote(req.plan_sku, req.seats)
    return _to_quote_out(q, purchasable_live=workspace.live_blocker(req.plan_sku) is None)


@router.post(
    "/checkout/session",
    response_model=CheckoutSessionOut,
    dependencies=[Depends(_checkout_throttle)],
)
def create_workspace_checkout(
    req: WorkspaceSubscriptionRequest, session: Session = Depends(get_session)
) -> CheckoutSessionOut:
    """Open a Stripe Checkout session for a Workspace subscription.

    Two live-mode refusals, both deliberate and both audited. Neither applies in
    mock mode, so the flow stays exercisable offline and in CI.
    """
    q = _quote(req.plan_sku, req.seats)

    def _refuse(reason: str, detail: str) -> HTTPException:
        log_event(
            session,
            actor="workspace",
            action="create_checkout_session",
            target=req.customer_email,
            payload={
                "rejected": reason,
                "plan_sku": q.sku,
                "seats": q.seats,
                "period_total": q.period_total,
            },
            result="rejected",
        )
        # Commit before raising: get_session rolls back on an exception, and a
        # refusal nobody can find in the ledger is worse than the refusal itself.
        session.commit()
        return HTTPException(status_code=503, detail=detail)

    if payments.is_live():
        blocker = workspace.live_blocker(q.sku)
        if blocker:
            raise _refuse("no_stripe_price", f"Workspace checkout is unavailable: {blocker}")

        if not payments.automatic_tax_enabled():
            raise _refuse(
                "automatic_tax_disabled",
                "Workspace checkout is unavailable: plans are quoted exclusive of "
                "GST/HST but Stripe Tax is not enabled, so a live charge would "
                "collect less than the customer was shown. Configure Tax settings "
                "and set STRIPE_AUTOMATIC_TAX=true.",
            )

    result = payments.create_checkout_session(
        workspace.to_stripe_line_items(q),
        customer_email=req.customer_email,
        checkout_mode="subscription",
        client_reference_id=req.client_reference_id,
        idempotency_key=req.client_reference_id,
        extra_metadata={
            "store": "workspace",
            "plan_sku": q.sku,
            "tier": q.tier,
            "seats": str(q.seats),
            "interval": q.interval,
            "quoted_period_total": str(q.period_total),
        },
    )
    log_event(
        session,
        actor="workspace",
        action="create_checkout_session",
        target=req.customer_email,
        payload={
            "amount_total": result["amount_total"],
            "mode": result["mode"],
            "plan_sku": q.sku,
            "tier": q.tier,
            "seats": q.seats,
            "interval": q.interval,
            "period_total": q.period_total,
        },
        result="executed",
    )
    return CheckoutSessionOut(**result)

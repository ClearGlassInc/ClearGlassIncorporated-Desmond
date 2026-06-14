"""Payments — Stripe checkout (customer revenue), webhook ingest, and gated refunds."""
from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import payments
from ..audit import log_event
from ..db import get_session
from ..models import Order
from ..schemas import ActionResult, CheckoutRequest, CheckoutSessionOut, RefundRequest
from ..service import run_governed_action

router = APIRouter(tags=["payments"])


@router.post("/checkout/session", response_model=CheckoutSessionOut)
def create_checkout(req: CheckoutRequest, session: Session = Depends(get_session)) -> CheckoutSessionOut:
    """Create a Stripe Checkout session for a customer cart.

    Customer-initiated purchases are normal revenue flow, not an autonomous admin action, so
    they are logged but not put behind the approval gate. Returns a mock session when no
    Stripe key is configured.
    """
    result = payments.create_checkout_session(
        [i.model_dump() for i in req.items],
        customer_email=req.customer_email,
        success_url=req.success_url,
        cancel_url=req.cancel_url,
    )
    log_event(
        session,
        actor="storefront",
        action="create_checkout_session",
        target=req.customer_email,
        payload={"amount_total": result["amount_total"], "mode": result["mode"]},
        result="executed",
    )
    return CheckoutSessionOut(**result)


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, session: Session = Depends(get_session)) -> dict:
    """Ingest Stripe webhook events. Signature is verified when a webhook secret is configured."""
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    check = payments.verify_webhook(payload, sig)

    if payments.webhook_secret_set() and not check["verified"]:
        raise HTTPException(status_code=400, detail=f"webhook rejected: {check['reason']}")

    event = check["event"]
    etype = event.get("type", "unknown")
    obj = (event.get("data") or {}).get("object") or {}

    if etype == "checkout.session.completed":
        order = Order(
            status="paid",
            total=Decimal(str((obj.get("amount_total") or 0) / 100)),
            currency=(obj.get("currency") or "cad").upper(),
            source="stripe_checkout",
        )
        session.add(order)
        session.flush()
        log_event(
            session,
            actor="stripe",
            action="order_paid",
            target=str(order.id),
            payload={"verified": check["verified"], "amount_total": obj.get("amount_total")},
            result="executed",
        )
    else:
        log_event(
            session,
            actor="stripe",
            action="stripe_webhook",
            target=etype,
            payload={"verified": check["verified"]},
            result="ok",
        )

    return {"received": True, "type": etype, "verified": check["verified"]}


@router.post("/payments/refund", response_model=ActionResult)
def refund(req: RefundRequest, session: Session = Depends(get_session)) -> ActionResult:
    """Issue a refund — CRITICAL risk, always routed to the human approval gate.

    The Stripe refund call itself runs only after the approval is approved downstream; this
    endpoint never moves money inline.
    """
    return run_governed_action(
        session,
        actor="operations_agent",
        action="trigger_refund",
        target=str(req.order_id),
        payload=req.model_dump(),
        execute=None,
    )

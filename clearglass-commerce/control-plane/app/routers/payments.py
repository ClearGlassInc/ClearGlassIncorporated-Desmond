"""Payments — Stripe checkout (customer revenue), webhook ingest, and gated refunds."""
from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import payments
from ..audit import log_event
from ..db import get_session
from ..models import Order, Payout
from ..schemas import (
    ActionResult,
    CheckoutRequest,
    CheckoutSessionOut,
    PayoutBankInfoOut,
    PayoutOut,
    RefundRequest,
)
from ..security import require_admin
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
    elif etype in payments.PAYOUT_EVENT_TYPES:
        payout = _upsert_payout(session, obj, tenant_id=event.get("account"))
        log_event(
            session,
            actor="stripe",
            action="payout_recorded",
            target=payout.stripe_payout_id,
            payload={
                "verified": check["verified"],
                "event": etype,
                "status": payout.status,
                "amount": str(payout.amount),
                "currency": payout.currency,
            },
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


def _upsert_payout(session: Session, obj: dict, *, tenant_id: str | None) -> Payout:
    """Insert or update a payout row keyed by Stripe's payout id (idempotent for retries).

    Stripe redelivers webhooks and fires several events per payout (created -> in_transit ->
    paid), so we look up by ``stripe_payout_id`` and update status/arrival in place rather than
    creating duplicate rows.
    """
    fields = payments.parse_payout(obj)
    existing = session.scalar(
        select(Payout).where(Payout.stripe_payout_id == fields["stripe_payout_id"])
    )
    if existing is None:
        payout = Payout(tenant_id=tenant_id, **fields)
        session.add(payout)
        session.flush()
        return payout

    existing.status = fields["status"]
    existing.amount = fields["amount"]
    existing.currency = fields["currency"]
    existing.destination = fields["destination"]
    existing.arrival_date = fields["arrival_date"]
    if tenant_id and not existing.tenant_id:
        existing.tenant_id = tenant_id
    session.flush()
    return existing


@router.get("/payments/payout-account", response_model=PayoutBankInfoOut)
def payout_account() -> PayoutBankInfoOut:
    """Return masked bank/payout routing metadata for earned revenue settlement.

    This endpoint never accepts or returns raw bank account/routing numbers. Stripe remains the
    system of record for the actual external bank account and performs the money movement.
    """
    return PayoutBankInfoOut(**payments.payout_bank_info())


@router.get("/payouts", response_model=list[PayoutOut])
def list_payouts(
    tenant_id: str | None = None,
    limit: int = 100,
    session: Session = Depends(get_session),
) -> list[Payout]:
    """Return recorded Stripe payouts, newest first. Optionally filter by ``tenant_id``.

    Read-only: payouts are written solely by the verified Stripe webhook, never via this API.
    """
    stmt = select(Payout).order_by(Payout.created_at.desc()).limit(max(1, min(limit, 500)))
    if tenant_id:
        stmt = stmt.where(Payout.tenant_id == tenant_id)
    return list(session.scalars(stmt).all())


@router.post("/payments/refund", response_model=ActionResult, dependencies=[Depends(require_admin)])
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

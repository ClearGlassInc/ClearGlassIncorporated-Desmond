"""The concrete work behind an approved approval.

:mod:`app.approval_executor` decides *whether* an approved action may run and
guarantees it runs once; this module is what actually runs. Kept separate so the
dispatcher imports no business logic and the set of things a human decision can
set in motion is one readable list.

Registering an executor is a deliberate act with a real implementation behind it.
An action with nothing here is reported as ``uncovered`` — still gated, still
approvable, but honest that approving it executes nothing. Inventing a plausible
no-op executor to make the coverage list look complete would be strictly worse
than the dead end this all exists to fix: the operator would be told the refund
went through.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from . import payments
from .approval_executor import register_delegated, register_executor
from .models import Approval, Order

#: Order statuses that mean money actually arrived and can be sent back.
REFUNDABLE_STATUSES = frozenset({"paid"})


def refund_order(session: Session, approval: Approval) -> dict[str, Any]:
    """Send a customer's money back, for an approval a human granted.

    Reads the order id and amount from the approval payload rather than from any
    live request: the payload is what the approver saw and agreed to, and letting
    the executing call restate them would mean approving one refund and issuing
    another.
    """
    payload = approval.payload or {}
    order_id = payload.get("order_id")
    if order_id is None:
        raise ValueError("refund approval carries no order_id")

    order = session.get(Order, int(order_id))
    if order is None:
        raise ValueError(f"order {order_id} not found")
    if order.status not in REFUNDABLE_STATUSES:
        # Covers the already-refunded case as well as never-paid. Both are a
        # refusal rather than a no-op success: an operator waiting on a refund
        # needs to hear that it did not happen.
        raise ValueError(
            f"order {order.id} is {order.status!r} — only a paid order can be refunded"
        )

    amount = payload.get("amount")
    amount = int(amount) if amount is not None else None

    result = payments.create_refund(
        order.external_ref or "",
        amount=amount,
        reason=str(payload.get("reason") or ""),
        # Single-use and stable: a retried execution of the same approval reaches
        # Stripe as the same request and returns the original refund rather than
        # issuing a second one. The approval id is the natural key because an
        # approval is itself single-use.
        idempotency_key=f"refund-approval-{approval.id}",
        metadata={"order_id": str(order.id), "approval_id": str(approval.id)},
    )

    # Partial refunds leave the order paid-but-reduced; only a full refund closes
    # it. Without the distinction a $5 goodwill refund on a $200 order would mark
    # the whole order refunded and hide $195 of real revenue.
    order.status = "refunded" if amount is None else "partially_refunded"
    session.flush()

    return {
        "order_id": order.id,
        "refund_id": result.get("id"),
        "mode": result.get("mode"),
        "amount": result.get("amount"),
        "order_status": order.status,
    }


def register_all() -> None:
    """Wire every executor. Idempotent, so importing twice is harmless."""
    register_executor("trigger_refund", refund_order)

    # Printful confirmation claims its own approval inside `confirm_shipment`,
    # which also has to take the shipment row in-flight atomically and reconcile a
    # crashed attempt against the supplier. Routing it through the generic
    # dispatcher would spend the approval outside that state machine, so it is
    # delegated rather than duplicated.
    register_delegated(
        "printful_confirm_order",
        "POST /fulfillment/shipments/{shipment_id}/confirm",
    )


register_all()

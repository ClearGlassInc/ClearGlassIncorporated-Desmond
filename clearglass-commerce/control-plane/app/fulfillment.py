"""Dropship fulfillment — from a paid order to a tracked parcel.

The lifecycle, and who is allowed to move it:

    pending           order paid, nothing sent to the supplier yet
    drafted           draft booked with Printful (costs nothing, deletable)
    confirmed         human approved; Printful is printing and will ship
    shipped           tracking received from the supplier
    unfulfillable     we cannot ship this — needs a human, and possibly a refund

The shipment row carries one extra state of its own, ``confirming``: an approval
has been spent and the supplier call is in flight. It exists so that a crash
mid-call leaves evidence rather than a row that looks untouched.

The one rule this module exists to enforce: **money in does not imply a parcel
out.** A paid order whose address Printful will not accept, or whose items have
no supplier variant, lands in ``unfulfillable`` and stays visible. It is never
quietly marked done, and the customer's money is never treated as settled
business while nothing is shipping.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import printful
from .audit import log_event
from .config import Settings, get_settings
from .governance import score_action
from .models import Approval, Order, Shipment
from .service import run_governed_action

#: Terminal-ish states that a re-run must not disturb.
SETTLED_STATUSES = frozenset({"confirmed", "shipped"})


class FulfillmentError(RuntimeError):
    """The order cannot be routed to a supplier as it stands."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ship_date(value: Any) -> datetime | None:
    """Parse a supplier ship date (``2026-08-07`` or a full ISO timestamp).

    Returns ``None`` rather than raising on anything unparseable: a malformed
    date is worth falling back on, not worth losing the whole tracking update.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def shipping_from_stripe_session(obj: dict[str, Any]) -> dict[str, Any]:
    """Pull the destination address out of a Stripe Checkout Session.

    Stripe has moved this field over the years — newer API versions nest it under
    ``collected_information``, older ones expose ``shipping_details`` at the top
    level, and a digital-only session has neither. All three are read here so an
    API-version bump cannot silently start dropping addresses, which would look
    exactly like customers forgetting to enter one.
    """
    collected = obj.get("collected_information") or {}
    details = (
        collected.get("shipping_details")
        or obj.get("shipping_details")
        or obj.get("shipping")
        or {}
    )
    address = details.get("address") or {}
    customer = obj.get("customer_details") or {}

    return {
        "name": details.get("name") or customer.get("name"),
        "address1": address.get("line1"),
        "address2": address.get("line2"),
        "city": address.get("city"),
        "state_code": address.get("state"),
        "country_code": (address.get("country") or "").upper() or None,
        "zip": address.get("postal_code"),
        "email": customer.get("email"),
        "phone": customer.get("phone"),
    }


def apply_shipping_details(order: Order, obj: dict[str, Any]) -> None:
    """Copy a Stripe session's shipping address onto the order."""
    shipping = shipping_from_stripe_session(obj)
    order.ship_to_name = shipping.get("name")
    order.ship_to_address1 = shipping.get("address1")
    order.ship_to_address2 = shipping.get("address2")
    order.ship_to_city = shipping.get("city")
    order.ship_to_state = shipping.get("state_code")
    order.ship_to_country = shipping.get("country_code")
    order.ship_to_zip = shipping.get("zip")
    order.ship_to_email = shipping.get("email")


def recipient_from_order(order: Order) -> dict[str, Any]:
    """The supplier-facing address for an order."""
    return {
        "name": order.ship_to_name,
        "address1": order.ship_to_address1,
        "address2": order.ship_to_address2,
        "city": order.ship_to_city,
        "state_code": order.ship_to_state,
        "country_code": order.ship_to_country,
        "zip": order.ship_to_zip,
        "email": order.ship_to_email,
    }


def _mark_unfulfillable(session: Session, order: Order, reason: str) -> dict[str, Any]:
    """Record that a paid order cannot ship, loudly enough that someone acts.

    Deliberately not a silent no-op: the customer has been charged, so this is an
    open obligation, and it belongs in the audit ledger where the daily loop and
    the admin queue will surface it.
    """
    order.fulfillment_status = "unfulfillable"
    log_event(
        session,
        actor="fulfillment",
        action="printful_draft_order",
        target=str(order.id),
        payload={"order_id": order.id, "reason": reason, "external_ref": order.external_ref},
        result="rejected",
        assessment=score_action("printful_draft_order", {}),
    )
    return {"status": "unfulfillable", "order_id": order.id, "reason": reason}


def book_supplier_draft(
    session: Session,
    order: Order,
    items: list[dict[str, Any]],
    *,
    settings: Settings | None = None,
    request: printful.Requester | None = None,
    actor: str = "fulfillment",
) -> dict[str, Any]:
    """Book a paid order with the supplier as a draft.

    Runs through the governance gate as ``printful_draft_order`` (medium: no
    money moves, and the draft is deletable). Returns without acting when the
    order is already past drafting, so a redelivered payment webhook cannot
    double-book a parcel.
    """
    settings = settings or get_settings()

    if order.fulfillment_status in SETTLED_STATUSES:
        return {"status": order.fulfillment_status, "order_id": order.id, "skipped": "already settled"}

    # This function promises to book a *paid* order, and everything downstream
    # assumes it. Without the check a pending or failed order could be drafted
    # and then walked through the confirmation gate, so production would start
    # on money that never arrived.
    if order.status != "paid":
        return {
            "status": order.fulfillment_status,
            "order_id": order.id,
            "skipped": f"order is {order.status!r}, not paid — nothing ships before settlement",
        }

    existing = session.scalar(select(Shipment).where(Shipment.order_id == order.id))
    if existing is not None:
        return {
            "status": order.fulfillment_status,
            "order_id": order.id,
            "shipment_id": existing.id,
            "skipped": "shipment already recorded",
        }

    # Refuse before calling out, so a bad address is a recorded obligation rather
    # than a supplier-side rejection nobody sees.
    if not printful.connection_status(settings)["connected"]:
        return _mark_unfulfillable(
            session,
            order,
            "Printful is not connected (PRINTFUL_API_KEY unset) — no supplier can ship this order",
        )
    if not items:
        return _mark_unfulfillable(session, order, "order has no line items with a supplier variant")

    problems = printful.validate_recipient(recipient_from_order(order))
    if problems:
        return _mark_unfulfillable(session, order, f"shipping address unusable: {'; '.join(problems)}")

    def execute() -> dict[str, Any]:
        return printful.create_draft_order(
            external_id=order.external_ref or f"order-{order.id}",
            recipient=recipient_from_order(order),
            items=items,
            currency=order.currency or "CAD",
            settings=settings,
            request=request,
        )

    try:
        result = run_governed_action(
            session,
            actor=actor,
            action="printful_draft_order",
            target=str(order.id),
            payload={"order_id": order.id, "item_count": len(items), "external_ref": order.external_ref},
            execute=execute,
        )
    except printful.PrintfulError as exc:
        # A supplier rejection or outage must not escape: an exception here
        # aborts the request and rolls the transaction back, leaving a *paid*
        # order sitting at `pending` with nothing recorded anywhere. That is
        # precisely the silent failure this module exists to prevent, so the
        # error becomes a recorded, visible obligation instead.
        return _mark_unfulfillable(session, order, f"supplier rejected or was unreachable: {exc}")

    detail = result.data or {}
    if not isinstance(detail, dict) or not detail.get("supplier_order_id"):
        # Queued for approval, or the supplier returned nothing usable. Either
        # way no draft exists yet, so the order stays pending rather than being
        # reported as drafted.
        return {"status": order.fulfillment_status, "order_id": order.id, "governed": True}

    shipment = Shipment(
        order_id=order.id,
        supplier="printful",
        supplier_order_id=detail.get("supplier_order_id"),
        status=detail.get("status") or "draft",
        supplier_cost=_as_decimal(detail.get("supplier_cost")),
        currency=(detail.get("currency") or order.currency or "CAD")[:3],
    )
    session.add(shipment)
    try:
        # The lookup above is a check-then-insert, so two overlapping calls can
        # both find nothing and both insert. Printful dedupes remotely on
        # external_id, but locally that would leave two confirmable rows for one
        # supplier order. The partial unique index on
        # (order_id, supplier) WHERE supplier_shipment_id IS NULL makes the
        # database the arbiter; the loser adopts the winner's row.
        session.flush()
    except IntegrityError:
        session.rollback()
        winner = session.scalar(
            select(Shipment).where(
                Shipment.order_id == order.id,
                Shipment.supplier == "printful",
            )
        )
        return {
            "status": order.fulfillment_status,
            "order_id": order.id,
            "shipment_id": winner.id if winner else None,
            "skipped": "shipment already recorded (concurrent booking)",
        }

    # `drafted` regardless of the auto-confirm flag. Reporting
    # `awaiting_approval` here would name a state with nothing in the approval
    # queue — no Approval row exists until `confirm_shipment` is called.
    order.fulfillment_status = "drafted"
    return {
        "status": order.fulfillment_status,
        "order_id": order.id,
        "shipment_id": shipment.id,
        "supplier_order_id": shipment.supplier_order_id,
        "already_booked": bool(detail.get("already_booked")),
    }


def _as_decimal(value: Any) -> Decimal | None:
    """Parse a supplier money value, or return None.

    Mirrors the connector's price parser rather than trusting anything Decimal
    will construct: ``Decimal("NaN")`` survives to ``session.flush()`` and fails
    there — outside the ``PrintfulError`` handler — rolling back the audit entry
    and leaving a paid order pending. A negative cost would quietly corrupt
    margin reporting instead.
    """
    if value in (None, ""):
        return None
    try:
        amount = Decimal(str(value))
    except (ValueError, ArithmeticError):
        return None
    if not amount.is_finite() or amount < 0:
        return None
    return amount


def claim_approval(session: Session, *, action: str, target: str) -> Approval | None:
    """Atomically claim one approved approval for this action and target.

    The gate only works if an approval is spent exactly once. The claim is a
    conditional ``UPDATE ... WHERE status = 'approved'`` whose row count is the
    proof: two concurrent confirmations race on the same row and exactly one
    wins, so a single human decision cannot be replayed into two supplier
    charges. An approval is bound to its target, so approving one shipment can
    never confirm a different one.
    """
    candidate = session.scalar(
        select(Approval)
        .where(Approval.action == action, Approval.target == target, Approval.status == "approved")
        .order_by(Approval.id)
        .limit(1)
    )
    if candidate is None:
        return None

    claimed = session.execute(
        update(Approval)
        .where(Approval.id == candidate.id, Approval.status == "approved")
        .values(status="executed")
    )
    if claimed.rowcount != 1:
        return None  # another worker claimed it first

    # Commit the claim *before* the caller spends money. A flush alone lives
    # inside the request transaction, so a crash between the supplier accepting
    # the confirmation and the request committing would roll the row back to
    # `approved` and let the same decision authorise a second charge.
    # Committing here trades that for the opposite failure: a claim that is
    # spent without the call having demonstrably happened, which needs a fresh
    # human decision rather than silently paying twice.
    session.commit()
    return candidate


#: Supplier order states that mean production has begun — past the point of a
#: harmless retry.
SUPPLIER_COMMITTED_STATES = frozenset(
    {"pending", "inprocess", "onhold", "partial", "fulfilled", "shipped"}
)


def _reconcile_in_flight(
    session: Session,
    shipment: Shipment,
    *,
    settings: Settings | None = None,
    request: printful.Requester | None = None,
    actor: str = "operator",
) -> dict[str, Any]:
    """Resolve a shipment left ``confirming`` by a crashed or failed attempt.

    The supplier is the only party that knows whether the confirmation landed,
    so it is asked. If the order is past draft, production started and the row
    settles to ``confirmed`` — no second charge. If it is still a draft, nothing
    happened and the row returns to ``draft`` so a fresh approval can retry.
    Anything unreadable leaves it ``confirming``, which is the safe stuck state.
    """
    settings = settings or get_settings()
    order = session.get(Order, shipment.order_id)

    try:
        remote = printful.order_status(
            (order.external_ref if order else None) or f"order-{shipment.order_id}",
            settings=settings,
            request=request,
        )
    except printful.PrintfulError as exc:
        log_event(
            session,
            actor=actor,
            action="printful_order_status",
            target=str(shipment.id),
            payload={"shipment_id": shipment.id, "reason": f"reconciliation failed: {exc}"},
            result="error",
            assessment=score_action("printful_order_status", {}),
        )
        return {
            "shipment_id": shipment.id,
            "status": shipment.status,
            "needs_reconciliation": True,
            "error": str(exc),
        }

    remote_status = (remote.get("status") or "").lower()
    started = remote_status in SUPPLIER_COMMITTED_STATES
    shipment.status = "confirmed" if started else "draft"
    if started and order is not None:
        order.fulfillment_status = "confirmed"

    log_event(
        session,
        actor=actor,
        action="printful_order_status",
        target=str(shipment.id),
        payload={
            "shipment_id": shipment.id,
            "reconciled_to": shipment.status,
            "supplier_status": remote_status or None,
        },
        result="executed",
        assessment=score_action("printful_order_status", {}),
    )
    return {
        "shipment_id": shipment.id,
        "status": shipment.status,
        "supplier_status": remote_status or None,
        "reconciled": True,
        "requires_approval": not started,
    }


def confirm_shipment(
    session: Session,
    shipment: Shipment,
    *,
    settings: Settings | None = None,
    request: printful.Requester | None = None,
    actor: str = "operator",
) -> dict[str, Any]:
    """Confirm a drafted supplier order. Spends money; always human-gated.

    Two-phase, because ``printful_confirm_order`` is in ``ALWAYS_ESCALATE``:

    1. No approved approval for this shipment ⇒ queue one and return its id.
       Nothing is sent to the supplier.
    2. An approved approval exists ⇒ claim it (single-use) and confirm.

    Without the second phase the gate would be a dead end: the governed runner
    always queues an escalated action, so an approval could be granted and never
    acted on, and every retry would pile up another pending row.
    """
    settings = settings or get_settings()

    if shipment.status in ("confirmed", "fulfilled", "shipped"):
        return {"status": shipment.status, "shipment_id": shipment.id, "skipped": "already confirmed"}

    # A previous attempt spent an approval and went in flight, then died before
    # recording the outcome. Whether production started is unknown *to us* but
    # known to the supplier, so ask rather than guess: retrying blind could pay
    # twice, and giving up could strand a paid order.
    if shipment.status == "confirming":
        return _reconcile_in_flight(session, shipment, settings=settings, request=request, actor=actor)

    payload = {
        "shipment_id": shipment.id,
        "order_id": shipment.order_id,
        "supplier_order_id": shipment.supplier_order_id,
        "supplier_cost": str(shipment.supplier_cost) if shipment.supplier_cost is not None else None,
    }
    approval = claim_approval(session, action="printful_confirm_order", target=str(shipment.id))

    if approval is None:
        # Reuse a pending approval instead of stacking another. Several pending
        # rows for one shipment means several *approvable* rows, and two of them
        # approved lets two requests each claim one and both call the supplier.
        pending = session.scalar(
            select(Approval).where(
                Approval.action == "printful_confirm_order",
                Approval.target == str(shipment.id),
                Approval.status == "pending",
            )
        )
        if pending is not None:
            return {
                "shipment_id": shipment.id,
                "status": shipment.status,
                "approval_id": pending.id,
                "requires_approval": True,
                "skipped": "approval already queued",
            }

        result = run_governed_action(
            session,
            actor=actor,
            action="printful_confirm_order",
            target=str(shipment.id),
            payload=payload,
            # No executor: an unapproved confirmation must not be able to reach
            # the supplier even if the scoring were ever loosened.
            execute=None,
        )
        return {
            "shipment_id": shipment.id,
            "status": shipment.status,
            "approval_id": result.approval_id,
            "requires_approval": True,
        }

    # Take the shipment in-flight atomically. Claiming an approval alone does not
    # serialise the shipment: two approved rows could be claimed concurrently and
    # both would still see `draft`. The conditional UPDATE's row count is what
    # makes exactly one caller proceed.
    in_flight = session.execute(
        update(Shipment)
        .where(Shipment.id == shipment.id, Shipment.status == "draft")
        .values(status="confirming")
    )
    if in_flight.rowcount != 1:
        session.commit()
        return {
            "shipment_id": shipment.id,
            "status": shipment.status,
            "approval_id": approval.id,
            "requires_approval": False,
            "skipped": "another confirmation is already in flight",
        }
    # Durable before the money moves: a crash from here on leaves the row visibly
    # `confirming`, which the reconciliation path above can resolve against the
    # supplier — rather than `draft`, which would invite a blind second charge.
    session.commit()

    try:
        detail = printful.confirm_order(
            shipment.supplier_order_id or "", settings=settings, request=request
        )
    except printful.PrintfulError as exc:
        # The approval stays spent — re-confirming needs a fresh human decision,
        # because the first one was acted on and the supplier may have partially
        # applied it.
        # The row stays `confirming`, not back to `draft`: the call may have
        # reached Printful before failing, and presenting it as un-started would
        # invite a second charge. The reconciliation path resolves it against
        # the supplier on the next attempt.
        log_event(
            session,
            actor=actor,
            action="printful_confirm_order",
            target=str(shipment.id),
            payload={**payload, "approval_id": approval.id, "error": str(exc)},
            result="error",
            assessment=score_action("printful_confirm_order", payload),
        )
        return {
            "shipment_id": shipment.id,
            "status": shipment.status,
            "approval_id": approval.id,
            "requires_approval": False,
            "needs_reconciliation": True,
            "error": str(exc),
        }

    # Local lifecycle state, not the supplier's. Printful reports `pending`
    # immediately after a successful confirmation, and storing that would make
    # the "already confirmed" guard above fail to recognise its own work — so a
    # second approved request could confirm, and pay for, the same order twice.
    supplier_status = detail.get("status")
    shipment.status = "confirmed"
    # Explicit None check: a confirmed cost of exactly 0 is a real value
    # (a reprint, a covered replacement) and `or` would discard it in favour
    # of the stale draft estimate.
    confirmed_cost = _as_decimal(detail.get("supplier_cost"))
    if confirmed_cost is not None:
        shipment.supplier_cost = confirmed_cost
    order = session.get(Order, shipment.order_id)
    if order is not None:
        order.fulfillment_status = "confirmed"

    log_event(
        session,
        actor=actor,
        action="printful_confirm_order",
        target=str(shipment.id),
        payload={**payload, "approval_id": approval.id, "supplier_status": supplier_status},
        result="executed",
        assessment=score_action("printful_confirm_order", payload),
    )
    return {
        "shipment_id": shipment.id,
        "status": shipment.status,
        "supplier_status": supplier_status,
        "approval_id": approval.id,
        "requires_approval": False,
        "confirmed": True,
    }


def record_shipment_notice(
    session: Session,
    notice: dict[str, Any],
) -> dict[str, Any]:
    """Apply a supplier ``package_shipped`` notice to our records.

    Idempotent on ``(supplier, supplier_shipment_id)`` — the *parcel*, not the
    order. Suppliers redeliver webhooks, and a second insert would tell the
    customer about a parcel that does not exist; but ``supplier_order_id``
    deliberately repeats across the parcels of one split shipment, so keying on
    it would collapse them into a single record.
    """
    external_id = notice.get("external_id")
    order = session.scalar(select(Order).where(Order.external_ref == external_id))
    if order is None:
        # Never guess. An unmatched notice is logged for a human rather than
        # attached to whichever order looks closest.
        log_event(
            session,
            actor="printful",
            action="printful_order_status",
            target=str(external_id),
            payload={"reason": "no order matches this external_id", "notice": notice},
            result="rejected",
            assessment=score_action("printful_order_status", {}),
        )
        return {"matched": False, "external_id": external_id}

    supplier = notice.get("supplier", "printful")
    parcel_id = notice.get("supplier_shipment_id")

    # Match on the parcel first — that is what makes a redelivery update its own
    # row. Only fall back to an unshipped draft row for this order, so a second
    # parcel of a split order cannot overwrite the first one's tracking.
    shipment = (
        session.scalar(
            select(Shipment).where(
                Shipment.supplier == supplier,
                Shipment.supplier_shipment_id == parcel_id,
            )
        )
        if parcel_id
        else None
    )

    # The parcel lookup spans every order, so a replayed or inconsistent notice
    # could name parcel P (belonging to order A) alongside order B's
    # external_id. Attaching it would update A's tracking *and* mark B shipped —
    # two customers wrong from one bad message. If the two disagree, nothing is
    # written and the conflict is recorded for a human.
    if shipment is not None and shipment.order_id != order.id:
        log_event(
            session,
            actor="printful",
            action="printful_order_status",
            target=str(order.id),
            payload={
                "reason": "parcel belongs to a different order",
                "parcel_shipment_id": parcel_id,
                "parcel_order_id": shipment.order_id,
                "notice_external_id": external_id,
                "notice_order_id": order.id,
            },
            result="rejected",
            assessment=score_action("printful_order_status", {}),
        )
        return {
            "matched": False,
            "conflict": "parcel_order_mismatch",
            "order_id": order.id,
            "parcel_order_id": shipment.order_id,
        }

    if shipment is None:
        placeholder = session.scalar(
            select(Shipment).where(
                Shipment.order_id == order.id,
                Shipment.supplier_shipment_id.is_(None),
            )
        )
        # Two split-shipment notices handled concurrently can both select this
        # same blank draft row and then assign *different* parcel ids. The ids
        # differ, so the unique index never fires, and the later commit silently
        # overwrites the first parcel's tracking. Claim the placeholder
        # atomically instead: the winner adopts it, the loser falls through and
        # inserts a row of its own.
        if placeholder is not None and parcel_id:
            claimed = session.execute(
                update(Shipment)
                .where(Shipment.id == placeholder.id, Shipment.supplier_shipment_id.is_(None))
                .values(supplier_shipment_id=parcel_id)
            )
            if claimed.rowcount == 1:
                session.refresh(placeholder)
                shipment = placeholder
        else:
            shipment = placeholder

    if shipment is None:
        shipment = Shipment(order_id=order.id, supplier=supplier)
        session.add(shipment)

    shipment.supplier_shipment_id = parcel_id or shipment.supplier_shipment_id
    shipment.supplier_order_id = notice.get("supplier_order_id") or shipment.supplier_order_id
    shipment.status = "shipped"
    shipment.tracking_number = notice.get("tracking_number") or shipment.tracking_number
    shipment.tracking_url = notice.get("tracking_url") or shipment.tracking_url
    shipment.carrier = notice.get("carrier") or shipment.carrier
    shipment.service = notice.get("service") or shipment.service
    # Prefer the supplier's own ship date. A webhook can be delayed or retried
    # hours later, so receipt time would quietly misdate the shipment.
    shipment.shipped_at = shipment.shipped_at or _parse_ship_date(notice.get("shipped_at")) or _utcnow()
    session.flush()

    order.fulfillment_status = "shipped"
    log_event(
        session,
        actor="printful",
        action="printful_order_status",
        target=str(order.id),
        payload={
            "order_id": order.id,
            "shipment_id": shipment.id,
            "tracking_number": shipment.tracking_number,
            "carrier": shipment.carrier,
        },
        result="executed",
        assessment=score_action("printful_order_status", {}),
    )
    return {"matched": True, "order_id": order.id, "shipment_id": shipment.id, "status": "shipped"}

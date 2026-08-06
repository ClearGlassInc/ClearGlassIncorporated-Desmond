"""Fulfillment routes — supplier connection, catalogue, and order routing.

Read paths (``/connection``, ``/catalog``, ``/orders/{id}``) are safe and always
available. Every write goes through the governance gate, so confirming a supplier
order — the step that spends money and starts an irreversible print run — cannot
happen without a human approval row.

The shipment webhook is the one open mutating route here, for the same reason the
Stripe one is: a supplier callback cannot carry an operator credential. It is
authenticated by a shared secret in the path and is idempotent on redelivery.
"""
from __future__ import annotations

import hmac

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import fulfillment, printful
from ..audit import log_event
from ..config import get_settings
from ..db import get_session
from ..governance import score_action
from ..models import Order, Shipment
from ..security import require_admin

router = APIRouter(prefix="/fulfillment", tags=["fulfillment"])


@router.get("/connection")
def get_connection() -> dict:
    """Supplier connection state (credential presence only — no network call)."""
    return printful.connection_status(get_settings())


@router.post("/verify", dependencies=[Depends(require_admin)])
def verify(session: Session = Depends(get_session)) -> dict:
    """Read-only supplier identity check. Writes nothing at the supplier."""
    settings = get_settings()
    result = printful.verify_connection(settings)
    action = "printful_verify_connection"
    log_event(
        session,
        actor="fulfillment_agent",
        action=action,
        target=str(result.get("store_id") or "unconnected"),
        payload={"connected": result.get("connected"), "verified": result.get("verified")},
        result="verified" if result.get("verified") else "not_verified",
        assessment=score_action(action, {}),
    )
    return result


@router.get("/catalog")
def catalog(session: Session = Depends(get_session)) -> dict:
    """The supplier's real catalogue: their products, variants, images, prices.

    Read-only, and the only source of product data fit to publish. Nothing here
    is synthesised — a supplier we cannot read is a catalogue we do not show.
    """
    settings = get_settings()
    status = printful.connection_status(settings)
    if not status["connected"]:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "printful_not_connected",
                "missing": status["missing"],
                "hint": "Set PRINTFUL_API_KEY. Until then there is no catalogue to publish.",
            },
        )
    products = printful.store_products(settings)
    action = "printful_catalog_snapshot"
    log_event(
        session,
        actor="fulfillment_agent",
        action=action,
        target="printful_store",
        payload={"product_count": len(products)},
        result="executed",
        assessment=score_action(action, {}),
    )
    return {"supplier": "printful", "count": len(products), "products": products}


@router.get("/orders/{order_id}")
def order_fulfillment(order_id: int, session: Session = Depends(get_session)) -> dict:
    """Fulfillment state and tracking for one order. Read-only."""
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    shipments = session.scalars(select(Shipment).where(Shipment.order_id == order_id)).all()
    return {
        "order_id": order.id,
        "fulfillment_status": order.fulfillment_status,
        "ship_to_country": order.ship_to_country,
        "shipments": [
            {
                "id": s.id,
                "supplier": s.supplier,
                "supplier_order_id": s.supplier_order_id,
                "status": s.status,
                "tracking_number": s.tracking_number,
                "tracking_url": s.tracking_url,
                "carrier": s.carrier,
                "supplier_cost": str(s.supplier_cost) if s.supplier_cost is not None else None,
                "currency": s.currency,
            }
            for s in shipments
        ],
    }


@router.post("/shipments/{shipment_id}/confirm", dependencies=[Depends(require_admin)])
def confirm(shipment_id: int, session: Session = Depends(get_session)) -> dict:
    """Confirm a drafted supplier order — **spends money and starts production**.

    Always escalates: without an approved approval row this queues one and
    returns its id rather than confirming.
    """
    shipment = session.get(Shipment, shipment_id)
    if shipment is None:
        raise HTTPException(status_code=404, detail="shipment not found")
    return fulfillment.confirm_shipment(session, shipment)


@router.post("/webhooks/printful/{secret}")
async def printful_webhook(
    secret: str,
    request: Request,
    session: Session = Depends(get_session),
) -> dict:
    """Supplier shipment notices (``package_shipped``).

    Authenticated by a shared secret in the path — Printful's webhooks carry no
    signature header, so the URL itself is the credential. It is compared in
    constant time, and an unset secret rejects every call rather than accepting
    all of them: failing open here would let anyone mark orders shipped.
    """
    settings = get_settings()
    configured = settings.printful_webhook_secret
    if not configured or not hmac.compare_digest(secret, configured):
        raise HTTPException(status_code=404, detail="not found")

    payload = await request.json()
    try:
        notice = printful.parse_shipment_webhook(payload)
    except printful.PrintfulError as exc:
        # Acknowledge so the supplier stops retrying, but record why we ignored it.
        log_event(
            session,
            actor="printful",
            action="printful_order_status",
            target="webhook",
            payload={"reason": str(exc), "type": payload.get("type")},
            result="rejected",
            assessment=score_action("printful_order_status", {}),
        )
        return {"received": True, "applied": False, "reason": str(exc)}

    return {"received": True, **fulfillment.record_shipment_notice(session, notice)}

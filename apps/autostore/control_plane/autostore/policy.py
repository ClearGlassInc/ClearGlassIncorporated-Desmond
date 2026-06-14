"""Policy evaluation — the *only* place decisions are made.

Returns ALLOW / DENY / ESCALATE with explicit reasons, never silent allows.
Every rule reconciles against the source-of-truth Store before deciding, so
the AI assistant can recommend but never improvise:

  - PRICING LOCK     : floor = product.min_price_cents AND discount ≤ max_pct
  - REFUND GATE      : ≤ refund_auto_max_cents auto, else ESCALATE; > 100%
                       of order value is DENY
  - AD SPEND CAP     : per-day cap enforced against record_ad_spend ledger
  - INVENTORY        : never go negative; reconcile against canonical count
"""
from __future__ import annotations

from .models import Decision, DecisionResult, EventType
from .store import Store


def _result(action: str, decision: Decision, reasons: list[str],
            payload: dict, requires_approval: bool = False) -> DecisionResult:
    return DecisionResult(
        decision=decision, action=action, reasons=reasons,
        audit_ref="",                          # filled by the ledger
        payload_validated=payload,
        requires_approval=requires_approval,
    )


def evaluate(event_type: EventType, payload: dict, store: Store) -> DecisionResult:
    p = store.policy()

    if event_type is EventType.PRICE_RECOMMENDATION:
        sku = str(payload.get("sku", ""))
        try:
            new_price = int(payload.get("new_price_cents"))
        except (TypeError, ValueError):
            return _result("price_change", Decision.DENY,
                           ["new_price_cents missing/invalid"], payload)
        product = store.get_product(sku)
        if product is None:
            return _result("price_change", Decision.DENY,
                           [f"unknown sku: {sku}"], payload)
        if new_price < product.min_price_cents:
            return _result("price_change", Decision.DENY,
                           [f"price {new_price} below floor {product.min_price_cents}"],
                           payload)
        if new_price < product.price_cents * (1 - p.max_discount_pct):
            return _result("price_change", Decision.ESCALATE,
                           [f"discount exceeds max_discount_pct={p.max_discount_pct:.2f}"],
                           payload, requires_approval=True)
        return _result("price_change", Decision.ALLOW,
                       ["within pricing lock"], payload)

    if event_type is EventType.REFUND_REQUEST:
        order_id = str(payload.get("order_id", ""))
        try:
            amount = int(payload.get("amount_cents"))
        except (TypeError, ValueError):
            return _result("refund_issue", Decision.DENY,
                           ["amount_cents missing/invalid"], payload)
        if amount <= 0:
            return _result("refund_issue", Decision.DENY,
                           ["refund amount must be positive"], payload)
        order = store.get_order(order_id)
        if order is None:
            return _result("refund_issue", Decision.DENY,
                           [f"unknown order: {order_id}"], payload)
        if amount > order.price_cents * order.qty:
            return _result("refund_issue", Decision.DENY,
                           ["refund exceeds order total"], payload)
        if amount > p.refund_auto_max_cents:
            return _result("refund_issue", Decision.ESCALATE,
                           [f"amount {amount} > auto-cap {p.refund_auto_max_cents}"],
                           payload, requires_approval=True)
        return _result("refund_issue", Decision.ALLOW,
                       ["within refund auto-cap"], payload)

    if event_type is EventType.AD_SPEND_REQUEST:
        try:
            cents = int(payload.get("amount_cents"))
        except (TypeError, ValueError):
            return _result("ad_budget_set", Decision.DENY,
                           ["amount_cents missing/invalid"], payload)
        if cents <= 0:
            return _result("ad_budget_set", Decision.DENY,
                           ["ad spend must be positive"], payload)
        if store.ad_spend_today_cents() + cents > p.ad_spend_daily_cap_cents:
            return _result("ad_budget_set", Decision.DENY,
                           [f"would exceed daily cap {p.ad_spend_daily_cap_cents}"],
                           payload)
        return _result("ad_budget_set", Decision.ALLOW,
                       ["within daily ad spend cap"], payload)

    if event_type is EventType.INVENTORY_EVENT:
        sku = str(payload.get("sku", ""))
        try:
            delta = int(payload.get("delta"))
        except (TypeError, ValueError):
            return _result("inventory_adjust", Decision.DENY,
                           ["delta missing/invalid"], payload)
        product = store.get_product(sku)
        if product is None:
            return _result("inventory_adjust", Decision.DENY,
                           [f"unknown sku: {sku}"], payload)
        if product.inventory + delta < 0:
            return _result("inventory_adjust", Decision.DENY,
                           ["would drive inventory negative"], payload)
        return _result("inventory_adjust", Decision.ALLOW,
                       ["reconciled against canonical inventory"], payload)

    return _result("noop", Decision.DENY,
                   [f"unknown event_type: {event_type}"], payload)

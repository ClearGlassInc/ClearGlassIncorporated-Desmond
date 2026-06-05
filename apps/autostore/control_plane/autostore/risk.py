"""Explainable risk scoring — an ADDITIONAL guardrail, never a bypass.

Each event is scored in [0, 1] with human-readable factors and a band
(LOW / MEDIUM / HIGH). The engine can be configured to ESCALATE an otherwise
ALLOW decision when the band crosses a threshold — i.e. risk can only ever make
the system *more* cautious, never less. It cannot turn a DENY into an ALLOW.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .models import EventType
from .store import Store


class Band(str):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


def band_at_least(band: str, threshold: str) -> bool:
    return _ORDER.get(band, 0) >= _ORDER.get(threshold, 2)


@dataclass
class RiskScore:
    score: float                       # 0..1
    band: str
    factors: list[str] = field(default_factory=list)

    @staticmethod
    def banded(score: float, factors: list[str]) -> "RiskScore":
        s = max(0.0, min(1.0, score))
        band = Band.HIGH if s >= 0.67 else Band.MEDIUM if s >= 0.34 else Band.LOW
        return RiskScore(round(s, 3), band, factors)


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


class RiskScorer:
    """Deterministic, side-effect-free risk model. Reconciles against the Store
    for context (margins, order totals, spend ledger, inventory)."""

    def score(self, event_type: EventType, payload: dict, store: Store) -> RiskScore:
        try:
            if event_type is EventType.PRICE_RECOMMENDATION:
                return self._price(payload, store)
            if event_type is EventType.REFUND_REQUEST:
                return self._refund(payload, store)
            if event_type is EventType.AD_SPEND_REQUEST:
                return self._ad(payload, store)
            if event_type is EventType.INVENTORY_EVENT:
                return self._inventory(payload, store)
        except (TypeError, ValueError, KeyError) as exc:
            # Unscoreable -> treat as elevated (cautious), never zero.
            return RiskScore.banded(0.5, [f"unscoreable payload: {exc}"])
        return RiskScore.banded(0.5, [f"no risk model for {event_type}"])

    def _price(self, payload: dict, store: Store) -> RiskScore:
        sku = str(payload.get("sku", ""))
        new = int(payload.get("new_price_cents"))
        p = store.get_product(sku)
        if p is None:
            return RiskScore.banded(1.0, [f"unknown sku {sku}"])
        factors: list[str] = []
        score = 0.0
        if p.price_cents > 0:
            discount = max(0.0, (p.price_cents - new) / p.price_cents)
            score = _clamp(discount / 0.6)            # 60% off ~ max risk
            if discount > 0:
                factors.append(f"discount {discount*100:.0f}% off current")
        margin = new - p.cost_cents
        if margin <= 0:
            score = max(score, 0.95)
            factors.append("price at/below cost — margin wipeout")
        elif new < p.cost_cents * 1.15:
            score = max(score, 0.7)
            factors.append("thin margin (<15% over cost)")
        if not factors:
            factors.append("price increase / negligible change")
        return RiskScore.banded(score, factors)

    def _refund(self, payload: dict, store: Store) -> RiskScore:
        order_id = str(payload.get("order_id", ""))
        amount = int(payload.get("amount_cents"))
        o = store.get_order(order_id)
        if o is None:
            return RiskScore.banded(1.0, [f"unknown order {order_id}"])
        total = max(1, o.price_cents * o.qty)
        ratio = amount / total
        score = _clamp(ratio)
        factors = [f"refund is {ratio*100:.0f}% of order total"]
        if ratio >= 1.0:
            factors.append("full-value refund")
        return RiskScore.banded(score, factors)

    def _ad(self, payload: dict, store: Store) -> RiskScore:
        cents = int(payload.get("amount_cents"))
        cap = max(1, store.policy().ad_spend_daily_cap_cents)
        used_after = store.ad_spend_today_cents() + cents
        frac = used_after / cap
        return RiskScore.banded(_clamp(frac),
                                [f"would use {frac*100:.0f}% of daily ad cap"])

    def _inventory(self, payload: dict, store: Store) -> RiskScore:
        sku = str(payload.get("sku", ""))
        delta = int(payload.get("delta"))
        p = store.get_product(sku)
        if p is None:
            return RiskScore.banded(1.0, [f"unknown sku {sku}"])
        base = max(1, p.inventory)
        swing = abs(delta) / base
        factors = [f"adjustment is {swing*100:.0f}% of current stock"]
        if delta < 0 and abs(delta) >= p.inventory:
            factors.append("would zero or oversell stock")
        return RiskScore.banded(_clamp(swing), factors)

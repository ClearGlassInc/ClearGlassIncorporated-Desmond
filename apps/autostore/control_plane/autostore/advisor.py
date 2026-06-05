"""Read-only advisory assistant.

Per the cited best practice — "the AI assistant should begin as read-only and
move to limited autonomy only after the control plane proves stable" — this
advisor can ONLY *propose* events. It has no reference to the engine, no Store
mutation, and cannot authorize or execute anything. Proposals are inert until
a human (or, later, a gated autonomy path) submits them through the control
plane, where policy + risk still decide.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .models import EventType
from .risk import RiskScore, RiskScorer
from .store import Store


@dataclass
class Proposal:
    """A non-binding suggestion. Submitting it still goes through policy+risk."""
    event_type: str
    payload: dict
    rationale: str
    projected_risk: RiskScore
    confidence: str                    # HIGH | MEDIUM | LOW
    advisory_only: bool = True         # always True — never executes


@dataclass
class AdvisoryReport:
    proposals: list[Proposal] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    disclaimer: str = ("Advisory only. The control plane (policy + risk + "
                       "approvals) authorizes; this assistant cannot execute.")


class ReadOnlyAdvisor:
    def __init__(self, store: Store, *, low_stock: int = 10,
                 target_margin_pct: float = 0.45) -> None:
        self.store = store
        self.low_stock = low_stock
        self.target_margin_pct = target_margin_pct
        self._risk = RiskScorer()

    def suggest_for_sku(self, sku: str) -> AdvisoryReport:
        report = AdvisoryReport()
        p = self.store.get_product(sku)
        if p is None:
            report.notes.append(f"unknown sku: {sku}")
            return report

        # 1. Restock suggestion when stock is low.
        if p.inventory <= self.low_stock:
            target = max(self.low_stock * 4, 1)
            delta = target - p.inventory
            payload = {"sku": sku, "delta": delta, "reason": "advisor restock"}
            report.proposals.append(Proposal(
                event_type=EventType.INVENTORY_EVENT.value, payload=payload,
                rationale=f"stock {p.inventory} ≤ low-stock {self.low_stock}; "
                          f"propose +{delta} to reach {target}",
                projected_risk=self._risk.score(EventType.INVENTORY_EVENT, payload, self.store),
                confidence="HIGH"))

        # 2. Margin-aware repricing — propose a price that hits target margin,
        #    but NEVER below the floor (the proposal respects the lock; the
        #    control plane will re-check anyway).
        target_price = int(round(p.cost_cents / max(0.01, 1 - self.target_margin_pct)))
        if target_price >= p.min_price_cents and target_price != p.price_cents:
            payload = {"sku": sku, "new_price_cents": target_price}
            direction = "raise" if target_price > p.price_cents else "lower"
            report.proposals.append(Proposal(
                event_type=EventType.PRICE_RECOMMENDATION.value, payload=payload,
                rationale=f"{direction} price to {target_price}c for ~"
                          f"{self.target_margin_pct*100:.0f}% margin "
                          f"(floor {p.min_price_cents}c respected)",
                projected_risk=self._risk.score(EventType.PRICE_RECOMMENDATION, payload, self.store),
                confidence="MEDIUM"))
        elif target_price < p.min_price_cents:
            report.notes.append(
                f"target-margin price {target_price}c is below floor "
                f"{p.min_price_cents}c — no price proposal (lock respected)")

        if not report.proposals:
            report.notes.append("no actions advised — within targets")
        return report

    def suggest_all(self, skus: list[str]) -> AdvisoryReport:
        out = AdvisoryReport()
        for sku in skus:
            r = self.suggest_for_sku(sku)
            out.proposals.extend(r.proposals)
            out.notes.extend(r.notes)
        return out

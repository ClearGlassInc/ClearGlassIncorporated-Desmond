"""Event loop — the only path from event → action.

    event → ingest → context (Store) → policy check → decision
                  → approval (if ESCALATE) → execute → log → learn

The engine is the *only* place workers receive validated execution packets.
Workers themselves are dumb-by-design — they don't touch policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .audit import AuditLedger
from .models import ActionLogEntry, Decision, DecisionResult, Event, EventType
from .policy import evaluate
from .store import Store, StoreError


@dataclass
class Pending:
    """An ESCALATEd decision waiting for human approval."""
    id: int
    event: Event
    result: DecisionResult
    audit_ref: str
    status: str = "pending"               # pending | approved | denied
    approver: Optional[str] = None


class Engine:
    def __init__(self, store: Store, ledger: Optional[AuditLedger] = None) -> None:
        self.store = store
        self.ledger = ledger or AuditLedger()
        self._next_event_id = 1
        self._events: list[Event] = []
        self._pending: dict[int, Pending] = {}
        self._next_pending = 1

    # --- ingest --------------------------------------------------------------
    def ingest(self, event_type: EventType, payload: dict) -> Event:
        eid = self._next_event_id
        self._next_event_id += 1
        ev = Event(id=eid, type=event_type, payload=dict(payload))
        self._events.append(ev)
        return ev

    # --- decide --------------------------------------------------------------
    def decide(self, ev: Event) -> tuple[DecisionResult, ActionLogEntry]:
        result = evaluate(ev.type, ev.payload, self.store)
        executed = False
        if result.decision is Decision.ALLOW:
            try:
                self._execute(ev, result)
                executed = True
            except StoreError as exc:
                result = DecisionResult(
                    decision=Decision.DENY,
                    action=result.action,
                    reasons=result.reasons + [f"execution refused: {exc}"],
                    audit_ref="",
                    payload_validated=result.payload_validated,
                )
        entry = self.ledger.append(
            event_id=ev.id, action=result.action, decision=result.decision,
            reasons=list(result.reasons), executed=executed,
        )
        result.audit_ref = entry.audit_ref
        if result.decision is Decision.ESCALATE:
            pid = self._next_pending
            self._next_pending += 1
            self._pending[pid] = Pending(id=pid, event=ev, result=result,
                                         audit_ref=entry.audit_ref)
        return result, entry

    def handle(self, event_type: EventType, payload: dict):
        return self.decide(self.ingest(event_type, payload))

    # --- approvals -----------------------------------------------------------
    @property
    def pending(self) -> list[Pending]:
        return [p for p in self._pending.values() if p.status == "pending"]

    def approve(self, pending_id: int, approver: str):
        p = self._pending.get(pending_id)
        if not p or p.status != "pending":
            raise StoreError(f"no pending approval {pending_id}")
        try:
            self._execute(p.event, p.result)
            executed = True
            reasons = p.result.reasons + [f"approved by {approver}"]
            decision = Decision.ALLOW
            p.status = "approved"
        except StoreError as exc:
            executed = False
            reasons = p.result.reasons + [f"approved but execution failed: {exc}"]
            decision = Decision.DENY
            p.status = "denied"
        p.approver = approver
        return self.ledger.append(event_id=p.event.id, action=p.result.action,
                                  decision=decision, reasons=reasons,
                                  executed=executed)

    def deny(self, pending_id: int, approver: str):
        p = self._pending.get(pending_id)
        if not p or p.status != "pending":
            raise StoreError(f"no pending approval {pending_id}")
        p.status = "denied"
        p.approver = approver
        return self.ledger.append(event_id=p.event.id, action=p.result.action,
                                  decision=Decision.DENY,
                                  reasons=p.result.reasons + [f"denied by {approver}"],
                                  executed=False)

    # --- execute (only after ALLOW) -----------------------------------------
    def _execute(self, ev: Event, result: DecisionResult) -> None:
        payload = result.payload_validated
        if ev.type is EventType.PRICE_RECOMMENDATION:
            self.store.update_price(payload["sku"], int(payload["new_price_cents"]))
        elif ev.type is EventType.AD_SPEND_REQUEST:
            self.store.record_ad_spend(int(payload["amount_cents"]))
        elif ev.type is EventType.INVENTORY_EVENT:
            self.store.adjust_inventory(payload["sku"], int(payload["delta"]),
                                        str(payload.get("reason", "n/a")))
        # REFUND_REQUEST: a real implementation would call a payment processor
        # here. The in-memory reference treats ALLOW as a recorded intent.

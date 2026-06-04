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
from .queue import ExecutionQueue, make_packet
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
    def __init__(self, store: Store, ledger: Optional[AuditLedger] = None,
                 queue: Optional["ExecutionQueue"] = None) -> None:
        self.store = store
        self.ledger = ledger or AuditLedger()
        self.queue = queue          # if set, ALLOW dispatches a packet instead of inline apply
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
                applied = self._dispatch(ev, result)
                executed = applied
                if not applied:
                    result.reasons = result.reasons + ["dispatched to worker queue"]
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
            applied = self._dispatch(p.event, p.result)
            executed = applied
            tail = "approved by" if applied else "approved + dispatched to worker queue by"
            reasons = p.result.reasons + [f"{tail} {approver}"]
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

    # --- dispatch (only after ALLOW) ----------------------------------------
    def _dispatch(self, ev: Event, result: DecisionResult) -> bool:
        """Apply inline (returns True) or enqueue a packet for a worker
        (returns False). Either way, policy was already decided."""
        if self.queue is not None:
            self.queue.put(make_packet(
                event_id=ev.id, action=result.action, audit_ref=result.audit_ref,
                payload={"event_type": ev.type.value, **result.payload_validated},
            ))
            return False
        apply_packet(self.store, ev.type.value, result.payload_validated)
        return True


def apply_packet(store: Store, event_type: str, payload: dict) -> None:
    """Dumb executor — applies an already-authorized packet to the Store.
    Shared by inline dispatch and the Redis worker. No policy here."""
    if event_type == EventType.PRICE_RECOMMENDATION.value:
        store.update_price(payload["sku"], int(payload["new_price_cents"]))
    elif event_type == EventType.AD_SPEND_REQUEST.value:
        store.record_ad_spend(int(payload["amount_cents"]))
    elif event_type == EventType.INVENTORY_EVENT.value:
        store.adjust_inventory(payload["sku"], int(payload["delta"]),
                               str(payload.get("reason", "n/a")))
    # REFUND_REQUEST: a real implementation would call a payment processor here.

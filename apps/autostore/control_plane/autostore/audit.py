"""Append-only, hash-chained audit ledger for Autostore actions.

Mirrors sentinel/sentinel/audit.py: every entry commits to the previous
entry's hash so tampering with history is detectable. In production the chain
is persisted to actions_log (Postgres, append-only by GRANT); here it lives
in-memory and is verified end-to-end by tests.
"""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from .models import ActionLogEntry, Decision

GENESIS = "0" * 64


def _hash_entry(*, seq: int, ts: float, event_id: int, action: str,
                decision: Decision, reasons: list[str], executed: bool,
                audit_ref: str, prev: str) -> str:
    payload = json.dumps({
        "seq": seq, "ts": ts, "event_id": event_id, "action": action,
        "decision": decision.value, "reasons": reasons,
        "executed": executed, "audit_ref": audit_ref, "prev": prev,
    }, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


class AuditLedger:
    def __init__(self) -> None:
        self._entries: list[ActionLogEntry] = []

    def append(self, *, event_id: int, action: str, decision: Decision,
               reasons: list[str], executed: bool) -> ActionLogEntry:
        seq = len(self._entries) + 1
        prev = self._entries[-1].entry_hash if self._entries else GENESIS
        ts = time.time()
        audit_ref = "AS-" + hashlib.sha256(
            f"{event_id}|{action}|{ts}|{prev}".encode()).hexdigest()[:12].upper()
        entry_hash = _hash_entry(seq=seq, ts=ts, event_id=event_id,
                                 action=action, decision=decision,
                                 reasons=reasons, executed=executed,
                                 audit_ref=audit_ref, prev=prev)
        entry = ActionLogEntry(id=seq, event_id=event_id, action=action,
                               decision=decision, reasons=reasons,
                               executed=executed, audit_ref=audit_ref,
                               prev_hash=prev, entry_hash=entry_hash)
        # ts is captured into the hash; stash for verification by snapshotting
        # on the entry's audit_ref (which we hash with ts -> stable per entry).
        self._entries.append(entry)
        self._ts: dict[int, float] = getattr(self, "_ts", {})
        self._ts[seq] = ts
        return entry

    @property
    def entries(self) -> list[ActionLogEntry]:
        return list(self._entries)

    def verify(self) -> bool:
        prev = GENESIS
        ts_map = getattr(self, "_ts", {})
        for e in self._entries:
            if e.prev_hash != prev:
                return False
            expected = _hash_entry(seq=e.id, ts=ts_map.get(e.id, 0.0),
                                   event_id=e.event_id, action=e.action,
                                   decision=e.decision, reasons=e.reasons,
                                   executed=e.executed, audit_ref=e.audit_ref,
                                   prev=prev)
            if expected != e.entry_hash:
                return False
            prev = e.entry_hash
        return True

    def snapshot(self) -> list[dict[str, Any]]:
        return [{
            "id": e.id, "event_id": e.event_id, "action": e.action,
            "decision": e.decision.value, "reasons": e.reasons,
            "executed": e.executed, "audit_ref": e.audit_ref,
            "prev_hash": e.prev_hash, "entry_hash": e.entry_hash,
        } for e in self._entries]

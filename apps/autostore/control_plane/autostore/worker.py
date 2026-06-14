"""Dumb-by-design execution worker.

Pulls authorized packets off the queue and applies them to the Store. It does
NO policy — policy was already decided by the control plane. Every applied
packet appends an audit entry so the ledger reflects execution, not just
authorization.
"""
from __future__ import annotations

import os
from typing import Optional

from .audit import AuditLedger
from .engine import apply_packet
from .models import Decision
from .queue import ExecutionQueue
from .store import Store, StoreError


class Worker:
    def __init__(self, store: Store, queue: ExecutionQueue,
                 ledger: Optional[AuditLedger] = None) -> None:
        self.store = store
        self.queue = queue
        self.ledger = ledger or AuditLedger()

    def run_once(self) -> Optional[dict]:
        """Process a single packet; return it (or None if the queue is empty)."""
        packet = self.queue.get()
        if packet is None:
            return None
        try:
            apply_packet(self.store, packet["payload"]["event_type"], packet["payload"])
            self.ledger.append(event_id=int(packet.get("event_id", 0)),
                               action=packet["action"] + "_applied",
                               decision=Decision.ALLOW,
                               reasons=[f"worker applied {packet.get('audit_ref','')}"],
                               executed=True)
        except StoreError as exc:
            self.ledger.append(event_id=int(packet.get("event_id", 0)),
                               action=packet["action"] + "_failed",
                               decision=Decision.DENY,
                               reasons=[f"worker execution failed: {exc}"],
                               executed=False)
        return packet

    def drain(self) -> int:
        n = 0
        while self.run_once() is not None:
            n += 1
        return n


def main() -> None:  # pragma: no cover - infra entrypoint
    from .queue import RedisQueue
    url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    q = RedisQueue(url=url)
    # NOTE: a production worker shares the canonical Store (Postgres), not a
    # fresh in-memory one. Wire PostgresStore here once DSN is configured.
    from .store import InMemoryStore
    w = Worker(InMemoryStore(), q)
    print(f"[autostore.worker] consuming {url} …", flush=True)
    while True:
        item = q.get_blocking(timeout=10)
        if item is None:
            continue
        q.put(item)         # put back; run_once pops via .get()
        w.run_once()


if __name__ == "__main__":  # pragma: no cover
    main()

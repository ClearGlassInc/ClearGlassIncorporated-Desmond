"""Execution queue — decouples authorization (control plane) from execution
(workers). Workers are dumb-by-design: they apply validated packets only.

``InMemoryQueue`` is the reference used by tests; ``RedisQueue`` is the
production transport (import-guarded). An execution *packet* is the minimal,
already-authorized instruction the worker must carry out — it contains no
policy, because policy was already decided.
"""
from __future__ import annotations

import json
from collections import deque
from typing import Any, Optional, Protocol


def make_packet(*, event_id: int, action: str, audit_ref: str,
                payload: dict[str, Any]) -> dict[str, Any]:
    return {"event_id": event_id, "action": action, "audit_ref": audit_ref,
            "payload": payload}


class ExecutionQueue(Protocol):
    def put(self, packet: dict[str, Any]) -> None: ...
    def get(self) -> Optional[dict[str, Any]]: ...      # None if empty
    def __len__(self) -> int: ...


class InMemoryQueue:
    def __init__(self) -> None:
        self._q: deque[dict[str, Any]] = deque()

    def put(self, packet: dict[str, Any]) -> None:
        self._q.append(dict(packet))

    def get(self) -> Optional[dict[str, Any]]:
        return self._q.popleft() if self._q else None

    def __len__(self) -> int:
        return len(self._q)


class RedisQueue:
    """Redis list-backed queue (LPUSH/BRPOP). Requires ``redis``."""

    def __init__(self, url: str = "redis://localhost:6379/0",
                 key: str = "autostore:exec") -> None:  # pragma: no cover - infra
        try:
            import redis  # noqa: F401
        except ImportError as exc:
            raise ImportError("RedisQueue requires the 'redis' package") from exc
        import redis as _redis
        self._r = _redis.from_url(url)
        self._key = key

    def put(self, packet: dict[str, Any]) -> None:  # pragma: no cover - infra
        self._r.lpush(self._key, json.dumps(packet))

    def get(self) -> Optional[dict[str, Any]]:  # pragma: no cover - infra
        raw = self._r.rpop(self._key)
        return json.loads(raw) if raw else None

    def get_blocking(self, timeout: int = 5) -> Optional[dict[str, Any]]:  # pragma: no cover
        item = self._r.brpop(self._key, timeout=timeout)
        return json.loads(item[1]) if item else None

    def __len__(self) -> int:  # pragma: no cover - infra
        return int(self._r.llen(self._key))

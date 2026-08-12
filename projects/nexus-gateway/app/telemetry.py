import asyncio
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .models import TelemetryEvent


@dataclass
class TelemetryBus:
    max_queue: int
    history_size: int
    queue: asyncio.Queue[dict[str, Any]] = field(init=False)
    history: deque[dict[str, Any]] = field(init=False)
    accepted: int = 0
    dropped: int = 0
    _task: asyncio.Task | None = None

    def __post_init__(self) -> None:
        self.queue = asyncio.Queue(maxsize=self.max_queue)
        self.history = deque(maxlen=self.history_size)

    async def start(self) -> None:
        if self._task is None or self._task.done():
            # asyncio synchronization primitives are loop-bound after first use.
            # Recreate the bounded queue on each application lifespan start so
            # test harnesses and process restarts cannot inherit a stale loop.
            self.queue = asyncio.Queue(maxsize=self.max_queue)
            self._task = asyncio.create_task(self._worker(), name="nexus-telemetry-worker")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def publish(self, event: TelemetryEvent, request_id: str) -> bool:
        item = event.model_dump(mode="json")
        item["request_id"] = request_id
        item["ingested_at"] = datetime.now(UTC).isoformat()
        try:
            self.queue.put_nowait(item)
            self.accepted += 1
            return True
        except asyncio.QueueFull:
            self.dropped += 1
            return False

    async def _worker(self) -> None:
        while True:
            item = await self.queue.get()
            try:
                self.history.append(item)
            finally:
                self.queue.task_done()

    def snapshot(self, limit: int = 25) -> list[dict[str, Any]]:
        return list(self.history)[-limit:]

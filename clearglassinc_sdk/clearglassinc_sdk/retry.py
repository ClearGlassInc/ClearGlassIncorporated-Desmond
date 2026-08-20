"""Resilience: retry with exponential backoff and jitter.

LLM APIs fail transiently — rate limits, 5xx, connection resets. `RetryPolicy`
wraps any callable (sync or async) so the `Runner` survives those without the
caller writing retry loops. Non-transient errors (bad request, auth) are
re-raised immediately rather than burning the budget.
"""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

T = TypeVar("T")

# Matched against the exception's type name and message, lowercased. Kept as
# strings so classification works without importing any provider SDK.
_DEFAULT_RETRYABLE_MARKERS: tuple[str, ...] = (
    "ratelimit",
    "rate limit",
    "timeout",
    "timed out",
    "connection",
    "temporarily unavailable",
    "service unavailable",
    "overloaded",
    "internalserver",
    "apiconnection",
    "502",
    "503",
    "504",
    "529",
)

_DEFAULT_NON_RETRYABLE_MARKERS: tuple[str, ...] = (
    "authentication",
    "permission",
    "invalid_api_key",
    "invalid request",
    "badrequest",
    "not found",
    "400",
    "401",
    "403",
    "404",
)


def is_retryable(exc: BaseException, extra_markers: tuple[str, ...] = ()) -> bool:
    """Classify an exception as transient (worth retrying) or terminal."""
    haystack = f"{type(exc).__name__} {exc}".lower()
    if any(marker in haystack for marker in _DEFAULT_NON_RETRYABLE_MARKERS):
        return False
    markers = _DEFAULT_RETRYABLE_MARKERS + extra_markers
    return any(marker in haystack for marker in markers)


@dataclass
class RetryPolicy:
    """Exponential backoff with full jitter.

    Delay before attempt *n* is `min(max_delay, base_delay * 2**(n-1))`,
    multiplied by a random factor in [0.5, 1.0] when `jitter` is on — so
    concurrent agents don't retry in lockstep.
    """

    max_attempts: int = 3
    base_delay: float = 0.5
    max_delay: float = 8.0
    jitter: bool = True
    retryable_markers: tuple[str, ...] = field(default_factory=tuple)

    def delay_for(self, attempt: int) -> float:
        """Seconds to wait before `attempt` (1-indexed retry number)."""
        raw = min(self.max_delay, self.base_delay * (2 ** max(0, attempt - 1)))
        if self.jitter:
            return raw * random.uniform(0.5, 1.0)
        return raw

    def should_retry(self, exc: BaseException, attempts_made: int) -> bool:
        if attempts_made >= self.max_attempts:
            return False
        return is_retryable(exc, self.retryable_markers)

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Run `func` under this policy, sleeping between transient failures."""
        attempts = 0
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                attempts += 1
                if not self.should_retry(exc, attempts):
                    raise
                time.sleep(self.delay_for(attempts))

    async def acall(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        """Async variant of `call`."""
        attempts = 0
        while True:
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                attempts += 1
                if not self.should_retry(exc, attempts):
                    raise
                await asyncio.sleep(self.delay_for(attempts))


NO_RETRY = RetryPolicy(max_attempts=1)

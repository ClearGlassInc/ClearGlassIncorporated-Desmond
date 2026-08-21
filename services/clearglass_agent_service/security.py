from __future__ import annotations

import hmac
import os
import threading
import time
from collections import defaultdict
from hashlib import sha256

from fastapi import Header, HTTPException, Request, status


CLEARGLASS_ORG_HEADER = "ClearGlassInc"
DEFAULT_RATE_LIMIT = 60
DEFAULT_RATE_WINDOW_SECONDS = 60

_rate_lock = threading.Lock()
_rate_windows: dict[str, list[float]] = defaultdict(list)


def _configured_keys() -> tuple[str, ...]:
    raw = os.getenv("CLEARGLASS_AGENT_API_KEYS", "")
    return tuple(item.strip() for item in raw.split(",") if item.strip())


def _allowed_orgs() -> set[str]:
    raw = os.getenv("CLEARGLASS_ALLOWED_ORGS", CLEARGLASS_ORG_HEADER)
    return {item.strip() for item in raw.split(",") if item.strip()}


def _fingerprint(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()[:12]


def _rate_limit() -> tuple[int, int]:
    try:
        limit = int(os.getenv("CLEARGLASS_AGENT_RATE_LIMIT", str(DEFAULT_RATE_LIMIT)))
        window = int(os.getenv("CLEARGLASS_AGENT_RATE_WINDOW_SECONDS", str(DEFAULT_RATE_WINDOW_SECONDS)))
    except ValueError as exc:
        raise RuntimeError("CLEARGLASS_AGENT_RATE_LIMIT and rate window must be integers") from exc
    if limit < 1 or window < 1:
        raise RuntimeError("CLEARGLASS_AGENT_RATE_LIMIT and rate window must be positive")
    return limit, window


def enforce_rate_limit(client_key: str) -> None:
    """Apply a bounded local fixed-window limit without trusting proxy headers."""
    limit, window = _rate_limit()
    now = time.monotonic()
    cutoff = now - window
    with _rate_lock:
        bucket = [stamp for stamp in _rate_windows[client_key] if stamp > cutoff]
        if len(bucket) >= limit:
            _rate_windows[client_key] = bucket
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="rate limit exceeded",
                headers={"Retry-After": str(window)},
            )
        bucket.append(now)
        _rate_windows[client_key] = bucket
        # Prevent unbounded growth if many client addresses are observed.
        if len(_rate_windows) > 4096:
            stale_keys = [key for key, stamps in _rate_windows.items() if not stamps or stamps[-1] <= cutoff]
            for key in stale_keys[:1024]:
                _rate_windows.pop(key, None)


def verify_clear_glass_request(
    request: Request,
    x_clear_glass_org: str | None = Header(default=None, alias="X-ClearGlass-Org"),
    x_clear_glass_api_key: str | None = Header(default=None, alias="X-ClearGlass-API-Key"),
) -> dict[str, str]:
    """Enforce ClearGlass-only service access and apply a local abuse guard."""

    allowed_orgs = _allowed_orgs()
    configured = _configured_keys()

    if not configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="agent service is not configured with CLEARGLASS_AGENT_API_KEYS",
        )

    if not x_clear_glass_org or x_clear_glass_org not in allowed_orgs:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ClearGlass authorization required")

    if not x_clear_glass_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing ClearGlass API key")

    enforce_rate_limit(request.client.host if request.client else "unknown")

    matched = any(hmac.compare_digest(x_clear_glass_api_key, candidate) for candidate in configured)
    if not matched:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid ClearGlass API key")

    return {
        "org": x_clear_glass_org,
        "key_fingerprint": _fingerprint(x_clear_glass_api_key),
        "client_host": request.client.host if request.client else "unknown",
    }

"""Security primitives — admin authentication and request throttling.

The governance model routes every high/critical action to the human approval
gate; this module protects that gate itself. Two primitives, no new
dependencies:

- ``require_admin`` — bearer-token auth for approval decisions. Fails closed:
  in production with no token configured, decisions are refused outright.
- ``rate_limit`` — in-process sliding-window throttle for abuse-prone
  endpoints (checkout, webhooks, approval decisions). Per-process only, which
  is sufficient for the single-instance Render/Docker deployments this repo
  targets; a shared store can replace the backend later without touching
  call sites.
"""
from __future__ import annotations

import hmac
import threading
import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import get_settings

# auto_error=False so we can return our own 401 detail (and allow dev mode).
_bearer = HTTPBearer(auto_error=False)


def require_admin(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """Authenticate an admin caller for approval decisions.

    Policy:
    - ``ADMIN_API_TOKEN`` set → require a matching bearer token (constant-time compare).
    - unset in production → 503; the gate must never silently run open in prod.
    - unset outside production → allow, so local demos and the test suite work
      with zero configuration.

    Returns the authenticated principal label used for audit context.
    """
    settings = get_settings()
    token = settings.admin_api_token
    if not token:
        if settings.app_env == "production":
            raise HTTPException(
                status_code=503,
                detail="approval gate not configured: set ADMIN_API_TOKEN",
            )
        return "dev-admin"
    if credentials is None or not hmac.compare_digest(credentials.credentials, token):
        raise HTTPException(status_code=401, detail="invalid or missing admin token")
    return "admin"


class SlidingWindowLimiter:
    """Thread-safe sliding-window counter keyed by caller identity."""

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int, window_seconds: float = 60.0) -> bool:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > window_seconds:
                hits.popleft()
            if len(hits) >= limit:
                return False
            hits.append(now)
            return True


_limiter = SlidingWindowLimiter()


def _client_key(request: Request, scope: str) -> str:
    client = request.client.host if request.client else "unknown"
    return f"{scope}:{client}"


def rate_limit(scope: str, setting_name: str):
    """Dependency factory: throttle ``scope`` at the per-minute limit named by
    ``setting_name`` on :class:`~app.config.Settings`. A limit of 0 disables
    the throttle for that scope."""

    def dependency(request: Request) -> None:
        limit = getattr(get_settings(), setting_name)
        if limit <= 0:
            return
        if not _limiter.allow(_client_key(request, scope), limit):
            raise HTTPException(status_code=429, detail=f"rate limit exceeded for {scope}")

    return dependency

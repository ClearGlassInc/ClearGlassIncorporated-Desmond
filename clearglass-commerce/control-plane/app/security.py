"""Admin authentication for governed / administrative endpoints.

The approval gate in :mod:`app.governance` is the heart of the safety model — but a
gate is only meaningful if not everyone can open it. Before this module, every
mutating admin endpoint (approve/reject, live pricing, refunds, catalog writes) was
reachable by anyone who could hit the API, and ``decided_by`` was a self-asserted
string. This closes that hole without changing the governance logic.

Behaviour mirrors the rest of the platform's fail-closed / mock-mode philosophy:

* **No key configured** → the API runs in *open* dev / mock mode (same spirit as
  running payments in mock mode with no Stripe key). Local dev and the test suite
  work unchanged.
* **``app_env == "production"`` with no key** → the app **fails closed at startup**
  (mirrors governance defaulting unknown actions to high risk). A production control
  plane must never boot wide open.
* **Key configured** → protected endpoints require ``Authorization: Bearer <key>``,
  compared in constant time. Multiple comma-separated keys are accepted so operators
  can rotate credentials without downtime.

The module is deliberately dependency-light (stdlib + fastapi) so it stays cheap to
test and reason about.
"""
from __future__ import annotations

import hmac
import logging
import threading
import time
from collections import defaultdict, deque

from fastapi import Depends, Header, HTTPException, Request, status

from .config import Settings, get_settings

logger = logging.getLogger("clearglass.security")

_BEARER_PREFIX = "bearer "


def _configured_keys(settings: Settings) -> list[str]:
    """Non-empty admin keys, split on commas and trimmed (supports rotation)."""
    return [k.strip() for k in settings.admin_api_key.split(",") if k.strip()]


def auth_enabled(settings: Settings | None = None) -> bool:
    """True when at least one admin key is configured (i.e. auth is enforced)."""
    settings = settings or get_settings()
    return bool(_configured_keys(settings))


def verify_startup_posture(settings: Settings | None = None) -> None:
    """Fail closed if a production deployment would boot without admin auth.

    Called once from the application factory. In non-production environments an
    unset key is allowed (open dev mode) but logged loudly so it is never a silent
    surprise.
    """
    settings = settings or get_settings()
    if auth_enabled(settings):
        return
    if settings.app_env.lower() in {"production", "prod"}:
        raise RuntimeError(
            "ADMIN_API_KEY is not set but APP_ENV is production. The commerce control "
            "plane refuses to start with an unauthenticated admin surface (approvals, "
            "pricing, refunds). Set ADMIN_API_KEY and redeploy."
        )
    logger.warning(
        "Admin authentication is DISABLED (no ADMIN_API_KEY set). This is acceptable for "
        "local/dev/mock use only — every mutating admin endpoint is open. Set ADMIN_API_KEY "
        "before exposing this service."
    )


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    if authorization[: len(_BEARER_PREFIX)].lower() == _BEARER_PREFIX:
        return authorization[len(_BEARER_PREFIX):].strip()
    return None


def require_admin(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> str:
    """FastAPI dependency guarding the administrative surface.

    Returns the authenticated principal (currently ``"admin"``; ``"dev-open"`` when auth
    is disabled) so callers can attribute audit entries to a real credential rather than
    a self-asserted request field.
    """
    keys = _configured_keys(settings)
    if not keys:
        # Open dev / mock mode. Startup posture (verify_startup_posture) already
        # guaranteed this cannot happen in production.
        return "dev-open"

    presented = _extract_bearer(authorization)
    if not presented:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="admin credentials required: send 'Authorization: Bearer <key>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Constant-time comparison against every configured key (no early exit / timing leak).
    if any(hmac.compare_digest(presented, key) for key in keys):
        return "admin"
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="invalid admin credentials",
    )


class SlidingWindowLimiter:
    """Thread-safe sliding-window request counter keyed by caller identity.

    In-process only, which matches the single-instance Render/Docker deployments this
    repo targets; a shared store (e.g. Redis) can replace the backend later without
    touching call sites.
    """

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


def rate_limit(scope: str, setting_name: str):
    """Dependency factory: throttle ``scope`` per client IP at the per-minute limit
    named by ``setting_name`` on :class:`~app.config.Settings`. A limit of 0 disables
    the throttle for that scope."""

    def dependency(request: Request) -> None:
        limit = getattr(get_settings(), setting_name)
        if limit <= 0:
            return
        client = request.client.host if request.client else "unknown"
        if not _limiter.allow(f"{scope}:{client}", limit):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"rate limit exceeded for {scope}",
            )

    return dependency

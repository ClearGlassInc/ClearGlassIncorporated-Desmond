"""Tests for admin authentication on the governed control-plane surface.

These verify the two things that make the approval gate trustworthy: production
cannot boot without auth, and — when auth is on — the guard rejects callers
without a valid bearer token while open mode stays permissive. The guard is
exercised directly (not via a live server) so the tests need no DB or web stack.
"""
from __future__ import annotations

import time

import pytest

from app.config import Settings
from app.security import auth_enabled, require_admin, verify_startup_posture


def _settings(**overrides) -> Settings:
    base = {"admin_api_key": "", "app_env": "development"}
    base.update(overrides)
    return Settings(**base)


# --- startup posture --------------------------------------------------------


def test_auth_disabled_by_default() -> None:
    assert auth_enabled(_settings()) is False


def test_auth_enabled_when_key_set() -> None:
    assert auth_enabled(_settings(admin_api_key="s3cret")) is True


def test_production_without_key_fails_closed() -> None:
    with pytest.raises(RuntimeError):
        verify_startup_posture(_settings(app_env="production"))


def test_production_with_key_boots() -> None:
    verify_startup_posture(_settings(app_env="production", admin_api_key="s3cret"))  # no raise


def test_dev_without_key_is_allowed() -> None:
    verify_startup_posture(_settings())  # no raise, warning only


# --- the guard dependency ---------------------------------------------------


def test_open_mode_returns_dev_principal() -> None:
    assert require_admin(authorization=None, settings=_settings()) == "dev-open"


def test_valid_bearer_is_accepted() -> None:
    s = _settings(admin_api_key="top-secret")
    assert require_admin(authorization="Bearer top-secret", settings=s) == "admin"


def test_valid_bearer_is_case_insensitive_scheme() -> None:
    s = _settings(admin_api_key="top-secret")
    assert require_admin(authorization="bearer top-secret", settings=s) == "admin"


def test_rotation_multiple_keys_accepted() -> None:
    s = _settings(admin_api_key="old-key, new-key")
    assert require_admin(authorization="Bearer new-key", settings=s) == "admin"
    assert require_admin(authorization="Bearer old-key", settings=s) == "admin"


def test_missing_credential_is_401() -> None:
    from fastapi import HTTPException

    s = _settings(admin_api_key="top-secret")
    with pytest.raises(HTTPException) as exc:
        require_admin(authorization=None, settings=s)
    assert exc.value.status_code == 401


def test_wrong_credential_is_403() -> None:
    from fastapi import HTTPException

    s = _settings(admin_api_key="top-secret")
    with pytest.raises(HTTPException) as exc:
        require_admin(authorization="Bearer nope", settings=s)
    assert exc.value.status_code == 403


def test_non_bearer_scheme_is_401() -> None:
    from fastapi import HTTPException

    s = _settings(admin_api_key="top-secret")
    with pytest.raises(HTTPException) as exc:
        require_admin(authorization="Basic abc123", settings=s)
    assert exc.value.status_code == 401


# --- rate limiter -----------------------------------------------------------


def test_limiter_enforces_the_window_limit() -> None:
    from app.security import SlidingWindowLimiter

    limiter = SlidingWindowLimiter()
    decisions = [limiter.allow("checkout:198.51.100.7", 3) for _ in range(5)]
    assert decisions == [True, True, True, False, False]


def test_limiter_allows_again_once_the_window_drains() -> None:
    from app.security import SlidingWindowLimiter

    limiter = SlidingWindowLimiter()
    assert limiter.allow("checkout:198.51.100.7", 1, window_seconds=0.01) is True
    assert limiter.allow("checkout:198.51.100.7", 1, window_seconds=0.01) is False
    time.sleep(0.02)
    assert limiter.allow("checkout:198.51.100.7", 1, window_seconds=0.01) is True


def test_limiter_does_not_grow_without_bound_across_callers() -> None:
    """Checkout/webhook throttles are keyed by client IP on public endpoints, so
    retaining a slot per IP that ever called would be an unbounded, stranger-driven
    leak in a long-running control plane. Drained keys must be reclaimed."""
    from app.security import SlidingWindowLimiter

    limiter = SlidingWindowLimiter(sweep_interval_seconds=0.01)

    for i in range(2000):
        limiter.allow(f"checkout:203.0.113.{i % 256}/{i}", 30, window_seconds=0.01)
    assert limiter.tracked_keys() > 1

    time.sleep(0.02)
    limiter.allow("checkout:198.51.100.7", 30)
    assert limiter.tracked_keys() == 1


def test_limiter_sweep_keeps_callers_inside_a_longer_window() -> None:
    """A sweep triggered by a short-window scope must not evict a long-window one."""
    from app.security import SlidingWindowLimiter

    limiter = SlidingWindowLimiter()
    assert limiter.allow("slow:198.51.100.7", 5, window_seconds=3600) is True

    limiter._next_sweep = time.monotonic() - 1  # force a sweep on the next call
    limiter.allow("fast:203.0.113.9", 5, window_seconds=0.001)

    assert limiter.tracked_keys() == 2

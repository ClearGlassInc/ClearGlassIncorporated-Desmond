"""Tests for admin authentication on the governed control-plane surface.

These verify the two things that make the approval gate trustworthy: production
cannot boot without auth, and — when auth is on — the guard rejects callers
without a valid bearer token while open mode stays permissive. The guard is
exercised directly (not via a live server) so the tests need no DB or web stack.
"""
from __future__ import annotations

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

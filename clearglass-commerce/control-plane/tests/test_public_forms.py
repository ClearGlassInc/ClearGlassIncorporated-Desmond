from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.routers.public_forms import PublicFormSubmission
from app.security import verify_startup_posture


def test_public_form_normalizes_and_bounds_fields() -> None:
    submission = PublicFormSubmission(
        kind="hardening-sprint",
        email=" Person@Example.COM ",
        name=" Person ",
        message=" help ",
        consent=True,
    )
    assert submission.email == "person@example.com"
    assert submission.name == "Person"
    assert submission.message == "help"


def test_public_form_rejects_invalid_email_or_unknown_kind() -> None:
    with pytest.raises(ValidationError):
        PublicFormSubmission(kind="hardening-sprint", email="not-an-email", consent=True)
    with pytest.raises(ValidationError):
        PublicFormSubmission(kind="other", email="person@example.com", consent=True)


def test_enabled_forms_require_protected_origin_and_allowlisted_https_relay() -> None:
    base = {
        "app_env": "development",
        "admin_api_key": "configured",
        "public_forms_enabled": True,
        "public_form_relay_url": "https://relay.example.test/forms",
        "public_form_relay_allowed_hosts": "relay.example.test",
    }
    with pytest.raises(RuntimeError, match="EDGE_ORIGIN_AUTH_REQUIRED"):
        verify_startup_posture(Settings(**base))

    protected = {
        **base,
        "edge_origin_auth_required": True,
        "edge_origin_auth_secrets": "s" * 40,
    }
    verify_startup_posture(Settings(**protected))
    unapproved = {**protected, "public_form_relay_url": "https://unapproved.example/forms"}
    with pytest.raises(RuntimeError, match="explicitly listed"):
        verify_startup_posture(Settings(**unapproved))

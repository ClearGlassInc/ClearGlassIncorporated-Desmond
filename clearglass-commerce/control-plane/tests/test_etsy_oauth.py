"""Tests for the Etsy OAuth2 (PKCE) handshake — offline, no network, no real credentials.

Covers PKCE generation, the consent URL, the code exchange and refresh (both via an
injected poster), failure reporting, and the CLI's redirect-URL parsing.
"""
from __future__ import annotations

import base64
import hashlib
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest

from app import etsy_connect, etsy_oauth
from app.config import Settings
from app.etsy import REQUIRED_SCOPES


def _settings(**over) -> Settings:
    base = {
        "etsy_keystring": "key123",
        "etsy_redirect_uri": "https://www.clearglassinc.com/etsy/callback",
    }
    base.update(over)
    return Settings(**base)


def _fake_post(status: int, body: dict):
    calls: list[tuple[str, dict]] = []

    def post(url: str, payload: dict) -> tuple[int, dict]:
        calls.append((url, payload))
        return status, body

    return post, calls


# --- PKCE ------------------------------------------------------------------------

def test_pkce_pair_is_fresh_and_correctly_derived() -> None:
    verifier, challenge = etsy_oauth.generate_pkce()
    expected = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).decode("ascii").rstrip("=")
    assert challenge == expected
    assert "=" not in verifier and "=" not in challenge   # base64url, unpadded
    assert etsy_oauth.generate_pkce()[0] != verifier      # never reused


# --- authorize URL ----------------------------------------------------------------

def test_authorize_url_carries_scopes_challenge_and_state() -> None:
    url = etsy_oauth.build_authorize_url(
        _settings(), code_challenge="chal", state="st4te", scopes=REQUIRED_SCOPES
    )
    assert url.startswith("https://www.etsy.com/oauth/connect?")
    assert "client_id=key123" in url
    assert "code_challenge=chal" in url
    assert "code_challenge_method=S256" in url
    assert "state=st4te" in url
    assert "response_type=code" in url
    # scopes are space-delimited for Etsy, so they urlencode as +
    assert "scope=listings_r+listings_w+transactions_r+transactions_w" in url


def test_authorize_url_requires_keystring_and_redirect() -> None:
    with pytest.raises(etsy_oauth.EtsyOAuthError, match="etsy_keystring"):
        etsy_oauth.build_authorize_url(
            Settings(etsy_redirect_uri="https://x/cb"), code_challenge="c", state="s"
        )
    with pytest.raises(etsy_oauth.EtsyOAuthError, match="etsy_redirect_uri"):
        etsy_oauth.build_authorize_url(
            Settings(etsy_keystring="k"), code_challenge="c", state="s"
        )


# --- code exchange ----------------------------------------------------------------

def test_exchange_code_returns_tokens_and_sends_pkce_verifier() -> None:
    post, calls = _fake_post(200, {
        "access_token": "42.acc3ss",
        "refresh_token": "42.r3fresh",
        "expires_in": 3600,
    })
    tokens = etsy_oauth.exchange_code("thecode", "theverifier", _settings(), post=post)

    assert tokens["access_token"] == "42.acc3ss"
    assert tokens["refresh_token"] == "42.r3fresh"
    assert tokens["user_id"] == "42"          # parsed from the token prefix

    url, payload = calls[0]
    assert url == "https://api.etsy.com/v3/public/oauth/token"
    assert payload["grant_type"] == "authorization_code"
    assert payload["code_verifier"] == "theverifier"
    assert payload["client_id"] == "key123"
    # PKCE is a public-client flow: the app's shared secret is never transmitted
    assert "client_secret" not in payload
    assert "etsy_shared_secret" not in payload


def test_exchange_failure_surfaces_etsy_error_text() -> None:
    post, _ = _fake_post(400, {"error": "invalid_grant", "error_description": "code expired"})
    with pytest.raises(etsy_oauth.EtsyOAuthError, match="code expired"):
        etsy_oauth.exchange_code("stale", "v", _settings(), post=post)


def test_exchange_rejects_200_without_a_token() -> None:
    post, _ = _fake_post(200, {"nope": True})
    with pytest.raises(etsy_oauth.EtsyOAuthError):
        etsy_oauth.exchange_code("c", "v", _settings(), post=post)


# --- refresh ----------------------------------------------------------------------

def test_refresh_uses_stored_token_when_none_passed() -> None:
    post, calls = _fake_post(200, {"access_token": "42.new", "refresh_token": "42.r2"})
    tokens = etsy_oauth.refresh_access_token(
        settings=_settings(etsy_refresh_token="42.stored"), post=post
    )
    assert tokens["access_token"] == "42.new"
    assert calls[0][1]["grant_type"] == "refresh_token"
    assert calls[0][1]["refresh_token"] == "42.stored"


def test_refresh_without_any_token_explains_the_remedy() -> None:
    with pytest.raises(etsy_oauth.EtsyOAuthError, match="etsy_connect"):
        etsy_oauth.refresh_access_token(settings=_settings(), post=lambda u, b: (200, {}))


# --- env rendering ----------------------------------------------------------------

def test_env_exports_lists_what_the_control_plane_reads() -> None:
    out = etsy_oauth.env_exports({"access_token": "42.a", "refresh_token": "42.r", "user_id": "42"})
    assert "ETSY_ACCESS_TOKEN=42.a" in out
    assert "ETSY_REFRESH_TOKEN=42.r" in out
    assert "ETSY_SCOPES=" + ",".join(REQUIRED_SCOPES) in out


# --- CLI input handling -----------------------------------------------------------

def test_code_accepted_bare_or_as_full_redirect_url() -> None:
    assert etsy_connect._code_from_input("  rawcode  ") == "rawcode"
    assert etsy_connect._code_from_input(
        "https://www.clearglassinc.com/etsy/callback?code=abc123&state=xyz"
    ) == "abc123"


def test_redirect_url_error_and_missing_code_are_reported() -> None:
    with pytest.raises(etsy_oauth.EtsyOAuthError, match="access_denied"):
        etsy_connect._code_from_input("https://cb/?error=access_denied")
    with pytest.raises(etsy_oauth.EtsyOAuthError, match="no .code="):
        etsy_connect._code_from_input("https://cb/?state=xyz")


def test_cli_exchange_requires_both_code_and_verifier() -> None:
    with pytest.raises(SystemExit):
        etsy_connect.main(["--exchange", "--code", "abc"])

from __future__ import annotations

import os

os.environ["CLEARGLASS_AGENT_API_KEYS"] = "test-key"
os.environ["CLEARGLASS_ALLOWED_ORIGINS"] = "https://www.clearglassinc.com"
os.environ["CLEARGLASS_AGENT_RATE_LIMIT"] = "2"
os.environ["CLEARGLASS_AGENT_RATE_WINDOW_SECONDS"] = "60"

from fastapi.testclient import TestClient

from .main import app


client = TestClient(app)
AUTH = {"X-ClearGlass-Org": "ClearGlassInc", "X-ClearGlass-API-Key": "test-key"}


def test_health_is_public_and_has_security_headers() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_policy_requires_authentication() -> None:
    response = client.get("/policy")
    assert response.status_code == 401


def test_policy_accepts_valid_clear_glass_credentials() -> None:
    response = client.get("/policy", headers=AUTH)
    assert response.status_code == 200
    assert response.json()["owner"] == "ClearGlassInc"


def test_signal_rejects_private_targeting_language() -> None:
    response = client.post(
        "/v1/signal",
        headers=AUTH,
        json={"target": "track person private messages", "mission": "risk_brief", "domain": "web"},
    )
    assert response.status_code == 422


def test_rate_limit_is_enforced() -> None:
    assert client.get("/policy", headers=AUTH).status_code == 200
    assert client.get("/policy", headers=AUTH).status_code == 200
    assert client.get("/policy", headers=AUTH).status_code == 429

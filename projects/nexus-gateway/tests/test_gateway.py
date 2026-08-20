import hashlib
import os

os.environ["NEXUS_DEV_AUTH_ENABLED"] = "true"
os.environ["NEXUS_ENVIRONMENT"] = "test"

from fastapi.testclient import TestClient

from app.main import app

HEADERS = {"Authorization": "Bearer dev-operator"}
OBJECTIVE = hashlib.sha256(b"authorized diagnostic objective").hexdigest()


def test_health_without_auth():
    with TestClient(app) as client:
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_sitrep_requires_auth():
    with TestClient(app) as client:
        assert client.get("/api/v1/sitrep").status_code == 401
        assert client.get("/api/v1/sitrep", headers=HEADERS).status_code == 200


def test_unauthorized_tool_is_denied():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/agent/execute",
            headers=HEADERS,
            json={
                "agent_id": "sentinel-01",
                "target_tool": "raw_shell",
                "payload": {},
                "objective_hash": OBJECTIVE,
            },
        )
        assert response.status_code == 403
        assert "POLICY DENY" in response.json()["detail"]


def test_network_mutation_is_denied():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/agent/execute",
            headers=HEADERS,
            json={
                "agent_id": "sentinel-01",
                "target_tool": "network_optimizer",
                "payload": {"mode": "Optimize", "diagnostic_only": False},
                "objective_hash": OBJECTIVE,
            },
        )
        assert response.status_code == 403


def test_authorized_tool_is_validated_not_executed():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/agent/execute",
            headers=HEADERS,
            json={
                "agent_id": "sentinel-01",
                "target_tool": "network_optimizer",
                "payload": {"mode": "Diagnose", "diagnostic_only": True, "duration_seconds": 60},
                "objective_hash": OBJECTIVE,
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "validated"


def test_aegis_execution_fails_closed_by_default():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/aegis/dispatch",
            headers=HEADERS,
            json={"mode": "Audit", "scan_minutes": 15, "generate_report": True},
        )
        assert response.status_code == 503

"""Tests for the deployable FastAPI surface.

Skipped when FastAPI isn't installed; the `dev`/`server` extras install it, and
the Agent SDK CI workflow installs those so these always run in CI.
"""

import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

# E402 is expected here: the importorskip calls above must run before these
# imports, or a machine without FastAPI fails at import instead of skipping.
# Same convention as tests/test_opal_security.py and test_generate_favicons.py.
from fastapi.testclient import TestClient  # noqa: E402

from clearglassinc_sdk.agent import Agent  # noqa: E402
from clearglassinc_sdk.guardrails import RequiredKeywordsGuardrail  # noqa: E402
from clearglassinc_sdk.server import create_app  # noqa: E402
from clearglassinc_sdk.sessions import InMemorySessionStore  # noqa: E402
from clearglassinc_sdk.testing import FakeLLMClient, text_response  # noqa: E402
from clearglassinc_sdk.tracing import Usage  # noqa: E402


def build_client(monkeypatch, *, api_key=None, agents=None, responses=None, store=None):
    monkeypatch.delenv("CLEARGLASS_ENV", raising=False)
    if api_key:
        monkeypatch.setenv("CLEARGLASS_API_KEY", api_key)
    else:
        monkeypatch.delenv("CLEARGLASS_API_KEY", raising=False)

    app = create_app(
        agents=agents or {"default": Agent(name="Test", instructions="Be helpful.")},
        llm_client=FakeLLMClient(
            responses=responses
            or [text_response("hello back", usage=Usage(input_tokens=10, output_tokens=3))]
        ),
        session_store=store or InMemorySessionStore(),
    )
    return TestClient(app)


def test_health_is_open_and_reports_version(monkeypatch):
    client = build_client(monkeypatch)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"]


def test_ready_reports_provider_and_agents(monkeypatch):
    client = build_client(monkeypatch)
    body = client.get("/ready").json()
    assert body["status"] == "ready"
    assert body["agents"] == ["default"]


def test_run_returns_output_steps_and_usage(monkeypatch):
    client = build_client(monkeypatch)
    response = client.post("/run", json={"prompt": "hello"})

    assert response.status_code == 200
    body = response.json()
    assert body["output"] == "hello back"
    assert body["steps"] == 1
    assert body["usage"]["total_tokens"] == 13
    assert body["trace_id"]


def test_run_rejects_empty_prompt(monkeypatch):
    client = build_client(monkeypatch)
    assert client.post("/run", json={"prompt": ""}).status_code == 422


def test_run_returns_404_for_unknown_agent(monkeypatch):
    client = build_client(monkeypatch)
    response = client.post("/run", json={"prompt": "hi", "agent": "nope"})
    assert response.status_code == 404


def test_guardrail_violation_maps_to_422(monkeypatch):
    agent = Agent(name="Test", instructions="Be helpful.")
    agent.input_guardrails = [RequiredKeywordsGuardrail(keywords=["allowed"])]
    client = build_client(monkeypatch, agents={"default": agent})

    response = client.post("/run", json={"prompt": "forbidden topic"})
    assert response.status_code == 422


def test_auth_required_when_api_key_is_set(monkeypatch):
    client = build_client(monkeypatch, api_key="secret-key")

    assert client.post("/run", json={"prompt": "hi"}).status_code == 401
    assert client.post("/run", json={"prompt": "hi"}, headers={"Authorization": "Bearer wrong"}).status_code == 401

    ok = client.post("/run", json={"prompt": "hi"}, headers={"Authorization": "Bearer secret-key"})
    assert ok.status_code == 200


def test_health_stays_open_even_with_auth_configured(monkeypatch):
    client = build_client(monkeypatch, api_key="secret-key")
    assert client.get("/health").status_code == 200


def test_production_without_api_key_fails_closed(monkeypatch):
    monkeypatch.setenv("CLEARGLASS_ENV", "production")
    monkeypatch.delenv("CLEARGLASS_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="CLEARGLASS_API_KEY"):
        create_app(llm_client=FakeLLMClient())


def test_production_with_api_key_starts(monkeypatch):
    monkeypatch.setenv("CLEARGLASS_ENV", "production")
    monkeypatch.setenv("CLEARGLASS_API_KEY", "k")
    assert create_app(llm_client=FakeLLMClient()) is not None


def test_session_roundtrip_through_the_api(monkeypatch):
    store = InMemorySessionStore()
    client = build_client(
        monkeypatch,
        store=store,
        responses=[text_response("noted"), text_response("recalled")],
    )

    client.post("/run", json={"prompt": "remember this", "session_id": "s1"})
    assert client.get("/sessions").json()["sessions"] == ["s1"]

    client.post("/run", json={"prompt": "what did I say?", "session_id": "s1"})
    stored = [message.content for message in store.load("s1")]
    assert "remember this" in stored

    assert client.delete("/sessions/s1").status_code == 200
    assert client.get("/sessions").json()["sessions"] == []


def test_stream_endpoint_emits_sse_events(monkeypatch):
    client = build_client(monkeypatch, responses=[text_response("streamed answer")])

    with client.stream("POST", "/run/stream", json={"prompt": "hi"}) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = "".join(response.iter_text())

    assert "streamed answer" in body
    assert '"done": true' in body


def test_traces_endpoint_exposes_recorded_spans(monkeypatch):
    client = build_client(monkeypatch)
    client.post("/run", json={"prompt": "hi"})

    spans = client.get("/traces").json()["spans"]
    assert spans
    assert {span["kind"] for span in spans} & {"run", "llm", "step"}

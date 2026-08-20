"""Deployable HTTP surface for the SDK: a FastAPI app that serves agent runs.

Endpoints
    GET  /health         liveness — always 200 if the process is up
    GET  /ready          readiness — reports whether a provider is configured
    POST /run            run an agent turn, return the final answer
    POST /run/stream     same, streamed as Server-Sent Events
    GET  /sessions       list persisted session ids
    DELETE /sessions/{id} drop a persisted session

Requires the `server` extra (`pip install clearglassinc-sdk[server]`).

Auth: set `CLEARGLASS_API_KEY` and callers must send
`Authorization: Bearer <key>`. Unset means open (local dev only) — with
`CLEARGLASS_ENV=production` and no key the app refuses to start, so a
production deploy can't accidentally come up unauthenticated.
"""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from typing import Any

from clearglassinc_sdk import __version__
from clearglassinc_sdk.agent import Agent
from clearglassinc_sdk.clients.base import LLMClient
from clearglassinc_sdk.exceptions import GuardrailViolation, MaxStepsExceeded, ToolExecutionError
from clearglassinc_sdk.runner import Runner
from clearglassinc_sdk.sessions import FileSessionStore, SessionStore
from clearglassinc_sdk.structured import OutputValidationError
from clearglassinc_sdk.tracing import InMemoryExporter, Tracer

try:
    from fastapi import Depends, FastAPI, Header, HTTPException
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "The server requires FastAPI: pip install clearglassinc-sdk[server]"
    ) from exc


class RunRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=100_000)
    session_id: str | None = None
    agent: str | None = None


class RunResponse(BaseModel):
    output: str
    steps: int
    trace_id: str
    session_id: str | None = None
    structured_output: Any = None
    usage: dict[str, int]


def build_client() -> LLMClient:
    """Pick a provider from the environment. Defaults to an offline fake so
    the container is runnable (and smoke-testable) with no API key."""
    provider = os.environ.get("CLEARGLASS_PROVIDER", "fake").lower()
    model = os.environ.get("CLEARGLASS_MODEL")

    if provider == "openai":
        from clearglassinc_sdk.clients.openai_client import OpenAIClient

        return OpenAIClient(model=model or "gpt-4o-mini")
    if provider == "anthropic":
        from clearglassinc_sdk.clients.anthropic_client import AnthropicClient

        return AnthropicClient(model=model or "claude-sonnet-5")

    from clearglassinc_sdk.testing import FakeLLMClient

    return FakeLLMClient()


def default_agent() -> Agent:
    return Agent(
        name=os.environ.get("CLEARGLASS_AGENT_NAME", "ClearGlassInc Agent"),
        instructions=os.environ.get(
            "CLEARGLASS_AGENT_INSTRUCTIONS",
            "You are a high-performance, futuristic automation agent.",
        ),
        model=os.environ.get("CLEARGLASS_MODEL"),
    )


def create_app(
    agents: dict[str, Agent] | None = None,
    llm_client: LLMClient | None = None,
    session_store: SessionStore | None = None,
) -> FastAPI:
    """Build the FastAPI app. Injectable for tests; env-driven in production."""
    api_key = os.environ.get("CLEARGLASS_API_KEY")
    if os.environ.get("CLEARGLASS_ENV", "").lower() == "production" and not api_key:
        raise RuntimeError(
            "CLEARGLASS_ENV=production requires CLEARGLASS_API_KEY to be set "
            "(refusing to start an unauthenticated production server)"
        )

    registry: dict[str, Agent] = agents or {"default": default_agent()}
    client = llm_client or build_client()
    store = session_store or FileSessionStore(
        directory=os.environ.get("CLEARGLASS_SESSION_DIR", "/tmp/clearglass-sessions")
    )
    trace_exporter = InMemoryExporter()

    app = FastAPI(title="ClearGlassInc Agent SDK", version=__version__)

    def require_auth(authorization: str | None = Header(default=None)) -> None:
        """Bearer-token gate. A no-op when no key is configured (dev mode)."""
        if not api_key:
            return
        expected = f"Bearer {api_key}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="invalid or missing bearer token")

    def resolve_agent(name: str | None) -> Agent:
        agent = registry.get(name or "default")
        if agent is None:
            raise HTTPException(status_code=404, detail=f"no agent named '{name}'")
        return agent

    def build_runner(agent: Agent, session_id: str | None) -> Runner:
        return Runner(
            agent,
            client,
            tracer=Tracer(exporters=[trace_exporter]),
            session_store=store if session_id else None,
            session_id=session_id,
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/ready")
    def ready() -> dict[str, Any]:
        provider = os.environ.get("CLEARGLASS_PROVIDER", "fake").lower()
        configured = provider == "fake" or bool(
            os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        )
        return {
            "status": "ready" if configured else "degraded",
            "provider": provider,
            "authenticated": bool(api_key),
            "agents": sorted(registry),
        }

    @app.post("/run", response_model=RunResponse, dependencies=[Depends(require_auth)])
    def run(request: RunRequest) -> RunResponse:
        agent = resolve_agent(request.agent)
        runner = build_runner(agent, request.session_id)
        try:
            result = runner.run(request.prompt)
        except GuardrailViolation as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except OutputValidationError as exc:
            raise HTTPException(status_code=422, detail=f"schema violation: {exc}") from exc
        except MaxStepsExceeded as exc:
            raise HTTPException(status_code=504, detail=str(exc)) from exc
        except ToolExecutionError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        return RunResponse(
            output=result.output,
            steps=result.steps,
            trace_id=result.trace_id,
            session_id=request.session_id,
            structured_output=result.structured_output,
            usage=result.usage.to_dict(),
        )

    @app.post("/run/stream", dependencies=[Depends(require_auth)])
    async def run_stream(request: RunRequest) -> StreamingResponse:
        agent = resolve_agent(request.agent)
        runner = build_runner(agent, request.session_id)

        async def event_source() -> AsyncIterator[str]:
            try:
                for chunk in runner.run_stream(request.prompt):
                    if chunk.delta:
                        yield f"data: {json.dumps({'delta': chunk.delta})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
            except (GuardrailViolation, OutputValidationError, MaxStepsExceeded) as exc:
                yield f"data: {json.dumps({'error': str(exc)})}\n\n"

        return StreamingResponse(
            event_source(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/sessions", dependencies=[Depends(require_auth)])
    def list_sessions() -> dict[str, list[str]]:
        return {"sessions": store.list_sessions()}

    @app.delete("/sessions/{session_id}", dependencies=[Depends(require_auth)])
    def delete_session(session_id: str) -> dict[str, str]:
        store.delete(session_id)
        return {"status": "deleted", "session_id": session_id}

    @app.get("/traces", dependencies=[Depends(require_auth)])
    def traces(limit: int = 50) -> dict[str, list[dict[str, Any]]]:
        spans = [span.to_dict() for span in trace_exporter.spans[-limit:]]
        return {"spans": spans}

    return app


def main() -> None:  # pragma: no cover - process entrypoint
    import uvicorn

    uvicorn.run(
        create_app(),
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
    )


if __name__ == "__main__":  # pragma: no cover
    main()

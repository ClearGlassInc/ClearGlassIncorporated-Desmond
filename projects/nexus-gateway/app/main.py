import time
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .aegis_bridge import AegisUnavailable, dispatch_aegis
from .auth import verify_managed_identity
from .config import Settings, get_settings
from .governance import evaluate_action
from .models import AegisDispatchRequest, AIActionRequest, Principal, TelemetryEvent
from .telemetry import TelemetryBus

settings = get_settings()
telemetry = TelemetryBus(settings.telemetry_queue_size, settings.telemetry_history_size)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await telemetry.start()
    yield
    await telemetry.stop()


app = FastAPI(
    title=settings.service_name,
    description="Zero-trust identity brokering, deterministic AI tool governance, AEGIS dispatch, and asynchronous telemetry.",
    version=settings.version,
    lifespan=lifespan,
)


@app.middleware("http")
async def security_interceptor(request: Request, call_next):
    start = time.perf_counter()
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-ClearGlass-Process-Time-Ms"] = f"{(time.perf_counter() - start) * 1000:.3f}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/api/") else response.headers.get("Cache-Control", "no-cache")
    return response


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/console/")


@app.get("/healthz", tags=["Platform"])
async def healthz():
    return {"status": "ok", "service": settings.service_name, "version": settings.version}


@app.get("/readyz", tags=["Platform"])
async def readyz():
    auth_ready = settings.dev_auth_enabled or bool(settings.entra_tenant_id and settings.entra_audience)
    return {
        "status": "ready" if auth_ready else "degraded",
        "identity_broker_configured": auth_ready,
        "aegis_execution_enabled": settings.aegis_execution_enabled,
    }


@app.get("/api/v1/sitrep", tags=["Operations"])
async def get_live_sitrep(operator: Principal = Depends(verify_managed_identity)):
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "operator": operator.display_name,
        "system_status": "GUARDED",
        "active_feeds": 1,
        "telemetry": {
            "queued": telemetry.queue.qsize(),
            "accepted": telemetry.accepted,
            "dropped": telemetry.dropped,
            "history": len(telemetry.history),
        },
        "authorized_tools": sorted(settings.tool_allowlist),
    }


@app.post("/api/v1/agent/execute", tags=["AI Governance"])
async def execute_agent_action(
    action: AIActionRequest,
    request: Request,
    operator: Principal = Depends(verify_managed_identity),
):
    decision = evaluate_action(action, settings)
    await telemetry.publish(
        TelemetryEvent(
            source="nexus-governance",
            event_type="agent_action_decision",
            severity="info" if decision.allowed else "high",
            details={
                "agent_id": action.agent_id,
                "target_tool": action.target_tool,
                "objective_hash": action.objective_hash,
                "allowed": decision.allowed,
                "reason": decision.reason,
                "operator": operator.subject,
            },
        ),
        request.state.request_id,
    )
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"AGENT POLICY DENY: {decision.reason}")

    return {
        "status": "validated",
        "target_tool": action.target_tool,
        "audit_id": request.state.request_id,
        "objective_hash": action.objective_hash,
        "message": "Tool request passed gateway policy. Execution remains delegated to the authorized downstream tool runner.",
    }


@app.post("/api/v1/telemetry", status_code=status.HTTP_202_ACCEPTED, tags=["Telemetry"])
async def ingest_telemetry(
    event: TelemetryEvent,
    request: Request,
    _: Principal = Depends(verify_managed_identity),
):
    accepted = await telemetry.publish(event, request.state.request_id)
    if not accepted:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telemetry buffer is full.")
    return {"status": "accepted", "request_id": request.state.request_id}


@app.get("/api/v1/telemetry/recent", tags=["Telemetry"])
async def recent_telemetry(limit: int = 25, _: Principal = Depends(verify_managed_identity)):
    return {"events": telemetry.snapshot(max(1, min(limit, 100)))}


@app.post("/api/v1/aegis/dispatch", tags=["AEGIS"])
async def aegis_dispatch(
    dispatch: AegisDispatchRequest,
    request: Request,
    operator: Principal = Depends(verify_managed_identity),
):
    try:
        result = await dispatch_aegis(dispatch, settings)
    except AegisUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    await telemetry.publish(
        TelemetryEvent(
            source="aegis-bridge",
            event_type="aegis_dispatch",
            severity="info" if result.return_code == 0 else "high",
            details={"mode": dispatch.mode, "return_code": result.return_code, "operator": operator.subject},
        ),
        request.state.request_id,
    )
    return {
        "status": "completed" if result.return_code == 0 else "failed",
        "return_code": result.return_code,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "audit_id": request.state.request_id,
    }


web_root = Path(__file__).resolve().parents[1] / "web"
if web_root.is_dir():
    app.mount("/console", StaticFiles(directory=web_root, html=True), name="console")

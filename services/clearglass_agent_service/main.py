from __future__ import annotations

import os

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .agent import build_report, root_policy
from .schemas import AgentReport, HealthResponse, SignalPacket
from .security import verify_clear_glass_request

VERSION = os.getenv("CLEARGLASS_AGENT_VERSION", "0.2.0")
MAX_REQUEST_BODY_BYTES = int(os.getenv("CLEARGLASS_MAX_REQUEST_BYTES", "262144"))


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.headers.get("content-length"):
            try:
                if int(request.headers["content-length"]) > MAX_REQUEST_BODY_BYTES:
                    return Response("request body too large", status_code=413)
            except ValueError:
                return Response("invalid content-length", status_code=400)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        return response


app = FastAPI(
    title="ClearGlass Agent Service",
    version=VERSION,
    description="ClearGlassInc-only lawful public-source and defensive risk-intelligence agent service.",
    docs_url=None if os.getenv("CLEARGLASS_DISABLE_DOCS", "false").lower() == "true" else "/docs",
    redoc_url=None if os.getenv("CLEARGLASS_DISABLE_DOCS", "false").lower() == "true" else "/redoc",
)

allowed_hosts = [host.strip() for host in os.getenv("CLEARGLASS_ALLOWED_HOSTS", "").split(",") if host.strip()]
if allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

app.add_middleware(SecurityHeadersMiddleware)

allowed_origins = [origin.strip() for origin in os.getenv("CLEARGLASS_ALLOWED_ORIGINS", "").split(",") if origin.strip()]
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["X-ClearGlass-Org", "X-ClearGlass-API-Key", "Content-Type"],
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(version=VERSION)


@app.get("/policy")
def policy(_: dict[str, str] = Depends(verify_clear_glass_request)) -> dict[str, object]:
    return root_policy()


@app.post("/v1/signal", response_model=AgentReport)
def signal_report(
    packet: SignalPacket,
    request: Request,
    principal: dict[str, str] = Depends(verify_clear_glass_request),
) -> AgentReport:
    del request
    return build_report(packet, principal)

"""FastAPI application factory for the commerce control plane."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config import get_settings
from .routers import approvals, events, inventory, metrics, orders, payments, store


def create_app() -> FastAPI:
    settings = get_settings()
    if settings.auto_create_tables:
        from .db import engine
        from .models import Base

        Base.metadata.create_all(engine)
    app = FastAPI(
        title="ClearGlass Autonomous E-Commerce Operator",
        version=__version__,
        description=(
            "Governed commerce control plane. Read-only analysis -> draft -> approval -> "
            "execution. Every material change is risk-scored and written to an append-only ledger."
        ),
    )

    origins = [o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if settings.app_env == "production":
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
            )
        return response

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        """Liveness: the process is up. Makes no external calls."""
        return {"status": "ok", "env": settings.app_env, "version": __version__}

    @app.get("/ready", tags=["meta"])
    def ready() -> dict:
        """Readiness: the service can reach its database. Use for orchestrator checks."""
        from sqlalchemy import text

        from .db import engine

        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as exc:  # pragma: no cover - exercised via fault injection
            raise HTTPException(status_code=503, detail=f"database unavailable: {type(exc).__name__}")
        return {"status": "ready", "database": "ok", "version": __version__}

    @app.get("/", tags=["meta"])
    def root() -> dict:
        return {
            "service": settings.app_name,
            "docs": "/docs",
            "governance": "high/critical actions require human approval",
        }

    app.include_router(store.router)
    app.include_router(payments.router)
    app.include_router(orders.router)
    app.include_router(inventory.router)
    app.include_router(metrics.router)
    app.include_router(events.router)
    app.include_router(approvals.router)
    return app


app = create_app()


def main() -> None:
    """Console entry point: ``python -m app.main`` (dev convenience)."""
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()

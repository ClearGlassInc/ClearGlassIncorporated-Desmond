"""FastAPI application factory for the commerce control plane."""
from __future__ import annotations

from fastapi import FastAPI
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

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok", "env": settings.app_env, "version": __version__}

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

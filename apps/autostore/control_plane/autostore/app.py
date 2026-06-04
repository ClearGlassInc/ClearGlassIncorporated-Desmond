"""FastAPI surface for the PERCIVAL Autostore control plane.

Thin adapter — all decisioning lives in autostore.policy / engine. The same
in-memory Store used by tests powers the demo; a Postgres-backed Store can be
dropped in without changing the engine.
"""
from __future__ import annotations

from typing import Any

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
except ImportError as exc:  # pragma: no cover
    raise ImportError("autostore.app requires fastapi + pydantic") from exc

from .engine import Engine
from .models import EventType, Product
from .store import InMemoryStore

app = FastAPI(title="PERCIVAL Autostore — Control Plane", version="0.1.0")

_store = InMemoryStore()
_store.seed_product(Product("SKU-RIDGE-01", "Ridge Hoodie",
                            price_cents=8900, cost_cents=3200,
                            min_price_cents=4500, inventory=120))
_store.seed_product(Product("SKU-VAULT-02", "Vault Backpack",
                            price_cents=14900, cost_cents=6100,
                            min_price_cents=7500, inventory=42))
_engine = Engine(_store)


class EventIn(BaseModel):
    type: str
    payload: dict[str, Any]


class ApprovalIn(BaseModel):
    approver: str


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "audit_intact": _engine.ledger.verify()}


@app.post("/v1/events")
def post_event(ev: EventIn) -> dict:
    try:
        kind = EventType(ev.type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"unknown event type: {ev.type}") from exc
    result, entry = _engine.handle(kind, ev.payload)
    return {
        "decision": result.decision.value,
        "action": result.action,
        "reasons": list(result.reasons),
        "executed": entry.executed,
        "audit_ref": result.audit_ref,
        "entry_id": entry.id,
    }


@app.get("/v1/approvals/pending")
def list_pending() -> list[dict]:
    return [{
        "id": p.id, "event_id": p.event.id, "event_type": p.event.type.value,
        "payload": p.event.payload, "action": p.result.action,
        "reasons": list(p.result.reasons), "audit_ref": p.audit_ref,
    } for p in _engine.pending]


@app.post("/v1/approvals/{pending_id}/approve")
def approve(pending_id: int, body: ApprovalIn) -> dict:
    try:
        entry = _engine.approve(pending_id, body.approver)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"audit_ref": entry.audit_ref, "executed": entry.executed,
            "decision": entry.decision.value}


@app.post("/v1/approvals/{pending_id}/deny")
def deny(pending_id: int, body: ApprovalIn) -> dict:
    try:
        entry = _engine.deny(pending_id, body.approver)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"audit_ref": entry.audit_ref, "decision": entry.decision.value}


@app.get("/v1/audit")
def audit(limit: int = 100) -> list[dict]:
    return _engine.ledger.snapshot()[-int(limit):]


@app.get("/v1/products/{sku}")
def product(sku: str) -> dict:
    p = _store.get_product(sku)
    if not p:
        raise HTTPException(status_code=404, detail="unknown sku")
    return {"sku": p.sku, "title": p.title, "price_cents": p.price_cents,
            "min_price_cents": p.min_price_cents, "inventory": p.inventory}

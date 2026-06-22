"""FastAPI surface for the PERCIVAL Autostore control plane.

Thin adapter — all decisioning lives in autostore.policy / engine. The same
in-memory Store used by tests powers the demo; a Postgres-backed Store can be
dropped in without changing the engine.
"""
from __future__ import annotations

import os
from typing import Any, Optional

try:
    from fastapi import Depends, FastAPI, Header, HTTPException
    from pydantic import BaseModel
except ImportError as exc:  # pragma: no cover
    raise ImportError("autostore.app requires fastapi + pydantic") from exc

from .advisor import ReadOnlyAdvisor
from .engine import Engine
from .models import EventType, Product
from .risk import RiskScorer
from .store import InMemoryStore

app = FastAPI(title="PERCIVAL Autostore — Control Plane", version="0.1.0")

# --- role auth: approver tokens (env APPROVER_TOKENS="tok:name,tok2:name2") ---
def _load_approvers() -> dict[str, str]:
    raw = os.environ.get("APPROVER_TOKENS", "demo-ops-token:ops-lead,demo-fin-token:finance-lead")
    out: dict[str, str] = {}
    for pair in raw.split(","):
        if ":" in pair:
            tok, name = pair.split(":", 1)
            out[tok.strip()] = name.strip()
    return out

_APPROVERS = _load_approvers()


def require_approver(x_approver_token: Optional[str] = Header(default=None)) -> str:
    name = _APPROVERS.get((x_approver_token or "").strip())
    if not name:
        raise HTTPException(status_code=401, detail="valid X-Approver-Token required")
    return name

_store = InMemoryStore()
_store.seed_product(Product("SKU-RIDGE-01", "Ridge Hoodie",
                            price_cents=8900, cost_cents=3200,
                            min_price_cents=4500, inventory=120))
_store.seed_product(Product("SKU-VAULT-02", "Vault Backpack",
                            price_cents=14900, cost_cents=6100,
                            min_price_cents=7500, inventory=42))
_engine = Engine(_store, risk_scorer=RiskScorer())   # risk guardrail enabled (escalates, never bypasses)
_advisor = ReadOnlyAdvisor(_store)
_SKUS = ["SKU-RIDGE-01", "SKU-VAULT-02"]


class EventIn(BaseModel):
    type: str
    payload: dict[str, Any]




@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "audit_intact": _engine.ledger.verify()}


@app.post("/v1/events")
def post_event(ev: EventIn, idempotency_key: Optional[str] = Header(default=None)) -> dict:
    try:
        kind = EventType(ev.type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"unknown event type: {ev.type}") from exc
    result, entry = _engine.handle(kind, ev.payload, idempotency_key=idempotency_key)
    risk = _engine.last_risk
    return {
        "decision": result.decision.value,
        "action": result.action,
        "risk": None if risk is None else {"score": risk.score, "band": risk.band, "factors": risk.factors},
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
def approve(pending_id: int, approver: str = Depends(require_approver)) -> dict:
    try:
        entry = _engine.approve(pending_id, approver)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"audit_ref": entry.audit_ref, "executed": entry.executed,
            "decision": entry.decision.value, "approver": approver}


@app.post("/v1/approvals/{pending_id}/deny")
def deny(pending_id: int, approver: str = Depends(require_approver)) -> dict:
    try:
        entry = _engine.deny(pending_id, approver)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"audit_ref": entry.audit_ref, "decision": entry.decision.value,
            "approver": approver}


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


@app.get("/v1/metrics")
def metrics() -> dict:
    return _engine.metrics()


@app.get("/v1/advisor/{sku}")
def advisor(sku: str) -> dict:
    """READ-ONLY suggestions. These are inert proposals — submitting one still
    goes through /v1/events where policy + risk decide. The advisor never acts."""
    report = _advisor.suggest_for_sku(sku)
    return {
        "advisory_only": True,
        "disclaimer": report.disclaimer,
        "notes": report.notes,
        "proposals": [{
            "event_type": p.event_type, "payload": p.payload, "rationale": p.rationale,
            "confidence": p.confidence,
            "projected_risk": {"score": p.projected_risk.score, "band": p.projected_risk.band,
                               "factors": p.projected_risk.factors},
        } for p in report.proposals],
    }

"""Approvals route — the human gate for high/critical actions."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..audit import log_event
from ..db import get_session
from ..models import Approval
from ..schemas import ApprovalOut, DecisionRequest

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("", response_model=list[ApprovalOut])
def list_approvals(status: str = "pending", session: Session = Depends(get_session)) -> list[Approval]:
    """List approvals filtered by status (default: pending)."""
    return list(
        session.execute(
            select(Approval).where(Approval.status == status).order_by(Approval.id.desc())
        ).scalars().all()
    )


def _decide(session: Session, approval_id: int, decision: str, req: DecisionRequest) -> Approval:
    approval = session.get(Approval, approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=409, detail=f"approval already {approval.status}")
    approval.status = decision
    approval.decided_by = req.decided_by
    approval.decided_at = datetime.now(timezone.utc)
    session.flush()
    log_event(
        session,
        actor=req.decided_by,
        action=f"approval_{decision}",
        target=approval.action,
        payload={"approval_id": approval_id, "note": req.note},
        result="executed" if decision == "approved" else "rejected",
    )
    return approval


@router.post("/{approval_id}/approve", response_model=ApprovalOut)
def approve(approval_id: int, req: DecisionRequest, session: Session = Depends(get_session)) -> Approval:
    """Approve a gated action. Execution of the side effect happens downstream."""
    return _decide(session, approval_id, "approved", req)


@router.post("/{approval_id}/reject", response_model=ApprovalOut)
def reject(approval_id: int, req: DecisionRequest, session: Session = Depends(get_session)) -> Approval:
    """Reject a gated action; nothing is executed."""
    return _decide(session, approval_id, "rejected", req)

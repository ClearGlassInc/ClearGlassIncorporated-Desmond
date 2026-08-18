"""Approvals route — the human gate for high/critical actions."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import approval_executor, executors  # noqa: F401 - import registers the executors
from ..audit import log_event
from ..db import get_session
from ..models import Approval
from ..schemas import ApprovalExecutionOut, ApprovalOut, DecisionRequest
from ..security import rate_limit, require_admin

router = APIRouter(prefix="/approvals", tags=["approvals"])

# Admin auth is applied router-wide in main.py; this adds abuse throttling on decisions.
_decision_throttle = rate_limit("approval_decisions", "rate_limit_decisions_per_minute")


def _resolve_decider(principal: str, req: DecisionRequest) -> str:
    """The authoritative decider is the authenticated admin credential, never the
    self-asserted request body — otherwise anyone able to reach the gate could sign
    another operator's name to a pricing/refund approval. In open dev mode there is no
    credential to trust, so fall back to the request's label purely for readability.
    """
    if principal == "dev-open":
        return req.decided_by or "dev-open"
    return principal


@router.get("", response_model=list[ApprovalOut])
def list_approvals(status: str = "pending", session: Session = Depends(get_session)) -> list[Approval]:
    """List approvals filtered by status (default: pending)."""
    return list(
        session.execute(
            select(Approval).where(Approval.status == status).order_by(Approval.id.desc())
        ).scalars().all()
    )


def _decide(
    session: Session, approval_id: int, decision: str, req: DecisionRequest, principal: str
) -> Approval:
    approval = session.get(Approval, approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=409, detail=f"approval already {approval.status}")
    decider = _resolve_decider(principal, req)
    approval.status = decision
    approval.decided_by = decider
    approval.decided_at = datetime.now(timezone.utc)
    session.flush()
    payload = {"approval_id": approval_id, "note": req.note}
    # Preserve any self-asserted label for forensic context, but only as an annotation —
    # the trusted actor above is always the authenticated credential, never this field.
    if req.decided_by and req.decided_by != decider:
        payload["asserted_by"] = req.decided_by
    log_event(
        session,
        actor=decider,
        action=f"approval_{decision}",
        target=approval.action,
        payload=payload,
        result="executed" if decision == "approved" else "rejected",
    )
    return approval


@router.post(
    "/{approval_id}/approve",
    response_model=ApprovalOut,
    dependencies=[Depends(_decision_throttle)],
)
def approve(
    approval_id: int,
    req: DecisionRequest,
    principal: str = Depends(require_admin),
    session: Session = Depends(get_session),
) -> Approval:
    """Approve a gated action. Execution of the side effect happens downstream."""
    return _decide(session, approval_id, "approved", req, principal)


@router.post(
    "/{approval_id}/reject",
    response_model=ApprovalOut,
    dependencies=[Depends(_decision_throttle)],
)
def reject(
    approval_id: int,
    req: DecisionRequest,
    principal: str = Depends(require_admin),
    session: Session = Depends(get_session),
) -> Approval:
    """Reject a gated action; nothing is executed."""
    return _decide(session, approval_id, "rejected", req, principal)


@router.get("/coverage")
def coverage() -> dict:
    """Which gated actions can actually be carried out once approved.

    Worth an endpoint of its own because the failure it describes is invisible
    from the queue: an ``uncovered`` action's approval looks exactly like a
    covered one's, right up until nothing happens. Read this before promising a
    customer that approving something will do it.
    """
    return approval_executor.coverage()


@router.post(
    "/{approval_id}/execute",
    response_model=ApprovalExecutionOut,
    dependencies=[Depends(_decision_throttle)],
)
def execute(
    approval_id: int,
    principal: str = Depends(require_admin),
    session: Session = Depends(get_session),
) -> ApprovalExecutionOut:
    """Carry out an already-approved action.

    Separate from ``/approve`` on purpose. Deciding and doing are different acts:
    an approver may not be the operator who runs it, execution can fail and need
    a retry that must not silently re-approve, and keeping them apart means the
    ledger records who decided and who acted as two facts rather than one guess.

    Safe to call twice — the approval is claimed atomically, so the second call
    reports ``executed: false`` with a reason instead of acting again.
    """
    try:
        result = approval_executor.execute_approval(session, approval_id, actor=principal)
    except approval_executor.ApprovalNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except approval_executor.ApprovalExecutionError as exc:
        # 409, not 500: the request is well-formed and the caller is authorised —
        # the approval is simply not in a state that can be executed. A 500 would
        # read as "retry me", which for a money-moving action is the wrong advice.
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return ApprovalExecutionOut(**result)

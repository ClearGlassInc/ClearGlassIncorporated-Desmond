"""What happens *after* a human approves — the other half of the gate.

The governance gate has always had two halves, and only one was built. Every
``ALWAYS_ESCALATE`` action queues an ``approvals`` row, a human approves it via
``POST /approvals/{id}/approve`` … and then, for all but one action, nothing.
The row sat at ``approved`` forever. An operator who approved a refund had no way
to tell that no refund had been issued: the queue said approved, the ledger said
approved, and the customer's money never moved. A gate that cannot be *passed
through* is not a gate, it is a wall with a sign on it.

This module is the pass-through, and it is deliberately narrow:

* An approved row executes **exactly once**. The claim is a conditional
  ``UPDATE ... WHERE status = 'approved'`` whose row count is the proof, committed
  before any side effect runs. Two concurrent executions race on that row and one
  loses; one human decision can never become two refunds.
* An action with **no registered executor is refused, loudly**, and the row is
  left at ``approved`` untouched. This is the important case: it is what turns a
  silent dead end into a visible one. ``GET /approvals/coverage`` and the daily
  loop both report the gap, so "approved but nothing can act on it" is a fact you
  are told rather than one you discover from a customer.
* Nothing here re-scores or re-gates. By the time a row is ``approved`` the
  governance decision has been made and audited; re-deciding it would either
  duplicate ``score_action`` or, worse, disagree with it.

Registration lives in :mod:`app.executors` so this module imports no business
logic and stays cheap to reason about.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .audit import log_event
from .governance import ALWAYS_ESCALATE, score_action
from .models import Approval

#: An executor receives the approval it is allowed to act on, already claimed,
#: and returns a JSON-serialisable summary of what it did. Raising is a legitimate
#: outcome: the claim stays spent and the failure is recorded (see ``execute_approval``).
ApprovalExecutor = Callable[[Session, Approval], dict[str, Any]]

_EXECUTORS: dict[str, ApprovalExecutor] = {}

#: Actions whose approval is claimed by their own dedicated endpoint rather than
#: the generic dispatcher. Listing one here is not an exemption from execution —
#: it says the execution path exists somewhere better placed, and names it, so a
#: reader is never left guessing whether an action is covered.
DELEGATED_ACTIONS: dict[str, str] = {}


class ApprovalExecutionError(RuntimeError):
    """The approval cannot be executed as it stands."""


class ApprovalNotFound(ApprovalExecutionError):
    """No such approval. Distinct so a caller can answer 404 rather than 409."""


def register_executor(action: str, executor: ApprovalExecutor) -> None:
    """Bind an action to the code that carries it out once approved."""
    _EXECUTORS[action] = executor


def register_delegated(action: str, where: str) -> None:
    """Record that ``action`` is executed by a dedicated path, naming it."""
    DELEGATED_ACTIONS[action] = where


def executor_for(action: str) -> ApprovalExecutor | None:
    return _EXECUTORS.get(action)


def coverage() -> dict[str, Any]:
    """Which gated actions can actually be carried out, and which cannot.

    Reported rather than merely known, because the failure this module exists to
    fix was invisible. An action in ``uncovered`` will queue approvals that no
    code can act on — approving one changes nothing but the row's status.
    """
    covered = sorted(_EXECUTORS)
    delegated = dict(sorted(DELEGATED_ACTIONS.items()))
    uncovered = sorted(ALWAYS_ESCALATE - set(covered) - set(delegated))
    return {
        "executable": covered,
        "delegated": delegated,
        "uncovered": uncovered,
        "note": (
            "'uncovered' actions are still correctly gated — they simply have no "
            "implementation behind the gate, so an approval for one executes nothing. "
            "They are reported here rather than failing silently."
        ),
    }


def claim_approval(session: Session, *, action: str, target: str) -> Approval | None:
    """Atomically claim one approved approval for this action and target.

    The gate only works if an approval is spent exactly once. The claim is a
    conditional ``UPDATE ... WHERE status = 'approved'`` whose row count is the
    proof: two concurrent claims race on the same row and exactly one wins, so a
    single human decision cannot be replayed into two supplier charges. An
    approval is bound to its target, so approving one shipment can never confirm
    a different one.
    """
    candidate = session.scalar(
        select(Approval)
        .where(Approval.action == action, Approval.target == target, Approval.status == "approved")
        .order_by(Approval.id)
        .limit(1)
    )
    if candidate is None:
        return None
    return _claim_row(session, candidate)


def _claim_row(session: Session, approval: Approval) -> Approval | None:
    """Spend one specific approved row, or return None if someone else got it."""
    claimed = session.execute(
        update(Approval)
        .where(Approval.id == approval.id, Approval.status == "approved")
        .values(status="executed")
    )
    if claimed.rowcount != 1:
        return None  # another worker claimed it first

    # Commit the claim *before* the caller spends money. A flush alone lives
    # inside the request transaction, so a crash between an external system
    # accepting the action and the request committing would roll the row back to
    # `approved` and let the same decision authorise a second charge. Committing
    # here trades that for the opposite failure: a claim spent without the call
    # having demonstrably happened, which needs a fresh human decision rather
    # than silently paying twice.
    session.commit()
    return approval


def execute_approval(session: Session, approval_id: int, *, actor: str = "operator") -> dict[str, Any]:
    """Carry out one approved action. Idempotent by construction — see the claim.

    Refuses, without touching the row, when the approval is not approved or when
    nothing knows how to execute it. Both refusals are audited: an operator who
    approved something must be able to find out that it did not happen.
    """
    approval = session.get(Approval, approval_id)
    if approval is None:
        raise ApprovalNotFound(f"approval {approval_id} not found")

    if approval.status != "approved":
        # Includes the already-executed case. Reported, not raised, so a
        # double-click reads as "already done" rather than an error page.
        return {
            "approval_id": approval.id,
            "action": approval.action,
            "status": approval.status,
            "executed": False,
            "skipped": f"approval is {approval.status!r}, not 'approved'",
        }

    delegated_to = DELEGATED_ACTIONS.get(approval.action)
    if delegated_to is not None:
        # Do NOT claim it here. The dedicated path claims the row itself, and a
        # claim taken by this dispatcher would leave that path unable to find an
        # approved row — it would queue a *second* approval and ask the human to
        # decide again, having already spent their first decision on nothing.
        return {
            "approval_id": approval.id,
            "action": approval.action,
            "status": approval.status,
            "executed": False,
            "delegated_to": delegated_to,
            "skipped": f"execute this action via {delegated_to}",
        }

    executor = _EXECUTORS.get(approval.action)
    if executor is None:
        # The row stays `approved`. Marking it executed would claim work that no
        # code performed, which is precisely the silent dead end this module
        # exists to remove.
        log_event(
            session,
            actor=actor,
            action=approval.action,
            target=approval.target,
            payload={"approval_id": approval.id, "reason": "no executor registered for this action"},
            result="blocked_no_executor",
            assessment=score_action(approval.action, approval.payload or {}),
        )
        session.commit()
        raise ApprovalExecutionError(
            f"'{approval.action}' has no executor — the approval is gated correctly but nothing "
            "in this service can carry it out. It remains approved and unexecuted; see "
            "GET /approvals/coverage."
        )

    if _claim_row(session, approval) is None:
        # The in-memory row still says `approved` — the winning claim happened in
        # another transaction. Re-read it so the caller is told the real state
        # rather than the one this session happened to load.
        session.refresh(approval)
        return {
            "approval_id": approval.id,
            "action": approval.action,
            "status": approval.status,
            "executed": False,
            "skipped": "another execution claimed this approval first",
        }

    assessment = score_action(approval.action, approval.payload or {})
    try:
        data = executor(session, approval)
    except Exception as exc:  # noqa: BLE001 - any failure must leave a record, not a traceback
        # The claim stays spent: the executor may have partially applied before
        # failing, and re-running it blind could charge, refund, or publish twice.
        # A retry needs a fresh human decision, so the row is marked `failed`
        # rather than returned to `approved`.
        session.rollback()
        session.execute(
            update(Approval).where(Approval.id == approval_id, Approval.status == "executed")
            .values(status="failed")
        )
        log_event(
            session,
            actor=actor,
            action=approval.action,
            target=approval.target,
            payload={"approval_id": approval_id, "error": str(exc)},
            result="error",
            assessment=assessment,
        )
        session.commit()
        raise ApprovalExecutionError(
            f"executing approval {approval_id} failed: {exc}. The approval is spent and marked "
            "'failed'; retrying requires a new approval."
        ) from exc

    log_event(
        session,
        actor=actor,
        action=approval.action,
        target=approval.target,
        payload={"approval_id": approval_id, "result": data},
        result="executed",
        assessment=assessment,
    )
    return {
        "approval_id": approval_id,
        "action": approval.action,
        "status": "executed",
        "executed": True,
        "data": data,
    }

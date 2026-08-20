"""The other half of the approval gate: what happens once a human says yes.

Before this existed, every ALWAYS_ESCALATE action queued an approval that only
one code path in the whole service knew how to consume. Approving a refund set a
row to 'approved' and moved no money, and nothing anywhere said so. These tests
pin the two properties that fix requires:

1. An approved action executes **exactly once**, or not at all — never twice.
2. An action with no executor **fails loudly and stays approved**. Silently
   marking it executed would be worse than the dead end it replaces.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app import approval_executor, executors, payments
from app.approval_executor import ApprovalExecutionError, ApprovalNotFound, execute_approval
from app.governance import ALWAYS_ESCALATE
from app.models import Approval, Base, Event, Order


@pytest.fixture()
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        yield db


@pytest.fixture(autouse=True)
def _registry():
    """Restore the real registry after any test that swaps entries into it."""
    saved_executors = dict(approval_executor._EXECUTORS)
    saved_delegated = dict(approval_executor.DELEGATED_ACTIONS)
    yield
    approval_executor._EXECUTORS.clear()
    approval_executor._EXECUTORS.update(saved_executors)
    approval_executor.DELEGATED_ACTIONS.clear()
    approval_executor.DELEGATED_ACTIONS.update(saved_delegated)


def make_approval(session: Session, *, action="trigger_refund", status="approved", **payload) -> Approval:
    approval = Approval(
        action=action,
        target=payload.get("target", "1"),
        payload=payload.get("payload", {}),
        risk_score=95,
        risk_tier="critical",
        status=status,
        requested_by="operations_agent",
    )
    session.add(approval)
    session.flush()
    return approval


def make_paid_order(session: Session, **overrides) -> Order:
    fields = {
        "status": "paid",
        "total": Decimal("200.00"),
        "currency": "CAD",
        "external_ref": "cs_test_refundable",
    }
    fields.update(overrides)
    order = Order(**fields)
    session.add(order)
    session.flush()
    return order


class TestExactlyOnce:
    def test_an_approved_action_executes(self, session):
        calls = []
        approval_executor.register_executor(
            "trigger_refund", lambda s, a: calls.append(a.id) or {"ok": True}
        )
        approval = make_approval(session)

        result = execute_approval(session, approval.id)

        assert result["executed"] is True
        assert result["data"] == {"ok": True}
        assert calls == [approval.id]
        assert session.get(Approval, approval.id).status == "executed"

    def test_a_second_execution_does_nothing(self, session):
        """The whole point. One human decision is one action, not one per click."""
        calls = []
        approval_executor.register_executor(
            "trigger_refund", lambda s, a: calls.append(a.id) or {"ok": True}
        )
        approval = make_approval(session)

        execute_approval(session, approval.id)
        again = execute_approval(session, approval.id)

        assert again["executed"] is False
        assert "not 'approved'" in again["skipped"]
        assert calls == [approval.id], "the executor ran twice for one approval"

    def test_a_pending_approval_is_refused(self, session):
        approval_executor.register_executor("trigger_refund", lambda s, a: {"ok": True})
        approval = make_approval(session, status="pending")

        result = execute_approval(session, approval.id)

        assert result["executed"] is False
        assert session.get(Approval, approval.id).status == "pending"

    def test_a_rejected_approval_is_refused(self, session):
        """A rejection must not be executable by anyone who knows the id."""
        approval_executor.register_executor("trigger_refund", lambda s, a: {"ok": True})
        approval = make_approval(session, status="rejected")

        assert execute_approval(session, approval.id)["executed"] is False
        assert session.get(Approval, approval.id).status == "rejected"

    def test_unknown_approval_is_distinguishable_from_a_bad_state(self, session):
        with pytest.raises(ApprovalNotFound):
            execute_approval(session, 9999)


class TestNoExecutorFailsLoudly:
    def test_an_unexecutable_action_raises_and_stays_approved(self, session):
        """The dead end, now visible.

        `update_pricing` is gated and has no implementation. Approving one must
        not report success, and must not consume the approval — a human's
        decision is not spent on work nothing performed.
        """
        approval = make_approval(session, action="update_pricing")

        with pytest.raises(ApprovalExecutionError, match="no executor"):
            execute_approval(session, approval.id)

        assert session.get(Approval, approval.id).status == "approved"

    def test_the_refusal_is_recorded_in_the_ledger(self, session):
        approval = make_approval(session, action="update_payment_settings")

        with pytest.raises(ApprovalExecutionError):
            execute_approval(session, approval.id)

        results = [e.result for e in session.scalars(select(Event)).all()]
        assert "blocked_no_executor" in results

    def test_coverage_names_every_gated_action_exactly_once(self, session):
        executors.register_all()
        report = approval_executor.coverage()
        accounted = set(report["executable"]) | set(report["delegated"]) | set(report["uncovered"])
        assert ALWAYS_ESCALATE <= accounted, (
            "a gated action is missing from the coverage report: "
            f"{sorted(ALWAYS_ESCALATE - accounted)}"
        )
        # Nothing may be claimed as both executable and uncovered.
        assert not set(report["executable"]) & set(report["uncovered"])


class TestDelegatedActions:
    def test_printful_confirmation_is_not_claimed_by_the_generic_dispatcher(self, session):
        """Claiming here would strand the real path.

        `confirm_shipment` looks for an *approved* row of its own. If this
        dispatcher spent it first, that path would find none, queue a second
        approval, and ask the operator to decide again — having already burned
        the first decision on nothing.
        """
        executors.register_all()
        approval = make_approval(session, action="printful_confirm_order")

        result = execute_approval(session, approval.id)

        assert result["executed"] is False
        assert "/fulfillment/shipments/" in result["delegated_to"]
        assert session.get(Approval, approval.id).status == "approved"


class TestFailureLeavesEvidence:
    def test_a_failing_executor_spends_the_approval_and_records_why(self, session):
        """A partially-applied action must not be silently retryable.

        The executor may have reached Stripe before failing, so returning the row
        to `approved` would invite a second refund. It is marked `failed`: spent,
        visible, and needing a fresh human decision.
        """
        def boom(s, a):
            raise RuntimeError("stripe said no")

        approval_executor.register_executor("trigger_refund", boom)
        approval = make_approval(session)

        with pytest.raises(ApprovalExecutionError, match="stripe said no"):
            execute_approval(session, approval.id)

        assert session.get(Approval, approval.id).status == "failed"
        errors = [e for e in session.scalars(select(Event)).all() if e.result == "error"]
        assert errors, "a failed execution left nothing in the audit ledger"

    def test_a_failed_approval_cannot_be_re_executed(self, session):
        calls = []

        def flaky(s, a):
            calls.append(a.id)
            raise RuntimeError("nope")

        approval_executor.register_executor("trigger_refund", flaky)
        approval = make_approval(session)

        with pytest.raises(ApprovalExecutionError):
            execute_approval(session, approval.id)
        assert execute_approval(session, approval.id)["executed"] is False
        assert calls == [approval.id]


class TestRefundExecutor:
    """The one money-moving executor. Offline: no Stripe key ⇒ mock mode."""

    def test_a_full_refund_closes_the_order(self, session):
        order = make_paid_order(session)
        approval = make_approval(session, payload={"order_id": order.id, "reason": "damaged"})

        result = execute_approval(session, approval.id)

        assert result["executed"] is True
        assert result["data"]["mode"] == "mock"
        assert session.get(Order, order.id).status == "refunded"

    def test_a_partial_refund_does_not_close_the_order(self, session):
        """A $5 goodwill refund on a $200 order must not hide $195 of revenue."""
        order = make_paid_order(session)
        approval = make_approval(session, payload={"order_id": order.id, "amount": 500})

        execute_approval(session, approval.id)

        assert session.get(Order, order.id).status == "partially_refunded"

    def test_an_unpaid_order_cannot_be_refunded(self, session):
        order = make_paid_order(session, status="pending", external_ref="cs_unpaid")
        approval = make_approval(session, payload={"order_id": order.id})

        with pytest.raises(ApprovalExecutionError, match="only a paid order"):
            execute_approval(session, approval.id)

        assert session.get(Order, order.id).status == "pending"

    def test_refunding_twice_is_refused_by_the_order_state(self, session):
        """Belt and braces: even with two approvals, the order guards itself."""
        order = make_paid_order(session)
        first = make_approval(session, payload={"order_id": order.id})
        second = make_approval(session, payload={"order_id": order.id})

        execute_approval(session, first.id)
        with pytest.raises(ApprovalExecutionError, match="only a paid order"):
            execute_approval(session, second.id)

    def test_a_missing_order_is_an_error_not_a_silent_success(self, session):
        approval = make_approval(session, payload={"order_id": 4242})
        with pytest.raises(ApprovalExecutionError, match="not found"):
            execute_approval(session, approval.id)

    def test_the_approver_chose_the_amount_not_the_caller(self, session):
        """The executed refund reads the payload the human approved.

        Taking the amount from the executing request instead would mean an
        operator approves one refund and a different one is issued.
        """
        order = make_paid_order(session)
        approval = make_approval(session, payload={"order_id": order.id, "amount": 1234})

        result = execute_approval(session, approval.id)

        assert result["data"]["amount"] == 1234


class TestRefundCall:
    """`payments.create_refund` itself, without a Stripe key."""

    def test_no_payment_reference_is_rejected(self):
        with pytest.raises(ValueError, match="nothing to refund"):
            payments.create_refund("")

    @pytest.mark.parametrize("amount", [0, -1, -500])
    def test_a_non_positive_amount_is_rejected(self, amount):
        """Stripe would reject it, but not before the row said the refund happened."""
        with pytest.raises(ValueError, match="positive"):
            payments.create_refund("cs_test_1", amount=amount)

    def test_mock_mode_never_reaches_the_network(self):
        result = payments.create_refund("cs_test_1", amount=100)
        assert result["mode"] == "mock"
        assert result["status"] == "succeeded"

    def test_free_text_reasons_are_not_smuggled_into_stripes_enum(self):
        """Stripe accepts three reasons and rejects everything else.

        The enum check lives in `create_refund`; this pins the vocabulary so a
        later edit cannot widen it and start failing live refunds.
        """
        assert payments.STRIPE_REFUND_REASONS == {
            "duplicate",
            "fraudulent",
            "requested_by_customer",
        }

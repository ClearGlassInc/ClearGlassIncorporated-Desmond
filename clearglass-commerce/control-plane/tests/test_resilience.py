"""Resilience & abuse-control tests — rate limiting, webhook idempotency, the
readiness probe, and security response headers. Offline: SQLite in-memory, no network.

Complements tests/test_security.py, which unit-tests the admin-auth guard itself.
"""
from __future__ import annotations

import json
import os

# Pin to an in-memory SQLite engine before importing app.db (which builds the engine at import).
os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import db as db_module
from app import payments
from app import security as security_module
from app.config import get_settings
from app.main import create_app
from app.models import Approval, Base, Event, Order
from app.security import SlidingWindowLimiter


@pytest.fixture()
def harness(monkeypatch):
    """Fresh app + DB + rate limiter per test; clears the settings cache on both sides."""
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test_123")
    monkeypatch.setattr(security_module, "_limiter", SlidingWindowLimiter())

    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_session():
        session = TestingSession()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def build(peer: str = "10.0.0.9"):
        """Build a client whose TCP peer is ``peer``.

        The default is a private address so it matches the trusted-proxy allowlist the
        proxy tests configure; pass a public address to simulate a request arriving on
        an ingress that is not the proxy.
        """
        get_settings.cache_clear()
        app = create_app()
        app.dependency_overrides[db_module.get_session] = override_session
        return TestClient(app, client=(peer, 51234))

    yield build, TestingSession, monkeypatch
    get_settings.cache_clear()


def test_limiter_allows_within_window_and_blocks_over() -> None:
    limiter = SlidingWindowLimiter()
    assert all(limiter.allow("k", 3) for _ in range(3))
    assert limiter.allow("k", 3) is False
    assert limiter.allow("other", 3) is True   # independent keys


def test_checkout_rate_limit_returns_429(harness) -> None:
    build, _, monkeypatch = harness
    monkeypatch.setenv("RATE_LIMIT_CHECKOUT_PER_MINUTE", "2")
    client = build()
    body = {"items": [{"sku": "quick-audit", "quantity": 1}]}
    codes = [client.post("/checkout/session", json=body).status_code for _ in range(3)]
    assert codes[:2] == [200, 200]
    assert codes[-1] == 429


def test_decision_rate_limit_returns_429(harness) -> None:
    build, TestingSession, monkeypatch = harness
    monkeypatch.setenv("RATE_LIMIT_DECISIONS_PER_MINUTE", "3")
    client = build()
    with TestingSession() as s:
        approval = Approval(action="update_pricing", risk_score=80, risk_tier="high")
        s.add(approval)
        s.commit()
        approval_id = approval.id
    decision = {"decided_by": "desmond", "note": "throttle test"}
    codes = [
        client.post(f"/approvals/{approval_id}/reject", json=decision).status_code
        for _ in range(4)
    ]
    assert codes[-1] == 429


def test_rate_limit_zero_disables_throttle(harness) -> None:
    build, _, monkeypatch = harness
    monkeypatch.setenv("RATE_LIMIT_CHECKOUT_PER_MINUTE", "0")
    client = build()
    body = {"items": [{"sku": "quick-audit", "quantity": 1}]}
    codes = [client.post("/checkout/session", json=body).status_code for _ in range(5)]
    assert 429 not in codes


def _paid_checkout_event(session_id: str) -> bytes:
    event = {
        "type": "checkout.session.completed",
        "data": {"object": {"id": session_id, "amount_total": 12500, "currency": "cad"}},
    }
    return json.dumps(event).encode()


def test_webhook_redelivery_creates_single_order(harness) -> None:
    build, TestingSession, _ = harness
    client = build()
    body = _paid_checkout_event("cs_test_abc")
    header = payments.sign_payload(body, "whsec_test_123")
    for _ in range(3):
        resp = client.post("/webhooks/stripe", content=body, headers={"stripe-signature": header})
        assert resp.status_code == 200
    with TestingSession() as s:
        orders = list(s.scalars(select(Order)).all())
    assert len(orders) == 1
    assert orders[0].external_ref == "cs_test_abc"
    assert str(orders[0].total) == "125.00"


def test_webhook_distinct_sessions_create_distinct_orders(harness) -> None:
    build, TestingSession, _ = harness
    client = build()
    for sid in ("cs_one", "cs_two"):
        body = _paid_checkout_event(sid)
        header = payments.sign_payload(body, "whsec_test_123")
        assert client.post(
            "/webhooks/stripe", content=body, headers={"stripe-signature": header}
        ).status_code == 200
    with TestingSession() as s:
        assert len(list(s.scalars(select(Order)).all())) == 2


def test_ready_probe_reports_database_ok(harness) -> None:
    build, _, _ = harness
    client = build()
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json()["database"] == "ok"


def test_security_headers_present(harness) -> None:
    build, _, _ = harness
    client = build()
    resp = client.get("/health")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


# --- approver identity binding ---------------------------------------------
# A decision must be attributed to the authenticated credential, not a name the
# caller types into the request body — otherwise the audit ledger records fiction.


def _pending_approval(TestingSession) -> int:
    with TestingSession() as s:
        approval = Approval(action="update_pricing", risk_score=80, risk_tier="high")
        s.add(approval)
        s.commit()
        return approval.id


def test_decision_records_authenticated_principal_not_body(harness) -> None:
    build, TestingSession, monkeypatch = harness
    monkeypatch.setenv("ADMIN_API_KEY", "top-secret")
    client = build()
    approval_id = _pending_approval(TestingSession)

    resp = client.post(
        f"/approvals/{approval_id}/approve",
        json={"decided_by": "not-me", "note": "ship it"},
        headers={"Authorization": "Bearer top-secret"},
    )
    assert resp.status_code == 200
    # The credential ("admin") wins over the self-asserted "not-me".
    assert resp.json()["decided_by"] == "admin"

    with TestingSession() as s:
        approval = s.get(Approval, approval_id)
        assert approval.decided_by == "admin"
        event = s.scalars(select(Event).where(Event.action == "approval_approved")).one()
    assert event.actor == "admin"
    # The self-asserted label is preserved as an annotation, never as the actor.
    assert event.payload.get("asserted_by") == "not-me"


def test_open_mode_falls_back_to_asserted_label(harness) -> None:
    build, TestingSession, _ = harness  # no ADMIN_API_KEY -> open dev mode
    client = build()
    approval_id = _pending_approval(TestingSession)

    resp = client.post(
        f"/approvals/{approval_id}/reject",
        json={"decided_by": "desmond", "note": "no"},
    )
    assert resp.status_code == 200
    assert resp.json()["decided_by"] == "desmond"
    with TestingSession() as s:
        event = s.scalars(select(Event).where(Event.action == "approval_rejected")).one()
    assert event.actor == "desmond"
    # Nothing to disambiguate in open mode: no separate asserted_by annotation.
    assert "asserted_by" not in event.payload


# --- caller identity behind a reverse proxy ---------------------------------
# Render/Cloudflare terminate TLS in front of the container and uvicorn only trusts
# X-Forwarded-For from 127.0.0.1, so request.client.host is the proxy. Without an
# explicit hop count every customer shares one throttle bucket — but the hop count
# alone must never be enough to trust the header (see the untrusted-peer test below).

TRUSTED_PROXY_CIDR = "10.0.0.0/8"


def test_throttle_isolates_callers_behind_a_declared_proxy(harness) -> None:
    build, _, monkeypatch = harness
    monkeypatch.setenv("RATE_LIMIT_CHECKOUT_PER_MINUTE", "2")
    monkeypatch.setenv("TRUSTED_PROXY_HOPS", "1")
    monkeypatch.setenv("TRUSTED_PROXY_IPS", TRUSTED_PROXY_CIDR)
    client = build()  # peer 10.0.0.9 is inside the allowlist
    body = {"items": [{"sku": "quick-audit", "quantity": 1}]}

    def post(caller: str) -> int:
        # The proxy appends the real peer, so the rightmost entry is the trustworthy one.
        return client.post(
            "/checkout/session", json=body, headers={"x-forwarded-for": caller}
        ).status_code

    assert [post("203.0.113.10") for _ in range(3)] == [200, 200, 429]
    # A different customer behind the same proxy must not inherit that exhaustion.
    assert post("198.51.100.22") == 200


def test_spoofed_forwarded_for_cannot_evade_the_throttle(harness) -> None:
    build, _, monkeypatch = harness
    monkeypatch.setenv("RATE_LIMIT_CHECKOUT_PER_MINUTE", "2")
    monkeypatch.setenv("TRUSTED_PROXY_HOPS", "1")
    monkeypatch.setenv("TRUSTED_PROXY_IPS", TRUSTED_PROXY_CIDR)
    client = build()
    body = {"items": [{"sku": "quick-audit", "quantity": 1}]}

    # The abuser rotates the value it sends; the proxy still appends its real address,
    # so the trusted rightmost hop stays constant and the throttle still bites.
    codes = [
        client.post(
            "/checkout/session",
            json=body,
            headers={"x-forwarded-for": f"192.168.5.{i}, 203.0.113.99"},
        ).status_code
        for i in range(3)
    ]
    assert codes == [200, 200, 429]


def test_forwarded_for_from_an_untrusted_peer_cannot_rotate_buckets(harness) -> None:
    """Trusting the hop count alone was a full throttle bypass.

    A request that reaches the service on an ingress that is not the proxy — a private
    service address, an internal mesh, a directly reachable container port — has nothing
    appending the real peer, so the caller owns every hop. Rotating the rightmost value
    then mints a fresh limiter bucket per request. The header must be ignored unless the
    TCP peer is an approved proxy.
    """
    build, _, monkeypatch = harness
    monkeypatch.setenv("RATE_LIMIT_CHECKOUT_PER_MINUTE", "2")
    monkeypatch.setenv("TRUSTED_PROXY_HOPS", "1")
    monkeypatch.setenv("TRUSTED_PROXY_IPS", TRUSTED_PROXY_CIDR)
    client = build(peer="203.0.113.7")  # public peer, outside the allowlist
    body = {"items": [{"sku": "quick-audit", "quantity": 1}]}

    codes = [
        client.post(
            "/checkout/session", json=body, headers={"x-forwarded-for": f"9.9.9.{i}"}
        ).status_code
        for i in range(6)
    ]
    assert codes == [200, 200, 429, 429, 429, 429]


def test_forwarded_for_ignored_when_no_proxy_allowlist_is_configured(harness) -> None:
    """Hops declared but no allowlist: fail toward over-throttling, never bypass."""
    build, _, monkeypatch = harness
    monkeypatch.setenv("RATE_LIMIT_CHECKOUT_PER_MINUTE", "2")
    monkeypatch.setenv("TRUSTED_PROXY_HOPS", "1")
    monkeypatch.delenv("TRUSTED_PROXY_IPS", raising=False)
    client = build()
    body = {"items": [{"sku": "quick-audit", "quantity": 1}]}

    codes = [
        client.post(
            "/checkout/session", json=body, headers={"x-forwarded-for": f"9.9.9.{i}"}
        ).status_code
        for i in range(4)
    ]
    assert codes == [200, 200, 429, 429]


def test_client_identity_only_reads_the_header_from_an_approved_proxy() -> None:
    from app.security import client_identity

    class _Req:
        def __init__(self, peer: str) -> None:
            self.client = type("C", (), {"host": peer})()
            self.headers = {"x-forwarded-for": "1.2.3.4"}

    proxy = _Req("10.0.0.9")
    stranger = _Req("203.0.113.7")

    # No declared proxies: the header is attacker-controlled and must be ignored.
    assert client_identity(proxy, 0, TRUSTED_PROXY_CIDR) == "10.0.0.9"
    # Declared proxy, but no allowlist -> the peer cannot be verified, so ignore it.
    assert client_identity(proxy, 1, "") == "10.0.0.9"
    # Peer outside the allowlist -> ignore the header it supplied.
    assert client_identity(stranger, 1, TRUSTED_PROXY_CIDR) == "203.0.113.7"
    # Approved proxy with the promised hops -> the caller it named.
    assert client_identity(proxy, 1, TRUSTED_PROXY_CIDR) == "1.2.3.4"
    # Raising the bound past the header length changes nothing: the walk stops at the
    # first untrusted entry, which is the caller. It only falls back to the peer when
    # it runs out of entries while still traversing trusted proxies (covered by
    # test_multi_hop_padding_cannot_select_an_attacker_value).
    assert client_identity(proxy, 2, TRUSTED_PROXY_CIDR) == "1.2.3.4"


def test_multi_hop_padding_cannot_select_an_attacker_value() -> None:
    """Counting back a fixed index was still spoofable above one hop.

    An attacker who reaches the last proxy directly can pad X-Forwarded-For so the
    counted-back position lands on a value it chose — the proxy only ever appends one
    address. Walking right to left and stopping at the first entry that is not itself a
    trusted proxy makes the padding land on the attacker's own address instead.
    """
    from app.security import client_identity

    class _Req:
        def __init__(self, peer: str, forwarded: str) -> None:
            self.client = type("C", (), {"host": peer})()
            self.headers = {"x-forwarded-for": forwarded}

    trusted = "10.0.0.0/8"

    # Two hops configured. The attacker connects straight to the last proxy (10.0.0.9)
    # sending a chosen value; that proxy appends the attacker's real address.
    attack = _Req("10.0.0.9", "203.0.113.250, 198.51.100.77")
    assert client_identity(attack, 2, trusted) == "198.51.100.77"  # not the chosen value

    # A genuine two-proxy chain still resolves the real client: the first proxy appends
    # the client, the second appends the first proxy.
    chain = _Req("10.0.0.9", "203.0.113.10, 10.0.0.5")
    assert client_identity(chain, 2, trusted) == "203.0.113.10"

    # All entries within the bound are proxies -> the caller is not identifiable.
    opaque = _Req("10.0.0.9", "10.0.0.5, 10.0.0.6")
    assert client_identity(opaque, 2, trusted) == "10.0.0.9"


def test_peer_is_trusted_proxy_handles_cidrs_and_junk() -> None:
    from app.security import peer_is_trusted_proxy

    assert peer_is_trusted_proxy("10.1.2.3", "10.0.0.0/8") is True
    assert peer_is_trusted_proxy("172.16.4.5", "10.0.0.0/8,172.16.0.0/12") is True
    assert peer_is_trusted_proxy("203.0.113.7", "10.0.0.0/8") is False
    assert peer_is_trusted_proxy("10.1.2.3", "") is False
    # A bare address is treated as a single host.
    assert peer_is_trusted_proxy("192.0.2.5", "192.0.2.5") is True
    # Non-IP peers (unix sockets, ASGI test transports) are never proxies.
    assert peer_is_trusted_proxy("testclient", "10.0.0.0/8") is False
    # Invalid entries are skipped, not fatal.
    assert peer_is_trusted_proxy("10.1.2.3", "not-an-ip,10.0.0.0/8") is True


def test_health_reports_the_peer_and_whether_the_header_is_trusted(harness) -> None:
    """Behind a proxy the router's address is otherwise hard to discover, and
    TRUSTED_PROXY_IPS cannot be set safely without it."""
    build, _, monkeypatch = harness
    monkeypatch.delenv("TRUSTED_PROXY_IPS", raising=False)
    monkeypatch.setenv("TRUSTED_PROXY_HOPS", "0")
    body = build(peer="10.0.0.9").get("/health").json()
    assert body["client_peer"] == "10.0.0.9"
    assert body["forwarded_for"] == "ignored"

    monkeypatch.setenv("TRUSTED_PROXY_HOPS", "1")
    monkeypatch.setenv("TRUSTED_PROXY_IPS", TRUSTED_PROXY_CIDR)
    assert build(peer="10.0.0.9").get("/health").json()["forwarded_for"] == "trusted"
    assert build(peer="203.0.113.7").get("/health").json()["forwarded_for"] == "ignored"

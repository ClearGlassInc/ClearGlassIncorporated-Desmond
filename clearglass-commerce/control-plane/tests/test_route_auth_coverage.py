"""Every mutating route must be behind the admin guard — enforced, not assumed.

`require_admin` is correct and `main.py` applies it at include time. The gap this
closes is coverage drift: a new router, or a new POST added to an existing one,
can ship unguarded and nothing fails. That is the shape of the RMM auth-bypass
class tracked in `security/RMM_AUTH_BYPASS_HARDENING.md` — the control was never
wrong, its coverage was incomplete.

So the allow-list below is the whole security argument for the open surface, and
adding to it is a deliberate act with a reason attached.

Route discovery is deliberately version-tolerant. FastAPI <=0.13x flattens
included routers into ``app.routes``; 0.14x keeps them as ``_IncludedRouter``
wrappers that hold the include-time dependencies separately from the route's own
dependency tree. A guard applied either way must count, and a discovery failure
must fail the suite rather than silently pass it — see
``test_route_discovery_actually_finds_routes``.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi.routing import APIRoute

from app.main import create_app
from app.security import require_admin

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

#: Routes that are intentionally reachable without an admin credential.
#: Each entry needs a reason that survives a reviewer asking "why is this open?".
PUBLIC_MUTATING_ROUTES: dict[tuple[str, str], str] = {
    ("POST", "/checkout/session"): (
        "Customer checkout. Public by necessity; protected by a per-IP rate limit, "
        "and it creates nothing privileged — amounts come from the server-side price "
        "book (app/pricebook.py), never from the request, so an anonymous caller "
        "cannot choose what it is charged. See tests/test_pricebook.py."
    ),
    ("POST", "/webhooks/stripe"): (
        "Stripe callback. Cannot carry an operator credential; authenticated by "
        "Stripe signature verification, rate limited, and idempotent on redelivery."
    ),
}


@dataclass(frozen=True)
class DiscoveredRoute:
    method: str
    path: str
    guarded: bool

    @property
    def key(self) -> tuple[str, str]:
        return (self.method, self.path)

    def __str__(self) -> str:
        return f"{self.method} {self.path}"


def _tree_has_admin(dependencies) -> bool:
    """True when require_admin appears anywhere in a dependency tree.

    Handles both shapes FastAPI hands us: a resolved ``Dependant`` exposes the
    callable as ``.call``, while an unresolved ``Depends`` marker (what
    ``include_router(dependencies=...)`` stores) exposes it as ``.dependency``.
    Checking only one silently misses every include-time guard.
    """
    stack = list(dependencies)
    seen: list[object] = []
    while stack:
        dep = stack.pop()
        if getattr(dep, "call", None) is require_admin:
            return True
        if getattr(dep, "dependency", None) is require_admin:
            return True
        if any(dep is s for s in seen):  # pragma: no cover - cycle guard
            continue
        seen.append(dep)
        stack.extend(getattr(dep, "dependencies", []) or [])
    return False


def _discover(router_or_app, prefix: str = "", inherited_guard: bool = False) -> list[DiscoveredRoute]:
    """Walk routes, carrying include-time guards down into nested routers."""
    found: list[DiscoveredRoute] = []
    for route in getattr(router_or_app, "routes", []):
        # FastAPI 0.14x: an included router is a wrapper holding the original
        # router plus the dependencies supplied at include() time.
        context = getattr(route, "include_context", None)
        original = getattr(route, "original_router", None)
        if context is not None and original is not None:
            found.extend(
                _discover(
                    original,
                    prefix + (getattr(context, "prefix", "") or ""),
                    inherited_guard or _tree_has_admin(getattr(context, "dependencies", []) or []),
                )
            )
            continue

        # A plain nested APIRouter (no wrapper) — recurse without extra guards.
        if not isinstance(route, APIRoute) and hasattr(route, "routes"):
            found.extend(_discover(route, prefix, inherited_guard))
            continue

        if not isinstance(route, APIRoute):
            continue

        guarded = inherited_guard or _tree_has_admin(route.dependant.dependencies)
        for method in sorted(MUTATING_METHODS & set(route.methods or set())):
            found.append(DiscoveredRoute(method, prefix + route.path, guarded))
    return found


@pytest.fixture(scope="module")
def routes() -> list[DiscoveredRoute]:
    return _discover(create_app())


def test_route_discovery_actually_finds_routes(routes) -> None:
    """Guard against a vacuous pass.

    If FastAPI changes its internals again and discovery returns nothing, the
    coverage assertion below would pass by finding no violations — the worst
    possible failure mode for a security test. Pin a floor and a known route.
    """
    assert len(routes) >= 10, f"route discovery found only {len(routes)} mutating routes"
    paths = {r.path for r in routes}
    assert "/store/update-pricing" in paths, f"discovery looks broken; found: {sorted(paths)}"


def test_every_mutating_route_is_guarded_or_explicitly_public(routes) -> None:
    unguarded = sorted(
        str(r) for r in routes if not r.guarded and r.key not in PUBLIC_MUTATING_ROUTES
    )
    assert not unguarded, (
        "These mutating routes are reachable without an admin credential:\n  "
        + "\n  ".join(unguarded)
        + "\n\nAdd Depends(require_admin) (or include the router with dependencies=admin), "
        "or add the route to PUBLIC_MUTATING_ROUTES with a written reason."
    )


def test_public_allow_list_has_no_stale_entries(routes) -> None:
    """A removed or renamed route must not leave a permanent hole behind."""
    live = {r.key for r in routes}
    stale = sorted(entry for entry in PUBLIC_MUTATING_ROUTES if entry not in live)
    assert not stale, f"PUBLIC_MUTATING_ROUTES references routes that no longer exist: {stale}"


def test_public_allow_list_entries_carry_a_reason() -> None:
    for entry, reason in PUBLIC_MUTATING_ROUTES.items():
        assert len(reason.strip()) > 40, f"{entry} needs a real justification, not a placeholder"


def test_the_approval_gate_itself_is_guarded(routes) -> None:
    """The gate that authorises high-risk actions must never be openable anonymously."""
    decisions = [r for r in routes if r.path.startswith("/approvals/")]
    assert decisions, "expected approval decision routes to exist"
    for route in decisions:
        assert route.guarded, f"{route} must require an admin credential"


def test_governed_money_and_pricing_routes_are_guarded(routes) -> None:
    """Spot-check the endpoints an attacker would actually want."""
    sensitive = {"/store/update-pricing", "/payments/refund", "/etsy/publish-listing"}
    by_path = {r.path: r for r in routes}
    for path in sorted(sensitive):
        assert path in by_path, f"{path} is missing — update this test if it moved"
        assert by_path[path].guarded, f"{path} must require an admin credential"


def test_public_checkout_and_webhook_are_genuinely_unguarded(routes) -> None:
    """The allow-list must describe reality, not aspiration.

    If one of these ever gains a guard, the entry should be removed rather than
    left behind implying an open surface that no longer exists.
    """
    by_key = {r.key: r for r in routes}
    for entry in PUBLIC_MUTATING_ROUTES:
        assert entry in by_key, f"{entry} not found"
        assert not by_key[entry].guarded, (
            f"{entry} is now guarded — drop it from PUBLIC_MUTATING_ROUTES"
        )

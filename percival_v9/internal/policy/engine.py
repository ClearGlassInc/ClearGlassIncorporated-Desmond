# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""Percival v9 Policy Governor — deny-by-default, fail-closed.

Synchronous capability evaluation, mirroring the OPA sidecar contract from
``docs/PERCIVAL_V9_ARCHITECTURE.md``:

* **Deny by default** — a capability not explicitly granted is denied.
* **Escalation Gate** — capabilities tagged ``requires_approval`` are denied
  until a matching, unconsumed approval is registered.
* **Fail closed** — if the audit ledger cannot record the decision, the
  governor enters deny-all mode; nothing executes unlogged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from percival_v9.internal.audit import AuditLedger, LedgerError


class Risk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


#: Risk tiers that always require an operator approval (Escalation Gate).
GATED_RISK = frozenset({Risk.HIGH, Risk.CRITICAL})


@dataclass(frozen=True)
class Capability:
    """A named, risk-scored permission that may be granted to an identity."""

    name: str
    risk: Risk = Risk.LOW

    @property
    def requires_approval(self) -> bool:
        return self.risk in GATED_RISK


@dataclass(frozen=True)
class Decision:
    """Outcome of a policy evaluation. ``allow`` is never implicit."""

    allow: bool
    reason: str
    capability: str
    identity: str


@dataclass
class PolicyGovernor:
    """Evaluates (identity, capability) requests against explicit grants."""

    ledger: AuditLedger
    _grants: dict[str, dict[str, Capability]] = field(default_factory=dict)
    _approvals: set[tuple[str, str]] = field(default_factory=set)
    _deny_all: bool = False

    # -- administration -------------------------------------------------
    def grant(self, identity: str, capability: Capability) -> None:
        self._grants.setdefault(identity, {})[capability.name] = capability

    def revoke(self, identity: str, capability_name: str) -> None:
        self._grants.get(identity, {}).pop(capability_name, None)

    def approve(self, identity: str, capability_name: str) -> None:
        """Operator approval for one gated execution (single-use)."""
        self._approvals.add((identity, capability_name))

    @property
    def deny_all(self) -> bool:
        return self._deny_all

    # -- evaluation ------------------------------------------------------
    def evaluate(self, identity: str, capability_name: str) -> Decision:
        """Evaluate a request. The decision is recorded before it is returned."""
        decision = self._decide(identity, capability_name)
        try:
            self.ledger.append(
                {
                    "type": "policy_decision",
                    "identity": identity,
                    "capability": capability_name,
                    "allow": decision.allow,
                    "reason": decision.reason,
                }
            )
        except LedgerError:
            # Fail-Closed Audit Sync: unlogged decisions must not take effect,
            # and the governor stops allowing anything until the ledger heals.
            self._deny_all = True
            return Decision(
                allow=False,
                reason="fail-closed: audit ledger unavailable; deny-all engaged",
                capability=capability_name,
                identity=identity,
            )
        if decision.allow and decision.capability_obj is not None:
            if decision.capability_obj.requires_approval:
                self._approvals.discard((identity, capability_name))  # consume
        return Decision(decision.allow, decision.reason, capability_name, identity)

    @dataclass(frozen=True)
    class _Verdict:
        allow: bool
        reason: str
        capability_obj: Capability | None = None

    def _decide(self, identity: str, capability_name: str) -> _Verdict:
        if self._deny_all:
            return self._Verdict(False, "deny-all mode active (fail-closed)")
        cap = self._grants.get(identity, {}).get(capability_name)
        if cap is None:
            return self._Verdict(False, "deny-by-default: capability not granted")
        if cap.requires_approval and (identity, capability_name) not in self._approvals:
            return self._Verdict(
                False, f"escalation gate: {cap.risk.value}-risk action awaiting approval"
            )
        return self._Verdict(True, "granted", cap)

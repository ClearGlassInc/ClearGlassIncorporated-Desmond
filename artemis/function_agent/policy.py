# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
"""Deterministic policy and signed approval controls."""
from __future__ import annotations

import base64
import fnmatch
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from .models import (
    ApprovalChallenge,
    ApprovalGrant,
    CapabilitySpec,
    ExecutionContext,
    PolicyDecision,
    RiskLevel,
)


def arguments_digest(arguments: dict[str, Any]) -> str:
    payload = json.dumps(arguments, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class PolicyResult:
    decision: PolicyDecision
    reason: str


@dataclass(slots=True)
class AgentPolicy:
    """Fail-closed policy with role and glob-based overrides."""

    denied_capabilities: set[str] = field(default_factory=set)
    approval_capabilities: set[str] = field(default_factory=set)
    privileged_roles: set[str] = field(default_factory=lambda: {"operator", "admin"})
    risk_decisions: dict[RiskLevel, PolicyDecision] = field(
        default_factory=lambda: {
            RiskLevel.SAFE: PolicyDecision.ALLOW,
            RiskLevel.READ: PolicyDecision.ALLOW,
            RiskLevel.WRITE: PolicyDecision.REQUIRE_APPROVAL,
            RiskLevel.EXTERNAL: PolicyDecision.REQUIRE_APPROVAL,
            RiskLevel.DESTRUCTIVE: PolicyDecision.DENY,
            RiskLevel.FINANCIAL: PolicyDecision.DENY,
        }
    )

    def evaluate(self, spec: CapabilitySpec, context: ExecutionContext) -> PolicyResult:
        if self._matches(spec.name, self.denied_capabilities):
            return PolicyResult(PolicyDecision.DENY, "Capability denied by explicit policy")
        if self._matches(spec.name, self.approval_capabilities):
            return PolicyResult(
                PolicyDecision.REQUIRE_APPROVAL,
                "Capability requires explicit approval",
            )

        decision = self.risk_decisions.get(spec.risk, PolicyDecision.DENY)
        if decision is PolicyDecision.REQUIRE_APPROVAL and not (
            context.roles & self.privileged_roles
        ):
            return PolicyResult(
                decision,
                f"Risk level '{spec.risk}' requires a privileged operator",
            )
        if decision is PolicyDecision.DENY:
            return PolicyResult(decision, f"Risk level '{spec.risk}' is disabled by policy")
        return PolicyResult(decision, f"Risk level '{spec.risk}' accepted")

    @staticmethod
    def _matches(name: str, patterns: set[str]) -> bool:
        return any(fnmatch.fnmatchcase(name, pattern) for pattern in patterns)


class ApprovalManager:
    """Issues one-use, HMAC-signed approval tokens bound to exact arguments."""

    def __init__(self, secret: str | bytes | None = None, ttl_seconds: int = 300) -> None:
        raw_secret = secret.encode("utf-8") if isinstance(secret, str) else secret
        self._secret = raw_secret or secrets.token_bytes(32)
        self._ttl = timedelta(seconds=ttl_seconds)
        self._challenges: dict[str, ApprovalChallenge] = {}
        self._consumed: set[str] = set()

    def challenge(
        self,
        capability: str,
        arguments: dict[str, Any],
        context: ExecutionContext,
        reason: str,
    ) -> ApprovalChallenge:
        item = ApprovalChallenge(
            capability=capability,
            arguments_digest=arguments_digest(arguments),
            actor=context.actor,
            reason=reason,
            expires_at=datetime.now(UTC) + self._ttl,
        )
        self._challenges[item.approval_id] = item
        return item

    def grant(self, approval_id: str) -> ApprovalGrant:
        challenge = self._get_live_challenge(approval_id)
        claims = {
            "approval_id": approval_id,
            "capability": challenge.capability,
            "arguments_digest": challenge.arguments_digest,
            "actor": challenge.actor,
            "expires": int(challenge.expires_at.timestamp()),
        }
        payload = json.dumps(claims, sort_keys=True, separators=(",", ":")).encode("utf-8")
        encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
        signature = hmac.new(self._secret, encoded.encode("ascii"), hashlib.sha256).hexdigest()
        return ApprovalGrant(
            approval_id=approval_id,
            token=f"{encoded}.{signature}",
            expires_at=challenge.expires_at,
        )

    def validate_and_consume(
        self,
        token: str,
        capability: str,
        arguments: dict[str, Any],
        context: ExecutionContext,
    ) -> bool:
        try:
            encoded, signature = token.split(".", 1)
            expected = hmac.new(
                self._secret,
                encoded.encode("ascii"),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(signature, expected):
                return False

            padding = "=" * (-len(encoded) % 4)
            claims = json.loads(base64.urlsafe_b64decode(encoded + padding))
            approval_id = str(claims["approval_id"])
            challenge = self._get_live_challenge(approval_id)
            valid = (
                approval_id not in self._consumed
                and int(claims["expires"]) >= int(datetime.now(UTC).timestamp())
                and claims["capability"] == challenge.capability == capability
                and claims["arguments_digest"]
                == challenge.arguments_digest
                == arguments_digest(arguments)
                and claims["actor"] == challenge.actor == context.actor
            )
            if valid:
                self._consumed.add(approval_id)
                self._challenges.pop(approval_id, None)
            return valid
        except (KeyError, ValueError, TypeError, json.JSONDecodeError):
            return False

    def _get_live_challenge(self, approval_id: str) -> ApprovalChallenge:
        challenge = self._challenges[approval_id]
        if challenge.expires_at < datetime.now(UTC):
            self._challenges.pop(approval_id, None)
            raise KeyError(approval_id)
        return challenge

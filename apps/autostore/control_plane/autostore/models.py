"""Typed domain model — products, orders, events, decisions, audit entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    ESCALATE = "ESCALATE"   # awaits human approval


class EventType(str, Enum):
    PRICE_RECOMMENDATION = "price_recommendation"
    REFUND_REQUEST       = "refund_request"
    AD_SPEND_REQUEST     = "ad_spend_request"
    INVENTORY_EVENT      = "inventory_event"


@dataclass(frozen=True)
class Product:
    sku: str
    title: str
    price_cents: int
    cost_cents: int
    min_price_cents: int
    inventory: int


@dataclass(frozen=True)
class Order:
    id: str
    sku: str
    qty: int
    price_cents: int
    status: str = "placed"


@dataclass(frozen=True)
class Event:
    id: int
    type: EventType
    payload: dict[str, Any]


@dataclass(frozen=True)
class PolicyConfig:
    max_discount_pct: float = 0.30
    refund_auto_max_cents: int = 5000
    ad_spend_daily_cap_cents: int = 50000


@dataclass
class ActionLogEntry:
    id: int
    event_id: int
    action: str
    decision: Decision
    reasons: list[str]
    executed: bool
    audit_ref: str
    prev_hash: str
    entry_hash: str


@dataclass
class DecisionResult:
    decision: Decision
    action: str
    reasons: list[str]
    audit_ref: str
    payload_validated: dict[str, Any] = field(default_factory=dict)
    requires_approval: bool = False

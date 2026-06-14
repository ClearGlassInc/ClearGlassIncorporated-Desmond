"""Request/response contracts (Pydantic v2)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class GenerateCopyRequest(BaseModel):
    product_slug: str
    kind: str = Field(default="description", description="description|faq|ad|email|sms")
    brand_voice: str = "clear, confident, no false claims"


class UpdatePricingRequest(BaseModel):
    sku: str
    old_price: float
    new_price: float
    reason: str = ""


class RefreshProductsRequest(BaseModel):
    source: str = "supplier_feed"
    dry_run: bool = True


class InventoryCheckRequest(BaseModel):
    reorder: bool = False


class ActionResult(BaseModel):
    """Uniform envelope returned by every governed action."""

    status: str               # executed | queued_for_approval | drafted | error
    action: str
    risk_score: int
    risk_tier: str
    requires_approval: bool
    approval_id: int | None = None
    reasons: list[str] = Field(default_factory=list)
    data: dict = Field(default_factory=dict)


class EventOut(BaseModel):
    id: int
    ts: datetime
    actor: str
    action: str
    target: str | None
    result: str
    risk_score: int
    risk_tier: str

    model_config = {"from_attributes": True}


class ApprovalOut(BaseModel):
    id: int
    action: str
    target: str | None
    risk_score: int
    risk_tier: str
    status: str
    requested_by: str
    decided_by: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DecisionRequest(BaseModel):
    decided_by: str = "human"
    note: str = ""


class MetricsOverview(BaseModel):
    revenue: float
    orders: int
    conversion_rate: float
    aov: float
    refund_rate: float
    open_approvals: int
    window_days: int

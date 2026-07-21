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


class CheckoutLineItem(BaseModel):
    name: str
    amount: int = Field(description="Unit price in the smallest currency unit (cents)", ge=0)
    quantity: int = Field(default=1, ge=1)
    currency: str = "cad"


class CheckoutRequest(BaseModel):
    items: list[CheckoutLineItem]
    customer_email: str | None = None
    success_url: str | None = None
    cancel_url: str | None = None


class CheckoutSessionOut(BaseModel):
    id: str
    url: str
    mode: str               # live | mock
    amount_total: int
    currency: str


class PayoutBankInfoOut(BaseModel):
    configured: bool
    processor: str
    settlement_mode: str
    external_account_id: str | None
    bank_name: str | None
    account_last4: str | None
    routing_hint: str | None
    country: str
    currencies: list[str]
    warnings: list[str] = Field(default_factory=list)


class PayoutOut(BaseModel):
    id: int
    stripe_payout_id: str
    amount: float
    currency: str
    status: str
    destination: str | None
    tenant_id: str | None
    arrival_date: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RefundRequest(BaseModel):
    order_id: int
    amount: int | None = Field(default=None, description="Cents to refund; None = full refund")
    reason: str = ""


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
    # Optional human-readable label only. The decider recorded on the approval and in the
    # audit ledger is the authenticated admin credential, not this field — see
    # routers/approvals.py::_resolve_decider. Kept for forensic annotation.
    decided_by: str = Field(default="human", description="Optional display label; not the trusted identity")
    note: str = ""


class MetricsOverview(BaseModel):
    revenue: float
    orders: int
    conversion_rate: float
    aov: float
    refund_rate: float
    open_approvals: int
    window_days: int

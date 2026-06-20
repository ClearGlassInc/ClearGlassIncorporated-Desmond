"""ORM models — mirrors migrations/001_init.sql.

The append-only ``events`` table is the audit ledger; ``approvals`` is the human gate.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# JSONB in Postgres, plain JSON elsewhere (SQLite for local/dev/demo runs).
PortableJSON = JSON().with_variant(JSONB(), "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Declarative base for all commerce tables."""


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True)
    title: Mapped[str] = mapped_column(String(240))
    status: Mapped[str] = mapped_column(String(32), default="draft")
    margin_pct: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Variant(Base):
    __tablename__ = "variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    sku: Mapped[str] = mapped_column(String(120), unique=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    currency: Mapped[str] = mapped_column(String(3), default="CAD")


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    consent_marketing: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    currency: Mapped[str] = mapped_column(String(3), default="CAD")
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("variants.id", ondelete="CASCADE"))
    on_hand: Mapped[int] = mapped_column(Integer, default=0)
    reorder_threshold: Mapped[int] = mapped_column(Integer, default=10)


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    channel: Mapped[str] = mapped_column(String(48))
    status: Mapped[str] = mapped_column(String(32), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContentAsset(Base):
    __tablename__ = "content_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String(48))
    body: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Event(Base):
    """Append-only audit ledger. Rows are never updated or deleted."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    actor: Mapped[str] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(80))
    target: Mapped[str | None] = mapped_column(String(160), nullable=True)
    payload: Mapped[dict] = mapped_column(PortableJSON, default=dict)
    result: Mapped[str] = mapped_column(String(32), default="ok")
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_tier: Mapped[str] = mapped_column(String(16), default="low")


class Approval(Base):
    """Human approval gate for high/critical actions."""

    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action: Mapped[str] = mapped_column(String(80))
    target: Mapped[str | None] = mapped_column(String(160), nullable=True)
    payload: Mapped[dict] = mapped_column(PortableJSON, default=dict)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_tier: Mapped[str] = mapped_column(String(16), default="high")
    status: Mapped[str] = mapped_column(String(16), default="pending")
    requested_by: Mapped[str] = mapped_column(String(120), default="operator")
    decided_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MetricsDaily(Base):
    __tablename__ = "metrics_daily"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day: Mapped[str] = mapped_column(String(10), unique=True)
    revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    orders: Mapped[int] = mapped_column(Integer, default=0)
    conversion_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0"))
    aov: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    refund_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0"))

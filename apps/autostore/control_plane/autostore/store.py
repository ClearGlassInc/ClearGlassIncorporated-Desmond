"""Source-of-truth store protocol + in-memory reference.

The control plane never reads from anywhere but a Store. In production the
implementation is Postgres; in tests it is InMemoryStore. Either way, the
engine reconciles every decision against this canonical view before allowing
execution — preventing hallucinated actions and silent drift.
"""
from __future__ import annotations

from typing import Optional, Protocol

from .models import Order, PolicyConfig, Product


class Store(Protocol):
    def get_product(self, sku: str) -> Optional[Product]: ...
    def update_price(self, sku: str, new_price_cents: int) -> Product: ...
    def get_order(self, order_id: str) -> Optional[Order]: ...
    def adjust_inventory(self, sku: str, delta: int, reason: str) -> Product: ...
    def policy(self) -> PolicyConfig: ...
    def ad_spend_today_cents(self) -> int: ...
    def record_ad_spend(self, cents: int) -> None: ...


class StoreError(Exception):
    pass


class InMemoryStore:
    """Reference implementation used by tests and the demo seed."""

    def __init__(self, *, policy: Optional[PolicyConfig] = None) -> None:
        self._products: dict[str, Product] = {}
        self._orders: dict[str, Order] = {}
        self._policy = policy or PolicyConfig()
        self._ad_spend_today: int = 0

    # --- seeding (not part of the protocol) ----------------------------------
    def seed_product(self, p: Product) -> None:
        self._products[p.sku] = p

    def seed_order(self, o: Order) -> None:
        self._orders[o.id] = o

    # --- Store protocol ------------------------------------------------------
    def get_product(self, sku: str) -> Optional[Product]:
        return self._products.get(sku)

    def update_price(self, sku: str, new_price_cents: int) -> Product:
        p = self._products.get(sku)
        if p is None:
            raise StoreError(f"unknown sku: {sku}")
        if new_price_cents < p.min_price_cents:
            # defense-in-depth — the engine should have caught this already.
            raise StoreError("price below floor (would violate pricing lock)")
        updated = Product(p.sku, p.title, int(new_price_cents), p.cost_cents,
                          p.min_price_cents, p.inventory)
        self._products[sku] = updated
        return updated

    def get_order(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)

    def adjust_inventory(self, sku: str, delta: int, reason: str) -> Product:
        p = self._products.get(sku)
        if p is None:
            raise StoreError(f"unknown sku: {sku}")
        new_inv = p.inventory + delta
        if new_inv < 0:
            raise StoreError("inventory would go negative")
        updated = Product(p.sku, p.title, p.price_cents, p.cost_cents,
                          p.min_price_cents, new_inv)
        self._products[sku] = updated
        return updated

    def policy(self) -> PolicyConfig:
        return self._policy

    def ad_spend_today_cents(self) -> int:
        return self._ad_spend_today

    def record_ad_spend(self, cents: int) -> None:
        self._ad_spend_today += int(cents)

"""Postgres-backed Store + a tiny migrations runner.

Drops in behind the ``Store`` protocol without changing the engine, policy, or
tests. ``psycopg`` is import-guarded so the module loads anywhere; the pure
helpers (``discover_migrations``, ``split_sql``) are unit-tested without a DB.
"""
from __future__ import annotations

import datetime as _dt
import pathlib
import re
from typing import Any, Optional

from .models import Order, PolicyConfig, Product
from .store import StoreError


# ---------- migrations (pure helpers, DB-free, unit-tested) ----------------

def discover_migrations(migrations_dir: str | pathlib.Path) -> list[pathlib.Path]:
    """Return .sql migration files sorted by their numeric prefix (001, 002…)."""
    d = pathlib.Path(migrations_dir)
    files = [p for p in d.glob("*.sql") if p.is_file()]

    def _key(p: pathlib.Path) -> tuple[int, str]:
        m = re.match(r"^(\d+)", p.name)
        return (int(m.group(1)) if m else 1_000_000, p.name)

    return sorted(files, key=_key)


def split_sql(text: str) -> list[str]:
    """Split a migration into individual statements (semicolon-terminated),
    ignoring blank lines and full-line comments."""
    cleaned = "\n".join(
        line for line in text.splitlines()
        if not line.strip().startswith("--")
    )
    return [s.strip() for s in cleaned.split(";") if s.strip()]


def apply_migrations(conn: Any, migrations_dir: str | pathlib.Path) -> list[str]:
    """Apply every migration in order. ``conn`` is a DB-API connection
    (psycopg). Returns the list of applied filenames."""
    applied: list[str] = []
    with conn.cursor() as cur:
        cur.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
            filename TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())""")
        cur.execute("SELECT filename FROM schema_migrations")
        done = {r[0] for r in cur.fetchall()}
        for path in discover_migrations(migrations_dir):
            if path.name in done:
                continue
            for stmt in split_sql(path.read_text()):
                cur.execute(stmt)
            cur.execute("INSERT INTO schema_migrations (filename) VALUES (%s)",
                        (path.name,))
            applied.append(path.name)
    conn.commit()
    return applied


# ---------- PostgresStore (import-guarded) ---------------------------------

class PostgresStore:
    """Implements the Store protocol against Postgres via psycopg."""

    def __init__(self, dsn: str) -> None:  # pragma: no cover - needs DB
        try:
            import psycopg  # noqa: F401
        except ImportError as exc:
            raise ImportError("PostgresStore requires the 'psycopg' package") from exc
        import psycopg
        self._conn = psycopg.connect(dsn, autocommit=True)

    def _one(self, sql: str, args: tuple) -> Optional[tuple]:  # pragma: no cover
        with self._conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchone()

    def get_product(self, sku: str) -> Optional[Product]:  # pragma: no cover
        row = self._one(
            "SELECT sku,title,price_cents,cost_cents,min_price_cents,inventory "
            "FROM products WHERE sku=%s", (sku,))
        return Product(*row) if row else None

    def update_price(self, sku: str, new_price_cents: int) -> Product:  # pragma: no cover
        p = self.get_product(sku)
        if p is None:
            raise StoreError(f"unknown sku: {sku}")
        if new_price_cents < p.min_price_cents:
            raise StoreError("price below floor (would violate pricing lock)")
        with self._conn.cursor() as cur:
            cur.execute("UPDATE products SET price_cents=%s, updated_at=now() WHERE sku=%s",
                        (int(new_price_cents), sku))
        return self.get_product(sku)  # type: ignore[return-value]

    def get_order(self, order_id: str) -> Optional[Order]:  # pragma: no cover
        row = self._one(
            "SELECT id,sku,qty,price_cents,status FROM orders WHERE id=%s", (order_id,))
        return Order(*row) if row else None

    def adjust_inventory(self, sku: str, delta: int, reason: str) -> Product:  # pragma: no cover
        p = self.get_product(sku)
        if p is None:
            raise StoreError(f"unknown sku: {sku}")
        if p.inventory + delta < 0:
            raise StoreError("inventory would go negative")
        with self._conn.cursor() as cur:
            cur.execute("UPDATE products SET inventory=inventory+%s WHERE sku=%s",
                        (int(delta), sku))
            cur.execute("INSERT INTO inventory_events (sku,delta,reason) VALUES (%s,%s,%s)",
                        (sku, int(delta), reason))
        return self.get_product(sku)  # type: ignore[return-value]

    def policy(self) -> PolicyConfig:  # pragma: no cover
        row = self._one("SELECT max_discount_pct, refund_auto_max_cents, "
                        "ad_spend_daily_cap_cents FROM policy_config WHERE id=1", ())
        return PolicyConfig(float(row[0]), int(row[1]), int(row[2])) if row else PolicyConfig()

    def ad_spend_today_cents(self) -> int:  # pragma: no cover
        row = self._one(
            "SELECT COALESCE(SUM((payload->>'amount_cents')::int),0) FROM events "
            "WHERE type='ad_spend_request' AND received_at::date = %s",
            (_dt.date.today(),))
        return int(row[0]) if row else 0

    def record_ad_spend(self, cents: int) -> None:  # pragma: no cover
        with self._conn.cursor() as cur:
            cur.execute("INSERT INTO events (type,payload) VALUES "
                        "('ad_spend_request', jsonb_build_object('amount_cents', %s))",
                        (int(cents),))

-- PERCIVAL Autostore — canonical schema (Postgres).
-- Single source of truth for products, orders, events, actions, refunds,
-- inventory, and the immutable audit ledger. Worker layer is dumb-by-design;
-- it executes only validated packets emitted by the control plane.

CREATE TABLE IF NOT EXISTS products (
    sku             TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    price_cents     INTEGER NOT NULL CHECK (price_cents >= 0),
    cost_cents      INTEGER NOT NULL CHECK (cost_cents  >= 0),
    min_price_cents INTEGER NOT NULL CHECK (min_price_cents >= cost_cents),
    inventory       INTEGER NOT NULL DEFAULT 0 CHECK (inventory >= 0),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS orders (
    id              TEXT PRIMARY KEY,
    sku             TEXT NOT NULL REFERENCES products(sku),
    qty             INTEGER NOT NULL CHECK (qty > 0),
    price_cents     INTEGER NOT NULL CHECK (price_cents >= 0),
    status          TEXT NOT NULL DEFAULT 'placed'
                    CHECK (status IN ('placed','fulfilled','refunded','cancelled')),
    placed_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS events (
    id              BIGSERIAL PRIMARY KEY,
    type            TEXT NOT NULL,             -- price_recommendation | refund_request | ad_spend_request | inventory_event
    payload         JSONB NOT NULL,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS actions_log (
    id              BIGSERIAL PRIMARY KEY,
    event_id        BIGINT REFERENCES events(id),
    action          TEXT NOT NULL,             -- e.g. price_change, refund_issue, ad_budget_set
    decision        TEXT NOT NULL              -- ALLOW | DENY | ESCALATE
                    CHECK (decision IN ('ALLOW','DENY','ESCALATE')),
    reasons         JSONB NOT NULL DEFAULT '[]'::jsonb,
    executed        BOOLEAN NOT NULL DEFAULT FALSE,
    audit_ref       TEXT NOT NULL,
    prev_hash       TEXT NOT NULL,
    entry_hash      TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_actions_log_event ON actions_log(event_id);

-- Append-only at the DB layer: revoke UPDATE / DELETE on audit-bearing tables.
REVOKE UPDATE, DELETE ON actions_log FROM PUBLIC;
REVOKE UPDATE, DELETE ON events      FROM PUBLIC;

CREATE TABLE IF NOT EXISTS approvals (
    id              BIGSERIAL PRIMARY KEY,
    action_id       BIGINT NOT NULL REFERENCES actions_log(id),
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','approved','denied')),
    approver        TEXT,
    decided_at      TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS refunds (
    id              BIGSERIAL PRIMARY KEY,
    order_id        TEXT NOT NULL REFERENCES orders(id),
    amount_cents    INTEGER NOT NULL CHECK (amount_cents > 0),
    reason          TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','issued','denied')),
    audit_ref       TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS inventory_events (
    id              BIGSERIAL PRIMARY KEY,
    sku             TEXT NOT NULL REFERENCES products(sku),
    delta           INTEGER NOT NULL,           -- can be negative
    reason          TEXT NOT NULL,
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS policy_config (
    id              INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    -- pricing lock: floor = min_price_cents (per product); also block discounts > X%
    max_discount_pct        NUMERIC NOT NULL DEFAULT 0.30,
    -- refund gate: above this needs human approval
    refund_auto_max_cents   INTEGER NOT NULL DEFAULT 5000,
    -- ad spend cap (daily, dollars)
    ad_spend_daily_cap_cents INTEGER NOT NULL DEFAULT 50000,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
INSERT INTO policy_config (id) VALUES (1) ON CONFLICT DO NOTHING;

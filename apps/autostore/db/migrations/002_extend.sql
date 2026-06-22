-- PERCIVAL Autostore — schema extension (phase 3).
-- Layers customer / campaign / support / refund-request / risk onto the core
-- without changing the control logic. All amounts in integer cents.

CREATE TABLE IF NOT EXISTS customers (
    id              TEXT PRIMARY KEY,
    email_hash      TEXT NOT NULL,                 -- never store raw PII; hash only
    lifetime_cents  INTEGER NOT NULL DEFAULT 0 CHECK (lifetime_cents >= 0),
    risk_flags      JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS campaigns (
    id                 TEXT PRIMARY KEY,
    channel            TEXT NOT NULL,              -- search | social | email | display
    daily_budget_cents INTEGER NOT NULL CHECK (daily_budget_cents >= 0),
    spent_today_cents  INTEGER NOT NULL DEFAULT 0 CHECK (spent_today_cents >= 0),
    status             TEXT NOT NULL DEFAULT 'active'
                       CHECK (status IN ('active','paused','archived')),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);

CREATE TABLE IF NOT EXISTS support_tickets (
    id              TEXT PRIMARY KEY,
    customer_id     TEXT REFERENCES customers(id),
    order_id        TEXT REFERENCES orders(id),
    subject         TEXT NOT NULL,
    priority        TEXT NOT NULL DEFAULT 'normal'
                    CHECK (priority IN ('low','normal','high','urgent')),
    status          TEXT NOT NULL DEFAULT 'open'
                    CHECK (status IN ('open','pending','resolved','closed')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON support_tickets(status);

CREATE TABLE IF NOT EXISTS refund_requests (
    id              BIGSERIAL PRIMARY KEY,
    order_id        TEXT NOT NULL REFERENCES orders(id),
    customer_id     TEXT REFERENCES customers(id),
    amount_cents    INTEGER NOT NULL CHECK (amount_cents > 0),
    reason          TEXT NOT NULL,
    risk_score      NUMERIC NOT NULL DEFAULT 0 CHECK (risk_score >= 0 AND risk_score <= 1),
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','approved','denied','issued')),
    audit_ref       TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_refund_requests_status ON refund_requests(status);

-- Idempotency: the control plane dedupes events by key so retries are safe.
CREATE TABLE IF NOT EXISTS idempotency_keys (
    key             TEXT PRIMARY KEY,
    event_id        BIGINT REFERENCES events(id),
    decision        TEXT NOT NULL,
    audit_ref       TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Risk on every action: store the computed score + factors alongside the log.
ALTER TABLE actions_log ADD COLUMN IF NOT EXISTS risk_score NUMERIC NOT NULL DEFAULT 0;
ALTER TABLE actions_log ADD COLUMN IF NOT EXISTS risk_band  TEXT   NOT NULL DEFAULT 'LOW';
ALTER TABLE actions_log ADD COLUMN IF NOT EXISTS risk_factors JSONB NOT NULL DEFAULT '[]'::jsonb;

REVOKE UPDATE, DELETE ON refund_requests   FROM PUBLIC;
REVOKE UPDATE, DELETE ON idempotency_keys  FROM PUBLIC;

-- ClearGlass Commerce — order line items (Postgres).
--
-- An order recorded a total and nothing about *what* was bought, so no supplier
-- could be told what to make. This is the missing link between a paid order and
-- a fulfillable one.
--
-- `printful_sync_variant_id` is captured per line rather than resolved later:
-- the price book is editable, and an order must be fulfilled as it was sold.

CREATE TABLE IF NOT EXISTS order_items (
    id                       SERIAL PRIMARY KEY,
    order_id                 INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    sku                      VARCHAR(120) NOT NULL,
    name                     VARCHAR(240),
    quantity                 INTEGER NOT NULL DEFAULT 1,
    unit_amount              INTEGER,
    currency                 VARCHAR(3) NOT NULL DEFAULT 'CAD',
    requires_shipping        BOOLEAN NOT NULL DEFAULT FALSE,
    printful_sync_variant_id INTEGER,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);

-- Payment webhooks are redelivered; without this a retry appends a second copy
-- of every line and the order looks twice as large as it was.
CREATE UNIQUE INDEX IF NOT EXISTS idx_order_items_order_sku
    ON order_items(order_id, sku);

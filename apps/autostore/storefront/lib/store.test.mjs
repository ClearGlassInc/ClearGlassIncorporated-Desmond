// ClearGlass Side Store — smoke tests for the pricing + checkout core.
// Run with:  node --test apps/autostore/storefront/lib/
// No external deps; reads the seed catalog from disk.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import {
  priceCart,
  bundleDiscountRate,
  MAX_DISCOUNT_RATE,
  FREE_SHIP_THRESHOLD_CENTS,
} from "./pricing.mjs";
import { buildCheckoutSessionParams } from "./checkout.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const catalog = JSON.parse(
  readFileSync(join(HERE, "..", "data", "catalog.json"), "utf8")
).items;

test("catalog has 50+ SKUs, all valid and cheap", () => {
  assert.ok(catalog.length >= 50, `expected 50+ SKUs, got ${catalog.length}`);
  const ids = new Set();
  for (const it of catalog) {
    assert.ok(it.id && it.sku && it.name && it.category, `missing fields: ${it.sku}`);
    assert.equal(it.currency, "CAD");
    assert.ok(it.price > 0 && it.price <= 10, `price out of range: ${it.sku} ${it.price}`);
    assert.ok(!ids.has(it.id), `duplicate id: ${it.id}`);
    ids.add(it.id);
  }
});

test("bundle discount tiers respect the 15% cap", () => {
  assert.equal(bundleDiscountRate(1), 0);
  assert.equal(bundleDiscountRate(2), 0);
  assert.equal(bundleDiscountRate(3), 0.1);
  assert.equal(bundleDiscountRate(4), 0.1);
  assert.equal(bundleDiscountRate(5), 0.15);
  assert.equal(bundleDiscountRate(50), 0.15);
  assert.ok(bundleDiscountRate(999) <= MAX_DISCOUNT_RATE);
});

test("single cheap item pays flat shipping + HST", () => {
  const id = catalog[0].id;
  const p = priceCart([{ id, qty: 1 }], catalog);
  assert.equal(p.discountCents, 0);
  assert.ok(p.shippingCents > 0, "small order should pay shipping");
  assert.ok(p.taxCents > 0, "HST should apply");
  assert.equal(p.totalCents, p.subtotalCents + p.shippingCents + p.taxCents);
});

test("3 items trigger a 10% bundle discount", () => {
  const id = catalog[0].id;
  const p = priceCart([{ id, qty: 3 }], catalog);
  assert.equal(p.discountPercent, 10);
  assert.equal(p.discountCents, Math.round(p.subtotalCents * 0.1));
});

test("large order earns free shipping and 15% cap", () => {
  // 5x the most expensive item clears the free-ship threshold post-discount.
  const dear = [...catalog].sort((a, b) => b.price - a.price)[0];
  const p = priceCart([{ id: dear.id, qty: 5 }], catalog);
  assert.equal(p.discountPercent, 15);
  assert.ok(p.subtotalCents - p.discountCents >= FREE_SHIP_THRESHOLD_CENTS);
  assert.equal(p.shippingCents, 0, "should be free shipping");
  assert.ok(p.freeShipping);
});

test("empty / unknown lines price to zero and never crash", () => {
  assert.equal(priceCart([], catalog).totalCents, 0);
  assert.equal(priceCart([{ id: "nope", qty: 3 }], catalog).totalCents, 0);
  assert.equal(priceCart([{ id: catalog[0].id, qty: 0 }], catalog).totalCents, 0);
});

test("checkout params are well-formed and secret-free", () => {
  const id = catalog[0].id;
  const params = buildCheckoutSessionParams(
    [{ id, qty: 3 }],
    catalog,
    { successUrl: "https://x/ok", cancelUrl: "https://x/no" }
  );
  assert.equal(params.mode, "payment");
  assert.equal(params.line_items.length, 1);
  assert.equal(params.line_items[0].quantity, 3);
  assert.equal(params.line_items[0].price_data.currency, "cad");
  assert.equal(params.discountPercent, 10);
  assert.ok(params.shipping_options.length === 1);
  assert.ok(!JSON.stringify(params).toLowerCase().includes("sk_"), "no secret key leak");
});

test("empty cart cannot create a checkout session", () => {
  assert.throws(() =>
    buildCheckoutSessionParams([], catalog, { successUrl: "a", cancelUrl: "b" })
  );
});

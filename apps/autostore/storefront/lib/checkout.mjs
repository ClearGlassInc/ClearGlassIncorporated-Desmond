// ClearGlass Side Store — pure Stripe Checkout params builder.
// Returns the object we would hand to stripe.checkout.sessions.create(), with
// no Stripe SDK call here so it stays unit-testable and secret-free. The API
// route (app/api/checkout/route.ts) injects the SDK and the discount coupon.

import { priceCart, CURRENCY, FLAT_SHIP_CENTS, FREE_SHIP_THRESHOLD_CENTS } from "./pricing.mjs";

/**
 * @param {Array<{id:string, qty:number}>} lines
 * @param {Array<object>} catalog
 * @param {{successUrl:string, cancelUrl:string}} urls
 */
export function buildCheckoutSessionParams(lines, catalog, urls) {
  const priced = priceCart(lines, catalog);
  if (priced.lines.length === 0) {
    throw new Error("Cannot create a checkout session for an empty cart.");
  }

  const line_items = priced.lines.map((l) => ({
    quantity: l.qty,
    price_data: {
      currency: CURRENCY.toLowerCase(),
      unit_amount: l.unit,
      product_data: { name: l.name, metadata: { sku_id: l.id } },
    },
  }));

  const shipping_options = [
    {
      shipping_rate_data: {
        type: "fixed_amount",
        display_name: priced.shippingCents === 0 ? "Free shipping" : "Standard shipping",
        fixed_amount: { amount: priced.shippingCents, currency: CURRENCY.toLowerCase() },
      },
    },
  ];

  return {
    mode: "payment",
    success_url: urls.successUrl,
    cancel_url: urls.cancelUrl,
    line_items,
    shipping_options,
    // The route turns a non-zero discountPercent into a one-time Stripe coupon.
    discountPercent: priced.discountPercent,
    metadata: {
      item_count: String(priced.itemCount),
      subtotal_cents: String(priced.subtotalCents),
      total_cents: String(priced.totalCents),
      free_ship_threshold_cents: String(FREE_SHIP_THRESHOLD_CENTS),
      flat_ship_cents: String(FLAT_SHIP_CENTS),
    },
  };
}

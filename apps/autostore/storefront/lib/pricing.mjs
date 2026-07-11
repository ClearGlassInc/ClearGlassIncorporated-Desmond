// ClearGlass Side Store — pure pricing engine (dependency-free ESM).
// Encodes the SOUL.md pricing rules so the storefront and the checkout API
// share one source of truth. All math is in integer cents to avoid float drift.

export const CURRENCY = "CAD";
export const FREE_SHIP_THRESHOLD_CENTS = 2500; // free shipping at CAD $25
export const FLAT_SHIP_CENTS = 499; // CAD $4.99 under the threshold
export const TAX_RATE = 0.13; // Ontario HST
export const MAX_DISCOUNT_RATE = 0.15; // hard cap from SOUL.md

/** Bundle discount by total item quantity. Never exceeds MAX_DISCOUNT_RATE. */
export function bundleDiscountRate(totalQty) {
  let rate = 0;
  if (totalQty >= 5) rate = 0.15;
  else if (totalQty >= 3) rate = 0.1;
  return Math.min(rate, MAX_DISCOUNT_RATE);
}

export function toCents(price) {
  return Math.round(Number(price) * 100);
}

export function formatCad(cents) {
  return `$${(cents / 100).toFixed(2)}`;
}

/**
 * Price a cart.
 * @param {Array<{id:string, qty:number}>} lines
 * @param {Array<object>} catalog  items with {id, price}
 * @returns structured breakdown in cents + formatted dollars
 */
export function priceCart(lines, catalog) {
  const byId = new Map(catalog.map((it) => [it.id, it]));
  const resolved = [];
  let subtotal = 0;
  let totalQty = 0;

  for (const line of lines || []) {
    const item = byId.get(line.id);
    const qty = Math.max(0, Math.floor(Number(line.qty) || 0));
    if (!item || qty === 0) continue;
    const unit = toCents(item.price);
    const lineTotal = unit * qty;
    subtotal += lineTotal;
    totalQty += qty;
    resolved.push({ id: item.id, name: item.name, unit, qty, lineTotal });
  }

  const rate = bundleDiscountRate(totalQty);
  const discount = Math.round(subtotal * rate);
  const discountedSubtotal = subtotal - discount;
  const shipping =
    resolved.length > 0 && discountedSubtotal < FREE_SHIP_THRESHOLD_CENTS
      ? FLAT_SHIP_CENTS
      : 0;
  const tax = Math.round((discountedSubtotal + shipping) * TAX_RATE);
  const total = discountedSubtotal + shipping + tax;

  return {
    currency: CURRENCY,
    lines: resolved,
    itemCount: totalQty,
    discountRate: rate,
    discountPercent: Math.round(rate * 100),
    subtotalCents: subtotal,
    discountCents: discount,
    shippingCents: shipping,
    taxCents: tax,
    totalCents: total,
    freeShipping: shipping === 0 && resolved.length > 0,
    display: {
      subtotal: formatCad(subtotal),
      discount: formatCad(discount),
      shipping: shipping === 0 ? "FREE" : formatCad(shipping),
      tax: formatCad(tax),
      total: formatCad(total),
    },
  };
}

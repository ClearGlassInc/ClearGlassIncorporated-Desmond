// Display catalog for the storefront.
//
// These entries drive what the shopper *sees*. They do not drive what they are
// *charged*: `slug` doubles as the price-book SKU, and the control plane resolves
// the amount server-side from `app/data/pricebook.json` at checkout. Keep the
// amounts here in step with that file — if they ever drift, the price book wins and
// the customer is charged the governed amount.
export interface Product {
  slug: string; // also the price-book SKU
  title: string;
  amount: number; // unit price in cents — display only
  currency: string;
  blurb: string;
  interval?: "month"; // set when the offer recurs
  note?: string; // deposit / scoping caveats shown next to the price
}

export const CATALOG: Product[] = [
  {
    slug: "quick-audit",
    title: "Security Quick-Audit",
    amount: 24900,
    currency: "cad",
    blurb:
      "Fixed-scope security review of your Microsoft 365 and Windows estate, delivered as a prioritised findings report.",
  },
  {
    slug: "hardening",
    title: "M365 + Windows Hardening Sprint",
    amount: 250000,
    currency: "cad",
    blurb:
      "Close the gaps the audit found — identity, endpoint and tenant hardening, executed and documented.",
    note: "Deposit. Final fixed fee confirmed on a scoping call.",
  },
  {
    slug: "phipa",
    title: "PHIPA Readiness",
    amount: 300000,
    currency: "cad",
    blurb:
      "Readiness assessment against Ontario's PHIPA obligations, with a remediation plan you can hand to an auditor.",
    note: "Deposit. Final fixed fee confirmed on a scoping call.",
  },
  {
    slug: "monitoring",
    title: "Managed Monitoring",
    amount: 60000,
    currency: "cad",
    blurb: "Ongoing managed monitoring and alert triage. Cancel any time.",
    interval: "month",
  },
];

export function findProduct(slug: string): Product | undefined {
  return CATALOG.find((p) => p.slug === slug);
}

export function formatPrice(amount: number, currency: string): string {
  return `${currency.toUpperCase()} $${(amount / 100).toFixed(2)}`;
}

// Price as shown to the shopper, including the billing interval for subscriptions.
export function formatOfferPrice(product: Product): string {
  const base = formatPrice(product.amount, product.currency);
  return product.interval ? `${base} / ${product.interval}` : base;
}

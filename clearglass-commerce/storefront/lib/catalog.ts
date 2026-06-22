// Shared product catalog for the storefront scaffold.
//
// In production these come from the commerce control plane (governed, audited
// product + pricing records). The scaffold ships a small static catalog so the
// storefront builds and the checkout flow works end-to-end without a live API.
// Prices are in the smallest currency unit (cents) to match the Stripe / control
// plane checkout shape.
export interface Product {
  slug: string;
  title: string;
  amount: number; // unit price in cents
  currency: string;
  blurb: string;
}

export const CATALOG: Product[] = [
  {
    slug: "aurora-desk-lamp",
    title: "Aurora LED Desk Lamp",
    amount: 4900,
    currency: "cad",
    blurb: "Warm-to-cool tunable desk lamp with a brushed-aluminium arm.",
  },
  {
    slug: "summit-water-bottle",
    title: "Summit Insulated Bottle",
    amount: 3400,
    currency: "cad",
    blurb: "Double-walled vacuum bottle that holds temperature for 24 hours.",
  },
];

export function findProduct(slug: string): Product | undefined {
  return CATALOG.find((p) => p.slug === slug);
}

export function formatPrice(amount: number, currency: string): string {
  return `${currency.toUpperCase()} $${(amount / 100).toFixed(2)}`;
}

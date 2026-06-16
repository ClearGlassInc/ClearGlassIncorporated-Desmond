// Thin client for the commerce control plane.
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status}`);
  }
  return (await res.json()) as T;
}

export interface MetricsOverview {
  revenue: number;
  orders: number;
  conversion_rate: number;
  aov: number;
  refund_rate: number;
  open_approvals: number;
  window_days: number;
}

export interface CheckoutLineItem {
  name: string;
  amount: number; // unit price in cents
  quantity?: number;
  currency?: string;
}

export interface CheckoutSession {
  id: string;
  url: string;
  mode: string; // "live" | "mock"
  amount_total: number;
  currency: string;
}

// Create a checkout session via the control plane. Returns a live Stripe
// Checkout URL when STRIPE_SECRET_KEY is configured, or a deterministic mock
// session URL otherwise — so the buy flow works in every environment.
export async function createCheckout(
  items: CheckoutLineItem[],
  customerEmail?: string,
): Promise<CheckoutSession> {
  return api<CheckoutSession>("/checkout/session", {
    method: "POST",
    body: JSON.stringify({ items, customer_email: customerEmail ?? null }),
  });
}

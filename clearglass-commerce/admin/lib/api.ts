// Admin client for the commerce control plane.
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

export interface Approval {
  id: number;
  action: string;
  target: string | null;
  risk_score: number;
  risk_tier: string;
  status: string;
  requested_by: string;
  created_at: string;
}

// Server-only fetch wrapper for the control plane. Keeps tokens off the client.
const BASE = process.env.AUTOSTORE_API_URL || "http://control_plane:8000";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    throw new Error(`control-plane ${path} -> ${res.status}`);
  }
  return res.json() as Promise<T>;
}

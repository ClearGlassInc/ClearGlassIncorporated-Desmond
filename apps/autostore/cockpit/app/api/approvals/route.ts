// Server-side proxy: approve/deny an item on the control plane.
// The approver token never reaches the control plane from the browser directly —
// it is forwarded here as the X-Approver-Token header (role auth).
import { NextRequest, NextResponse } from "next/server";

const BASE = process.env.AUTOSTORE_API_URL || "http://control_plane:8000";

export async function POST(req: NextRequest) {
  let body: { id?: number; action?: string; token?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "invalid json" }, { status: 400 });
  }
  const { id, action, token } = body;
  if (!id || (action !== "approve" && action !== "deny")) {
    return NextResponse.json({ error: "id and action=approve|deny required" }, { status: 400 });
  }
  if (!token) {
    return NextResponse.json({ error: "approver token required" }, { status: 401 });
  }
  const res = await fetch(`${BASE}/v1/approvals/${id}/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Approver-Token": token },
    cache: "no-store",
  });
  const data = await res.json().catch(() => ({}));
  return NextResponse.json(data, { status: res.status });
}

"use client";
import { useEffect, useState } from "react";

export function ApproverToken() {
  const [token, setToken] = useState("");
  useEffect(() => { setToken(localStorage.getItem("approverToken") || ""); }, []);
  return (
    <div style={{ marginBottom: 12, display: "flex", gap: 8, alignItems: "center" }}>
      <span style={{ fontSize: 12, color: "var(--dim)" }}>Approver token:</span>
      <input
        value={token}
        placeholder="X-Approver-Token (role auth)"
        onChange={(e) => { setToken(e.target.value); localStorage.setItem("approverToken", e.target.value); }}
        style={{ background: "rgba(0,0,0,.3)", border: "1px solid var(--line)", color: "var(--txt)", borderRadius: 8, padding: "6px 10px", fontSize: 12, minWidth: 260 }}
      />
    </div>
  );
}

export function ApprovalActions({ id }: { id: number }) {
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function act(action: "approve" | "deny") {
    setBusy(true); setMsg(null);
    const token = localStorage.getItem("approverToken") || "";
    const res = await fetch("/api/approvals", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, action, token }),
    });
    const data = await res.json().catch(() => ({}));
    if (res.ok) { setMsg(`${action} ✓ ${data.audit_ref ?? ""}`); setTimeout(() => location.reload(), 700); }
    else { setMsg(`✗ ${data.detail ?? data.error ?? res.status}`); }
    setBusy(false);
  }

  return (
    <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
      <button disabled={busy} onClick={() => act("approve")}
        style={{ cursor: "pointer", borderRadius: 7, padding: "5px 10px", fontSize: 12,
          border: "1px solid rgba(52,211,153,.5)", color: "#34d399", background: "rgba(52,211,153,.1)" }}>
        Approve
      </button>
      <button disabled={busy} onClick={() => act("deny")}
        style={{ cursor: "pointer", borderRadius: 7, padding: "5px 10px", fontSize: 12,
          border: "1px solid rgba(255,60,80,.5)", color: "#ff3c50", background: "rgba(255,60,80,.1)" }}>
        Deny
      </button>
      {msg && <span style={{ fontSize: 11, color: "var(--dim)" }}>{msg}</span>}
    </div>
  );
}

// The human approval gate. High/critical actions land here and execute only when approved.
import { api, type Approval } from "../../lib/api";

async function getApprovals(): Promise<Approval[]> {
  try {
    return await api<Approval[]>("/approvals?status=pending");
  } catch {
    return [];
  }
}

export default async function ApprovalsPage() {
  const approvals = await getApprovals();
  return (
    <section>
      <h1 style={{ fontSize: 30 }}>Pending approvals</h1>
      <p style={{ color: "#9aa6c8" }}>
        Pricing, payments, refunds, fulfillment and reorders are gated. Nothing here has executed.
      </p>
      {approvals.length === 0 ? (
        <p style={{ color: "#5f6a8a", fontFamily: "monospace", marginTop: 18 }}>
          No pending approvals.
        </p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 18 }}>
          <thead>
            <tr style={{ textAlign: "left", color: "#9aa6c8", fontSize: 12 }}>
              <th style={{ padding: 8 }}>#</th>
              <th style={{ padding: 8 }}>Action</th>
              <th style={{ padding: 8 }}>Target</th>
              <th style={{ padding: 8 }}>Risk</th>
              <th style={{ padding: 8 }}>Requested by</th>
            </tr>
          </thead>
          <tbody>
            {approvals.map((a) => (
              <tr key={a.id} style={{ borderTop: "1px solid rgba(124,150,255,.12)" }}>
                <td style={{ padding: 8 }}>{a.id}</td>
                <td style={{ padding: 8 }}>{a.action}</td>
                <td style={{ padding: 8 }}>{a.target ?? "—"}</td>
                <td style={{ padding: 8 }}>
                  {a.risk_tier} ({a.risk_score})
                </td>
                <td style={{ padding: 8 }}>{a.requested_by}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

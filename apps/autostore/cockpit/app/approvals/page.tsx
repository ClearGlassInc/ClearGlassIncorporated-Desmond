import { api } from "@/lib/api";

type Pending = {
  id: number; event_id: number; event_type: string; payload: Record<string, any>;
  action: string; reasons: string[]; audit_ref: string;
};

export default async function ApprovalsPage() {
  let rows: Pending[] = [];
  let err: string | null = null;
  try { rows = await api<Pending[]>("/v1/approvals/pending"); }
  catch (e: any) { err = e?.message ?? "control plane unreachable"; }

  return (
    <section className="cg-card">
      <h2>Pending approvals</h2>
      {err && <div className="empty">⚠ {err}</div>}
      {!err && rows.length === 0 && <div className="empty">No pending approvals.</div>}
      {!err && rows.length > 0 && (
        <table>
          <thead><tr><th>#</th><th>Event</th><th>Action</th><th>Payload</th><th>Reasons</th><th>Audit</th></tr></thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.id}>
                <td>{r.id}</td>
                <td>{r.event_type} #{r.event_id}</td>
                <td>{r.action}</td>
                <td><code>{JSON.stringify(r.payload)}</code></td>
                <td>{r.reasons.join("; ")}</td>
                <td><code>{r.audit_ref}</code></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <div className="empty" style={{ marginTop: 12 }}>
        Approve/deny via the control plane API: <code>POST /v1/approvals/&lt;id&gt;/approve</code> or <code>/deny</code> with {"{ approver }"}. Read-first cockpit by design.
      </div>
    </section>
  );
}

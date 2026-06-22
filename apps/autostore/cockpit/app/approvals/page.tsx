import { api } from "@/lib/api";
import { ApprovalActions, ApproverToken } from "./actions";

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
      <ApproverToken />
      {err && <div className="empty">⚠ {err}</div>}
      {!err && rows.length === 0 && <div className="empty">No pending approvals.</div>}
      {!err && rows.length > 0 && (
        <table>
          <thead><tr><th>#</th><th>Event</th><th>Action</th><th>Payload</th><th>Reasons</th><th>Decide</th></tr></thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.id}>
                <td>{r.id}</td>
                <td>{r.event_type} #{r.event_id}</td>
                <td>{r.action}</td>
                <td><code>{JSON.stringify(r.payload)}</code></td>
                <td>{r.reasons.join("; ")}</td>
                <td><ApprovalActions id={r.id} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <div className="empty" style={{ marginTop: 12 }}>
        Approvals require a valid <code>X-Approver-Token</code> (role auth). Demo tokens:
        <code> demo-ops-token</code> (ops-lead), <code>demo-fin-token</code> (finance-lead).
      </div>
    </section>
  );
}

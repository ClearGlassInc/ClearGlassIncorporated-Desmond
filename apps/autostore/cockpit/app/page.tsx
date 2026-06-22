import { api } from "@/lib/api";

type AuditRow = {
  id: number; event_id: number; action: string; decision: string;
  reasons: string[]; executed: boolean; audit_ref: string;
};

function pill(d: string) {
  const cls = d === "ALLOW" ? "pill-allow" : d === "DENY" ? "pill-deny" : "pill-escalate";
  return <span className={`pill ${cls}`}>{d}</span>;
}

export default async function DecisionsPage() {
  let rows: AuditRow[] = [];
  let err: string | null = null;
  try { rows = await api<AuditRow[]>("/v1/audit?limit=50"); }
  catch (e: any) { err = e?.message ?? "control plane unreachable"; }

  return (
    <>
      <section className="cg-card">
        <h2>Recent decisions</h2>
        {err && <div className="empty">⚠ {err}</div>}
        {!err && rows.length === 0 && <div className="empty">No decisions yet. Post an event to <code>/v1/events</code>.</div>}
        {!err && rows.length > 0 && (
          <table>
            <thead><tr><th>#</th><th>Event</th><th>Action</th><th>Decision</th><th>Executed</th><th>Reasons</th><th>Audit</th></tr></thead>
            <tbody>
              {rows.slice().reverse().map(r => (
                <tr key={r.id}>
                  <td>{r.id}</td><td>{r.event_id}</td><td>{r.action}</td>
                  <td>{pill(r.decision)}</td>
                  <td>{r.executed ? "✓" : "—"}</td>
                  <td>{r.reasons.join("; ")}</td>
                  <td><code>{r.audit_ref}</code></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </>
  );
}

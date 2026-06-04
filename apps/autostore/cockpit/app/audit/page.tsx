import { api } from "@/lib/api";

type Row = {
  id: number; event_id: number; action: string; decision: string;
  reasons: string[]; executed: boolean; audit_ref: string;
  prev_hash: string; entry_hash: string;
};

export default async function AuditPage() {
  let rows: Row[] = [];
  let err: string | null = null;
  try { rows = await api<Row[]>("/v1/audit?limit=200"); }
  catch (e: any) { err = e?.message ?? "control plane unreachable"; }

  return (
    <section className="cg-card">
      <h2>Hash-chained audit ledger</h2>
      {err && <div className="empty">⚠ {err}</div>}
      {!err && rows.length === 0 && <div className="empty">Ledger empty.</div>}
      {!err && rows.length > 0 && (
        <table>
          <thead><tr><th>#</th><th>Action</th><th>Decision</th><th>Audit ref</th><th>Prev hash</th><th>Entry hash</th></tr></thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.id}>
                <td>{r.id}</td><td>{r.action}</td><td>{r.decision}</td>
                <td><code>{r.audit_ref}</code></td>
                <td><code>{r.prev_hash.slice(0, 10)}…</code></td>
                <td><code>{r.entry_hash.slice(0, 10)}…</code></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

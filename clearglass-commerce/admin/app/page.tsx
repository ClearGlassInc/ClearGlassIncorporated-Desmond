// Admin overview — pulls KPI snapshot from the control plane at request time.
import { api, type MetricsOverview } from "../lib/api";

interface Overview extends MetricsOverview {}

async function getOverview(): Promise<Overview | null> {
  try {
    return await api<Overview>("/metrics/overview");
  } catch {
    return null;
  }
}

export default async function Page() {
  const m = await getOverview();
  return (
    <section>
      <h1 style={{ fontSize: 30 }}>Store overview</h1>
      {!m ? (
        <p style={{ color: "#9aa6c8" }}>
          Control plane unreachable. Start it at <code>http://localhost:8000</code>.
        </p>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))",
            gap: 14,
            marginTop: 18,
          }}
        >
          <Stat label="Revenue" value={`$${m.revenue}`} />
          <Stat label="Orders" value={`${m.orders}`} />
          <Stat label="Conversion" value={`${(m.conversion_rate * 100).toFixed(2)}%`} />
          <Stat label="AOV" value={`$${m.aov}`} />
          <Stat label="Refund rate" value={`${(m.refund_rate * 100).toFixed(2)}%`} />
          <Stat label="Open approvals" value={`${m.open_approvals}`} />
        </div>
      )}
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        border: "1px solid rgba(124,150,255,.16)",
        borderRadius: 12,
        padding: 16,
        background: "rgba(12,16,38,.6)",
      }}
    >
      <div style={{ fontSize: 24, fontWeight: 800, color: "#a78bfa" }}>{value}</div>
      <div style={{ fontSize: 12, color: "#9aa6c8", marginTop: 4 }}>{label}</div>
    </div>
  );
}

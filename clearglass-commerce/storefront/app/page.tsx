// Public storefront home. In production this lists products from the control plane;
// the scaffold renders a static demo grid so it builds without a live API.
const DEMO = [
  { slug: "aurora-desk-lamp", title: "Aurora LED Desk Lamp", price: "CAD $49" },
  { slug: "summit-water-bottle", title: "Summit Insulated Bottle", price: "CAD $34" },
];

export default function Home() {
  return (
    <section>
      <h1 style={{ fontSize: 34 }}>Shop the collection</h1>
      <p style={{ color: "#9aa6c8" }}>
        Storefront powered by the ClearGlass commerce control plane. Pricing and copy changes are
        governed and audited.
      </p>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill,minmax(240px,1fr))",
          gap: 16,
          marginTop: 24,
        }}
      >
        {DEMO.map((p) => (
          <a
            key={p.slug}
            href={`/products/${p.slug}`}
            style={{
              border: "1px solid rgba(124,150,255,.16)",
              borderRadius: 14,
              padding: 20,
              textDecoration: "none",
              color: "inherit",
              background: "rgba(12,16,38,.6)",
            }}
          >
            <div style={{ fontWeight: 600 }}>{p.title}</div>
            <div style={{ color: "#a78bfa", marginTop: 8 }}>{p.price}</div>
          </a>
        ))}
      </div>
    </section>
  );
}

// Public storefront home. In production this lists products from the control
// plane; the scaffold renders the shared static catalog so it builds without a
// live API and stays in sync with the checkout pricing.
import { CATALOG, formatPrice } from "@/lib/catalog";

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
        {CATALOG.map((p) => (
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
            <div style={{ color: "#a78bfa", marginTop: 8 }}>{formatPrice(p.amount, p.currency)}</div>
          </a>
        ))}
      </div>
    </section>
  );
}

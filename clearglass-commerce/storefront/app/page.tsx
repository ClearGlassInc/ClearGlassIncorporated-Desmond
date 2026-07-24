// Public storefront home. In production this lists products from the control
// plane; the scaffold renders the shared static catalog so it builds without a
// live API and stays in sync with the checkout pricing.
import { CATALOG, formatPrice } from "@/lib/catalog";
import { AddToCart } from "@/lib/AddToCart";

export default function Home() {
  return (
    <section>
      <h1 className="neon-text-primary" style={{ fontSize: 34 }}>
        Shop the collection
      </h1>
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
          <div
            key={p.slug}
            className="neon-card"
            style={{
              padding: 20,
              display: "flex",
              flexDirection: "column",
            }}
          >
            <a
              href={`/products/${p.slug}`}
              style={{ textDecoration: "none", color: "inherit" }}
            >
              <div style={{ fontWeight: 600 }}>{p.title}</div>
              <div style={{ color: "#9aa6c8", fontSize: 13, marginTop: 6, lineHeight: 1.5 }}>
                {p.blurb}
              </div>
              <div className="neon-text-secondary" style={{ marginTop: 8 }}>
                {formatPrice(p.amount, p.currency)}
              </div>
            </a>
            <AddToCart product={p} block />
          </div>
        ))}
      </div>
    </section>
  );
}

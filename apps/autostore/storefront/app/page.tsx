import catalogData from "../data/catalog.json";
// @ts-expect-error — shared dependency-free ESM core (allowJs enabled).
import { formatCad, toCents } from "../lib/pricing.mjs";

type Item = {
  id: string;
  sku: string;
  name: string;
  category: string;
  price: number;
  description: string;
};

const catalog = (catalogData as { items: Item[] }).items;

export default function StorefrontPage() {
  const categories = [...new Set(catalog.map((i) => i.category))];
  return (
    <main style={{ maxWidth: 1080, margin: "0 auto", padding: "32px 20px" }}>
      <h1>ClearGlass Side Store</h1>
      <p style={{ color: "#94a0c0" }}>
        Cheap wires &amp; electronics. Bundle 3+ items for 10% off (5+ for 15%). Free shipping over
        CAD $25.
      </p>
      {categories.map((cat) => (
        <section key={cat}>
          <h2 style={{ fontSize: 16, marginTop: 28 }}>{cat}</h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
              gap: 12,
            }}
          >
            {catalog
              .filter((i) => i.category === cat)
              .map((i) => (
                <article
                  key={i.id}
                  style={{
                    border: "1px solid rgba(124,150,255,.18)",
                    borderRadius: 12,
                    padding: 14,
                  }}
                >
                  <div style={{ fontWeight: 700 }}>{i.name}</div>
                  <div style={{ fontSize: 12, color: "#94a0c0", margin: "4px 0 8px" }}>
                    {i.description}
                  </div>
                  <div style={{ fontFamily: "monospace" }}>{formatCad(toCents(i.price))}</div>
                </article>
              ))}
          </div>
        </section>
      ))}
    </main>
  );
}

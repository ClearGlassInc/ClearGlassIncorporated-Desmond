import type { ReactNode } from "react";

export const metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3001"),
  title: "ClearGlass Commerce — Admin Cockpit",
  description: "Orders, products, inventory, analytics, and the approval gate.",
  alternates: { canonical: "/" },
  openGraph: {
    title: "ClearGlass Commerce — Admin Cockpit",
    description: "Orders, products, inventory, analytics, and the approval gate.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          fontFamily: "Inter, system-ui, sans-serif",
          background: "#070a14",
          color: "#eef2ff",
        }}
      >
        <nav
          style={{
            display: "flex",
            gap: 18,
            padding: "14px 24px",
            borderBottom: "1px solid rgba(124,150,255,.16)",
          }}
        >
          <strong>Admin Cockpit</strong>
          <a href="/" style={{ color: "#9fc4ff" }}>
            Overview
          </a>
          <a href="/approvals" style={{ color: "#9fc4ff" }}>
            Approvals
          </a>
          <a href="/audit" style={{ color: "#9fc4ff" }}>
            Audit
          </a>
        </nav>
        <main style={{ maxWidth: 1080, margin: "0 auto", padding: 24 }}>{children}</main>
        <footer aria-label="Copyright notice" style={{ maxWidth: 1080, margin: "0 auto", padding: "0 24px 24px", color: "#aab6d3" }}>
          <small>© {new Date().getFullYear()} ClearGlass Inc. All rights reserved.</small>
        </footer>
      </body>
    </html>
  );
}

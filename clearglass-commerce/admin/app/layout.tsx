import type { ReactNode } from "react";

export const metadata = {
  title: "ClearGlass Commerce — Admin Cockpit",
  description: "Orders, products, inventory, analytics, and the approval gate.",
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
        </nav>
        <main style={{ maxWidth: 1080, margin: "0 auto", padding: 24 }}>{children}</main>
      </body>
    </html>
  );
}

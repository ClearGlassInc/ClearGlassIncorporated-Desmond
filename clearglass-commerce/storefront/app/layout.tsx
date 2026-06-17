import type { ReactNode } from "react";

export const metadata = {
  title: "ClearGlass Store",
  description: "A governed, autonomous e-commerce storefront.",
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
        <header style={{ padding: "16px 24px", borderBottom: "1px solid rgba(124,150,255,.16)" }}>
          <strong>ClearGlass Store</strong>
        </header>
        <main style={{ maxWidth: 1080, margin: "0 auto", padding: 24 }}>{children}</main>
      </body>
    </html>
  );
}

import type { ReactNode } from "react";

export const metadata = {
  title: "ClearGlass Side Store — Cheap Wires & Electronics",
  description:
    "Low-cost wires, cables, connectors, adapters, and basic electronics. Free shipping over CAD $25.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          fontFamily: "Inter, system-ui, sans-serif",
          background: "#070a14",
          color: "#e7ecff",
        }}
      >
        {children}
      </body>
    </html>
  );
}

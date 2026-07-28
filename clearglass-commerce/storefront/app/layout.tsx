import type { ReactNode } from "react";
import { StoreShell } from "@/lib/StoreShell";

export const metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://clearglassinc.github.io"),
  title: "ClearGlass Store",
  description: "A governed, autonomous e-commerce storefront.",
  alternates: { canonical: "/" },
  other: { copyright: "© ClearGlass Inc. All rights reserved." },
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
        <StoreShell>{children}</StoreShell>
      </body>
    </html>
  );
}

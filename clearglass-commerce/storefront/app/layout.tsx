import type { ReactNode } from "react";
import "./globals.css";
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
      <body>
        {/* Futuristic cyber grid behind all content (pure CSS, no images). */}
        <div className="bg-grid" aria-hidden="true" />
        <StoreShell>{children}</StoreShell>
      </body>
    </html>
  );
}

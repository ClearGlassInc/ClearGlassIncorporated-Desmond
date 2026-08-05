import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  // Same holographic seal the marketing site uses as its tab icon, served from
  // this app's own public/ since it deploys on a separate origin.
  icons: {
    icon: "/clearglass-seal-192.png",
    shortcut: "/clearglass-seal-192.png",
    apple: "/clearglass-seal-192.png",
  },
  title: "Artemis Air Systems Control Surface | ClearGlass Inc.",
  description:
    "A premium aerospace-grade glassmorphism air systems console with live interactive controls for airflow, pressure, temperature, humidity, filtration, vents, and zones.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

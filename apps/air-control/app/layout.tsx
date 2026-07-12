import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
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

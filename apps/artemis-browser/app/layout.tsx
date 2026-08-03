import type { Metadata } from "next";
import "./globals.css";
import { SiteShell } from "../components/layout/SiteShell";

export const metadata: Metadata = {
  title: "ClearGlassInc Artemis Browser Intelligence Assistant",
  description: "Open-source browser security, AI research automation, and cybersecurity workflow automation for lawful defensive teams.",
  keywords: ["browser security", "AI research automation", "cybersecurity workflow automation", "OSINT", "defensive security"],
  openGraph: { title: "Artemis Browser Intelligence", description: "Local-first browser research with cited AI summaries and audited workflows.", type: "website" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body><SiteShell>{children}</SiteShell></body></html>;
}

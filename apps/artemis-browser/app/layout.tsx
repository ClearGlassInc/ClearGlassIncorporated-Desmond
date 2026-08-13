import type { Metadata } from "next";
import "./globals.css";
import "./mission-theme.css";
import { SiteShell } from "../components/layout/SiteShell";

export const metadata: Metadata = {
  // Same holographic seal the marketing site uses as its tab icon, served from
  // this app's own public/ since it deploys on a separate origin.
  icons: {
    icon: "/clearglass-seal-192.png",
    shortcut: "/clearglass-seal-192.png",
    apple: "/clearglass-seal-192.png",
  },
  title: "ClearGlassInc Artemis Browser Intelligence Assistant",
  description: "Open-source browser security, AI research automation, and cybersecurity workflow automation for lawful defensive teams.",
  keywords: ["browser security", "AI research automation", "cybersecurity workflow automation", "OSINT", "defensive security"],
  openGraph: { title: "Artemis Browser Intelligence", description: "Local-first browser research with cited AI summaries and audited workflows.", type: "website" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body><SiteShell>{children}</SiteShell></body></html>;
}

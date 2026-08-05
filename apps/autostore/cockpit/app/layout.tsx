import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  // Same holographic seal the marketing site uses as its tab icon, served from
  // this app's own public/ since it deploys on a separate origin.
  icons: {
    icon: "/clearglass-seal-192.png",
    shortcut: "/clearglass-seal-192.png",
    apple: "/clearglass-seal-192.png",
  },
  title: "PERCIVAL Autostore · Control Cockpit",
  description: "Read-first cockpit over the Autostore control plane.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="cg-header">
          <div className="cg-mark" />
          <div>
            <div className="cg-title">PERCIVAL · Autostore</div>
            <div className="cg-sub">CONTROL COCKPIT · READ-ONLY</div>
          </div>
          <nav className="cg-nav">
            <a href="/">Decisions</a>
            <a href="/approvals">Approvals</a>
            <a href="/audit">Audit</a>
          </nav>
        </header>
        <main className="cg-main">{children}</main>
      </body>
    </html>
  );
}

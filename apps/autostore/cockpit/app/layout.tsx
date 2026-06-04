import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
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

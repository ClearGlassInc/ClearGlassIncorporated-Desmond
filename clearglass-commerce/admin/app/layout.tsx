import type { ReactNode } from "react";
import type { Metadata } from "next";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://admin.clearglass.example";
const YEAR = new Date().getFullYear();

// metadataBase lets relative `alternates.canonical` values in each page resolve
// to absolute URLs. The admin cockpit is private, so the default robots policy
// is noindex/nofollow site-wide (individual pages reaffirm this too).
export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "ClearGlass Commerce — Admin Cockpit",
    template: "%s",
  },
  description: "Orders, products, inventory, analytics, and the approval gate.",
  applicationName: "ClearGlass Commerce Admin",
  robots: { index: false, follow: false },
  alternates: { canonical: "/" },
  // Machine-readable copyright asserted on every page (paired with the visible
  // footer notice below).
  other: { copyright: `© ${YEAR} ClearGlass Inc. All rights reserved.` },
  openGraph: {
    title: "ClearGlass Commerce — Admin Cockpit",
    description: "Governed commerce operator cockpit.",
    siteName: "ClearGlass Commerce Admin",
    type: "website",
  },
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
        {/* Keyboard/screen-reader skip link — first focusable element on the page. */}
        <a
          href="#main-content"
          style={{
            position: "absolute",
            left: -9999,
            top: 0,
            padding: "10px 14px",
            background: "#1a2340",
            color: "#eef2ff",
            borderRadius: 8,
            zIndex: 100,
          }}
          // Reveal on focus without any client JS or blocking behavior.
          className="cg-skip-link"
        >
          Skip to main content
        </a>
        <style>{`.cg-skip-link:focus{left:12px;top:12px;}`}</style>

        <nav
          aria-label="Primary"
          style={{
            display: "flex",
            gap: 18,
            alignItems: "center",
            padding: "14px 24px",
            borderBottom: "1px solid rgba(124,150,255,.16)",
          }}
        >
          <strong>Admin Cockpit</strong>
          <a href="/" style={{ color: "#9fc4ff" }}>
            Overview
          </a>
          <a href="/approvals" style={{ color: "#9fc4ff" }}>
            Approvals
          </a>
          <a href="/audit" style={{ color: "#9fc4ff" }}>
            Audit
          </a>
          <a href="/playbooks" style={{ color: "#9fc4ff" }}>
            Playbooks
          </a>
          {/* Logout is a real form POST — works without JavaScript. */}
          <form method="post" action="/api/auth/logout" style={{ marginLeft: "auto" }}>
            <button
              type="submit"
              style={{
                background: "transparent",
                border: "1px solid rgba(124,150,255,.3)",
                color: "#9fc4ff",
                borderRadius: 8,
                padding: "6px 12px",
                cursor: "pointer",
              }}
            >
              Sign out
            </button>
          </form>
        </nav>

        <main id="main-content" style={{ maxWidth: 1080, margin: "0 auto", padding: 24 }}>
          {children}
        </main>

        <footer
          style={{
            maxWidth: 1080,
            margin: "0 auto",
            padding: "24px",
            color: "#6b7699",
            fontSize: 13,
            borderTop: "1px solid rgba(124,150,255,.1)",
          }}
        >
          © {YEAR} ClearGlass Inc. All rights reserved. Confidential — for authorized operators only.
        </footer>
      </body>
    </html>
  );
}

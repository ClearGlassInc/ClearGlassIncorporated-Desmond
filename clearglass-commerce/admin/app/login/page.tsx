// Login page — the only unauthenticated entry point.
//
// Accessibility first: this is a plain server-rendered <form> that POSTs to
// /api/auth/login. It needs no JavaScript to work, every control has an
// associated <label>, the error is announced via role="alert", and focus/tab
// order is the natural DOM order. Nothing here blocks screen readers or input.
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sign in — ClearGlass Commerce Admin",
  description: "Authenticate to access the ClearGlass Commerce operator cockpit.",
  robots: { index: false, follow: false },
  alternates: { canonical: "/login" },
};

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string; next?: string }>;
}) {
  const { error, next } = await searchParams;
  const nextTarget = typeof next === "string" && next.startsWith("/") && !next.startsWith("//") ? next : "/";

  return (
    <section style={{ maxWidth: 420, margin: "0 auto", padding: "48px 0" }}>
      <h1 style={{ fontSize: 26, marginBottom: 6 }}>Operator sign in</h1>
      <p style={{ color: "#9aa6c8", marginTop: 0, marginBottom: 24 }}>
        This cockpit and its premium playbooks are restricted to authorized
        ClearGlass operators.
      </p>

      {error ? (
        <p
          role="alert"
          style={{
            padding: "10px 14px",
            borderRadius: 10,
            border: "1px solid rgba(248,113,113,.4)",
            background: "rgba(248,113,113,.12)",
            color: "#fca5a5",
            marginBottom: 18,
          }}
        >
          Incorrect password. Please try again.
        </p>
      ) : null}

      <form method="post" action="/api/auth/login">
        <input type="hidden" name="next" value={nextTarget} />
        <label htmlFor="password" style={{ display: "block", fontWeight: 600, marginBottom: 8 }}>
          Password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          autoFocus
          aria-describedby="password-hint"
          style={{
            width: "100%",
            boxSizing: "border-box",
            padding: "12px 14px",
            borderRadius: 10,
            border: "1px solid rgba(124,150,255,.3)",
            background: "#0b1020",
            color: "#eef2ff",
            fontSize: 16,
          }}
        />
        <p id="password-hint" style={{ color: "#6b7699", fontSize: 13, margin: "8px 0 20px" }}>
          Your session lasts 12 hours and is bound to this browser.
        </p>
        <button
          type="submit"
          style={{
            width: "100%",
            padding: "12px 16px",
            borderRadius: 10,
            border: "1px solid rgba(124,150,255,.5)",
            background: "rgba(124,150,255,.18)",
            color: "#eef2ff",
            fontSize: 16,
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Sign in
        </button>
      </form>
    </section>
  );
}

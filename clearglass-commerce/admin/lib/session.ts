// Server-side session access for SSR pages and route handlers.
//
// Middleware already blocks unauthenticated requests, but pages/routes that
// render premium content call requireSession() as defense-in-depth: if the
// matcher is ever misconfigured or a route is invoked internally, the sensitive
// render still refuses to proceed without a valid session. This is the
// server-only counterpart to lib/auth.ts (which is Edge-safe and shared).
//
// This module imports next/headers, which is server-only by construction — it
// throws if ever pulled into a client bundle, giving the same guarantee as the
// `server-only` marker without depending on that package being resolvable.
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { SESSION_COOKIE, verifySession, type SessionClaims } from "@/lib/auth";

/** Return the current session claims, or null if unauthenticated. Never throws. */
export async function getSession(): Promise<SessionClaims | null> {
  const store = await cookies();
  return verifySession(store.get(SESSION_COOKIE)?.value);
}

/**
 * Require a session for an SSR page. Redirects to /login (preserving the intended
 * destination) when absent. Returns the claims when present.
 */
export async function requireSession(returnTo?: string): Promise<SessionClaims> {
  const session = await getSession();
  if (!session) {
    const next = returnTo ? `?next=${encodeURIComponent(returnTo)}` : "";
    redirect(`/login${next}`);
  }
  return session;
}

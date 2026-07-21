// Edge middleware — the front door for the admin cockpit.
//
// Runs before ANY matched route renders, on the server, at the edge. Its job:
//   1. Fingerprint + log every request (referrer, timestamp, burst detection).
//   2. Let a small allowlist of public paths through (login, its API, health).
//   3. For everything else, require a valid session cookie — otherwise redirect
//      to /login?next=<original>. Premium pages/prompts never even begin to
//      render for an unauthenticated visitor, so nothing sensitive is shipped
//      to the client.
//   4. Add hardening + no-store headers so premium responses aren't cached by
//      shared proxies or indexed.
//
// This is server-side only. It does not inject any client-side script, focus
// trap, or overlay — so screen readers, keyboard navigation, and form inputs on
// the pages that DO render are completely unaffected.

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { SESSION_COOKIE, verifySession } from "@/lib/auth";
import {
  fingerprintRequest,
  logAccess,
  recordAndDetectBurst,
  type AccessDecision,
} from "@/lib/logging";

// Paths that must stay reachable without a session. Everything else is gated.
const PUBLIC_PREFIXES = [
  "/login",
  "/api/auth/login",
  "/api/auth/logout",
  "/healthz",
  "/favicon.ico",
];

function isPublic(pathname: string): boolean {
  return PUBLIC_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}

function harden(res: NextResponse): NextResponse {
  // Premium responses must never be cached by a shared cache or indexed.
  res.headers.set("Cache-Control", "no-store, max-age=0, must-revalidate");
  res.headers.set("X-Robots-Tag", "noindex, nofollow");
  res.headers.set("X-Content-Type-Options", "nosniff");
  res.headers.set("X-Frame-Options", "DENY");
  res.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  return res;
}

export async function middleware(req: NextRequest): Promise<NextResponse> {
  const { pathname, search } = req.nextUrl;

  // 1. Fingerprint + burst detection + structured log for every request.
  const fp = await fingerprintRequest(req, pathname);
  const { burst } = recordAndDetectBurst(fp.fingerprint);

  const emit = (decision: AccessDecision, res: NextResponse): NextResponse => {
    logAccess(fp, decision, burst);
    return res;
  };

  // 2. Public routes pass through (still logged + hardened).
  if (isPublic(pathname)) {
    return emit("allow", harden(NextResponse.next()));
  }

  // 3. Gate everything else on a valid session.
  const token = req.cookies.get(SESSION_COOKIE)?.value;
  const session = await verifySession(token);
  if (!session) {
    // API routes get a 401 (no HTML redirect); pages redirect to login.
    if (pathname.startsWith("/api/")) {
      return emit(
        "redirect-login",
        harden(NextResponse.json({ error: "authentication required" }, { status: 401 })),
      );
    }
    const loginUrl = req.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.search = "";
    loginUrl.searchParams.set("next", `${pathname}${search}`);
    return emit("redirect-login", harden(NextResponse.redirect(loginUrl)));
  }

  // Authenticated: proceed, surfacing the subject to downstream handlers.
  const res = NextResponse.next();
  res.headers.set("x-cg-operator", session.sub);
  return emit("allow", harden(res));
}

// Match everything except Next internals and static assets. Those are excluded
// so the middleware never gates framework chunks (which would break the login
// page itself) and so hashed static files stay cacheable.
export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|robots.txt|sitemap.xml).*)"],
};

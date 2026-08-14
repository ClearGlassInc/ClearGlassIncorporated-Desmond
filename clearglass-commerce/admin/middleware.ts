import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE } from "@/lib/constants";
import { edgeOriginFailure } from "@/lib/origin-auth";

const PROTECTED_PREFIXES = [
  "/",
  "/approvals",
  "/audit",
  "/playbooks",
  "/premium",
  "/api/premium",
  "/api/assets",
  "/api/download",
];
const PUBLIC_PREFIXES = ["/login", "/api/login", "/api/auth/login", "/api/auth/logout", "/healthz", "/_next", "/favicon.ico"];
const WINDOW_MS = 60_000;
const MAX_BURST_BUCKETS = 10_000;
const configuredBurstThreshold = Number(process.env.ROUTE_BURST_THRESHOLD || 60);
const BURST_THRESHOLD = Number.isFinite(configuredBurstThreshold) && configuredBurstThreshold > 0
  ? configuredBurstThreshold
  : 60;
const burstBuckets = new Map<string, number[]>();

function isProtected(pathname: string): boolean {
  if (PUBLIC_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`))) return false;
  return PROTECTED_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}

function base64Url(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

async function hmac(value: string): Promise<string> {
  const fingerprintSecret = process.env.REQUEST_FINGERPRINT_SECRET;
  const production = process.env.NODE_ENV === "production" || process.env.APP_ENV === "production";
  if (production && (!fingerprintSecret || fingerprintSecret.length < 16)) {
    throw new Error("REQUEST_FINGERPRINT_SECRET must be at least 16 characters in production");
  }

  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(fingerprintSecret || "dev-only-fingerprint-secret"),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(value));
  return base64Url(new Uint8Array(signature));
}

function burstCount(fingerprint: string): number {
  const now = Date.now();
  const hits = (burstBuckets.get(fingerprint) || []).filter((hit) => now - hit <= WINDOW_MS);
  hits.push(now);

  if (!burstBuckets.has(fingerprint) && burstBuckets.size >= MAX_BURST_BUCKETS) {
    const oldest = burstBuckets.keys().next().value as string | undefined;
    if (oldest) burstBuckets.delete(oldest);
  }

  burstBuckets.set(fingerprint, hits);
  return hits.length;
}

export async function middleware(request: NextRequest) {
  const originFailure = edgeOriginFailure(request);
  if (originFailure) return originFailure;
  const pathname = request.nextUrl.pathname;
  const fingerprint = await hmac([
    request.headers.get("x-forwarded-for") || "unknown-ip",
    request.headers.get("user-agent") || "unknown-agent",
  ].join("|"));
  const count = burstCount(fingerprint);

  console.info(JSON.stringify({
    severity: count > BURST_THRESHOLD ? "warn" : "info",
    event: "route_request",
    at: new Date().toISOString(),
    fingerprint,
    referrer: request.headers.get("referer") || "direct",
    path: pathname,
    method: request.method,
    burstCount: count,
  }));

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-request-fingerprint", fingerprint);
  requestHeaders.set("x-pathname", pathname);

  if (isProtected(pathname) && !request.cookies.get(SESSION_COOKIE)?.value) {
    const login = new URL("/login", request.url);
    login.searchParams.set("next", pathname);
    return NextResponse.redirect(login, { headers: requestHeaders });
  }

  return NextResponse.next({ request: { headers: requestHeaders } });
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};

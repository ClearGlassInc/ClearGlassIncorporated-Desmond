// Session tokens for the admin cockpit.
//
// This module is intentionally dependency-free and uses only Web Crypto +
// TextEncoder/btoa/atob so the *same* code runs in the Edge middleware runtime
// (which has no Node built-ins) and in Node route handlers. That lets the
// middleware verify a session without a round-trip and without importing a JWT
// library that would break on the Edge.
//
// A session token is a signed, expiring bearer of "this browser authenticated".
// It is NOT the control-plane `ADMIN_API_KEY` — that key still independently
// gates every mutating control-plane endpoint (see control-plane/app/security.py).
// This layer only decides who may load the premium admin *pages*.

const encoder = new TextEncoder();

// The signing secret. In production this MUST be set (see fail-closed check in
// requireSecret). In local/dev with no secret we fall back to a fixed dev-only
// value so `next dev` / `next build` work without configuration.
const DEV_SECRET = "clearglass-dev-only-insecure-secret-change-me";

export const SESSION_COOKIE = "cg_admin_session";
// Default session lifetime: 12h. Short enough to bound exposure of a leaked
// cookie, long enough to cover an operator's working session.
export const SESSION_TTL_SECONDS = 12 * 60 * 60;

export interface SessionClaims {
  sub: string; // subject / operator identifier
  iat: number; // issued-at (unix seconds)
  exp: number; // expiry (unix seconds)
}

function getSecret(): string {
  return process.env.AUTH_SECRET || DEV_SECRET;
}

/**
 * True when a real (non-dev) secret is configured. Callers that must fail
 * closed in production (login route) use this to refuse to mint sessions with
 * the insecure default.
 */
export function hasStrongSecret(): boolean {
  const s = process.env.AUTH_SECRET;
  return typeof s === "string" && s.length >= 16;
}

// --- base64url without Buffer (works on Edge + Node) ---------------------------

function bytesToBase64Url(bytes: Uint8Array): string {
  let binary = "";
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function base64UrlToBytes(b64url: string): Uint8Array {
  const b64 = b64url.replace(/-/g, "+").replace(/_/g, "/");
  const pad = b64.length % 4 === 0 ? "" : "=".repeat(4 - (b64.length % 4));
  const binary = atob(b64 + pad);
  const out = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) out[i] = binary.charCodeAt(i);
  return out;
}

async function hmacKey(): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    "raw",
    encoder.encode(getSecret()),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"],
  );
}

// Constant-time-ish comparison. crypto.subtle.verify does the real constant-time
// check; this guards the string-length short-circuit for the manual path.
function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let mismatch = 0;
  for (let i = 0; i < a.length; i++) mismatch |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return mismatch === 0;
}

/**
 * Mint a signed session token for `subject`, valid for `ttlSeconds`.
 * Format: base64url(payloadJSON).base64url(hmac) — compact and self-contained.
 */
export async function createSession(
  subject: string,
  ttlSeconds: number = SESSION_TTL_SECONDS,
): Promise<string> {
  const now = Math.floor(Date.now() / 1000);
  const claims: SessionClaims = { sub: subject, iat: now, exp: now + ttlSeconds };
  const payload = bytesToBase64Url(encoder.encode(JSON.stringify(claims)));
  const sig = await crypto.subtle.sign("HMAC", await hmacKey(), encoder.encode(payload));
  return `${payload}.${bytesToBase64Url(new Uint8Array(sig))}`;
}

/**
 * Verify a token's signature and expiry. Returns the claims when valid, or null
 * for any failure (malformed, bad signature, expired). Never throws — callers
 * treat null as "unauthenticated".
 */
export async function verifySession(token: string | undefined | null): Promise<SessionClaims | null> {
  if (!token) return null;
  const dot = token.indexOf(".");
  if (dot <= 0) return null;
  const payload = token.slice(0, dot);
  const providedSig = token.slice(dot + 1);
  try {
    const expectedSigBytes = await crypto.subtle.sign(
      "HMAC",
      await hmacKey(),
      encoder.encode(payload),
    );
    const expectedSig = bytesToBase64Url(new Uint8Array(expectedSigBytes));
    if (!timingSafeEqual(expectedSig, providedSig)) return null;
    const claims = JSON.parse(new TextDecoder().decode(base64UrlToBytes(payload))) as SessionClaims;
    if (typeof claims.exp !== "number" || claims.exp < Math.floor(Date.now() / 1000)) return null;
    return claims;
  } catch {
    return null;
  }
}

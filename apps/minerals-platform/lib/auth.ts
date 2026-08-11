import { timingSafeEqual } from "node:crypto";
import type { NextRequest } from "next/server";

export type Role = "VIEWER" | "ANALYST" | "SENIOR_ANALYST" | "DATA_STEWARD" | "ADMINISTRATOR" | "API_CLIENT";
export type Principal = { userId: string; organizationId: string; role: Role; subject?: string };

const rank: Record<Role, number> = {
  VIEWER: 10,
  API_CLIENT: 15,
  ANALYST: 20,
  SENIOR_ANALYST: 30,
  DATA_STEWARD: 40,
  ADMINISTRATOR: 50
};

export function resolvePrincipal(request: NextRequest): Principal | null {
  const mode = process.env.AUTH_MODE ?? "development";
  if (mode === "development") {
    return {
      userId: request.headers.get("x-cg-user-id") ?? "00000000-0000-0000-0000-000000000001",
      organizationId: request.headers.get("x-cg-org-id") ?? "00000000-0000-0000-0000-000000000001",
      role: normalizeRole(request.headers.get("x-cg-role")) ?? "ADMINISTRATOR"
    };
  }
  // Production identity claims are accepted only when a trusted OIDC/SAML gateway
  // proves the request crossed the private ingress boundary.
  const expectedGatewaySecret = process.env.IDENTITY_GATEWAY_SECRET;
  const presentedGatewaySecret = request.headers.get("x-cg-gateway-secret");
  if (!expectedGatewaySecret || !presentedGatewaySecret || !safeEqual(expectedGatewaySecret, presentedGatewaySecret)) return null;
  const userId = request.headers.get("x-cg-user-id");
  const organizationId = request.headers.get("x-cg-org-id");
  const role = normalizeRole(request.headers.get("x-cg-role"));
  const subject = request.headers.get("x-cg-subject") ?? undefined;
  if (!userId || !organizationId || !role) return null;
  return { userId, organizationId, role, subject };
}

export function requireRole(principal: Principal | null, minimum: Role): Principal {
  if (!principal) throw new AuthError(401, "Authentication required");
  if (rank[principal.role] < rank[minimum]) throw new AuthError(403, `Role ${minimum} or higher required`);
  return principal;
}

export class AuthError extends Error {
  constructor(public readonly status: 401 | 403, message: string) { super(message); }
}

function normalizeRole(value: string | null): Role | null {
  const role = value?.toUpperCase() as Role | undefined;
  return role && role in rank ? role : null;
}

function safeEqual(a: string, b: string): boolean {
  const left = Buffer.from(a);
  const right = Buffer.from(b);
  return left.length === right.length && timingSafeEqual(left, right);
}

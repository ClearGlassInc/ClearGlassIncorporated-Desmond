import { afterEach, describe, expect, it } from "vitest";
import { resolvePrincipal } from "@/lib/auth";

const originalNodeEnv = process.env.NODE_ENV;
const originalAuthMode = process.env.AUTH_MODE;
const originalGatewaySecret = process.env.IDENTITY_GATEWAY_SECRET;

function requestWith(headers: Record<string, string> = {}) {
  return { headers: new Headers(headers) };
}

function restore(name: "NODE_ENV" | "AUTH_MODE" | "IDENTITY_GATEWAY_SECRET", value: string | undefined) {
  if (value === undefined) delete process.env[name];
  else process.env[name] = value;
}

afterEach(() => {
  restore("NODE_ENV", originalNodeEnv);
  restore("AUTH_MODE", originalAuthMode);
  restore("IDENTITY_GATEWAY_SECRET", originalGatewaySecret);
});

describe("resolvePrincipal", () => {
  it("fails closed when AUTH_MODE is missing", () => {
    process.env.NODE_ENV = "production";
    delete process.env.AUTH_MODE;

    expect(resolvePrincipal(requestWith())).toBeNull();
  });

  it("fails closed when AUTH_MODE is blank", () => {
    process.env.NODE_ENV = "production";
    process.env.AUTH_MODE = "   ";

    expect(resolvePrincipal(requestWith())).toBeNull();
  });

  it("rejects development identities in production", () => {
    process.env.NODE_ENV = "production";
    process.env.AUTH_MODE = "development";

    expect(resolvePrincipal(requestWith({ "x-cg-role": "ADMINISTRATOR" }))).toBeNull();
  });

  it("preserves explicitly configured local development identities", () => {
    process.env.NODE_ENV = "development";
    process.env.AUTH_MODE = "development";

    expect(resolvePrincipal(requestWith())).toEqual({
      userId: "00000000-0000-0000-0000-000000000001",
      organizationId: "00000000-0000-0000-0000-000000000001",
      role: "ADMINISTRATOR"
    });
  });

  it("rejects gateway claims when the gateway secret is not configured", () => {
    process.env.NODE_ENV = "production";
    process.env.AUTH_MODE = "gateway";
    delete process.env.IDENTITY_GATEWAY_SECRET;

    expect(resolvePrincipal(requestWith({
      "x-cg-gateway-secret": "presented-secret",
      "x-cg-user-id": "11111111-1111-1111-1111-111111111111",
      "x-cg-org-id": "22222222-2222-2222-2222-222222222222",
      "x-cg-role": "ANALYST"
    }))).toBeNull();
  });

  it("accepts complete gateway claims only with the configured shared secret", () => {
    process.env.NODE_ENV = "production";
    process.env.AUTH_MODE = "gateway";
    process.env.IDENTITY_GATEWAY_SECRET = "expected-secret";

    expect(resolvePrincipal(requestWith({
      "x-cg-gateway-secret": "expected-secret",
      "x-cg-user-id": "11111111-1111-1111-1111-111111111111",
      "x-cg-org-id": "22222222-2222-2222-2222-222222222222",
      "x-cg-role": "analyst",
      "x-cg-subject": "oidc|example"
    }))).toEqual({
      userId: "11111111-1111-1111-1111-111111111111",
      organizationId: "22222222-2222-2222-2222-222222222222",
      role: "ANALYST",
      subject: "oidc|example"
    });
  });
});

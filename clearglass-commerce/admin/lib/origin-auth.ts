import { NextRequest, NextResponse } from "next/server";

const HEADER_NAME = /^[A-Za-z][A-Za-z0-9-]{1,62}$/;
const MAX_SECRET_LENGTH = 512;

function required(): boolean {
  return ["1", "true", "yes"].includes((process.env.EDGE_ORIGIN_AUTH_REQUIRED || "").toLowerCase());
}

function fixedWorkEqual(left: string, right: string): boolean {
  if (left.length > MAX_SECRET_LENGTH || right.length > MAX_SECRET_LENGTH) return false;
  let difference = left.length ^ right.length;
  for (let index = 0; index < MAX_SECRET_LENGTH; index += 1) {
    difference |= (left.charCodeAt(index) || 0) ^ (right.charCodeAt(index) || 0);
  }
  return difference === 0;
}

/**
 * Fail closed before session routing when the admin origin is configured to
 * accept only requests carrying the edge-overwritten origin identity.
 */
export function edgeOriginFailure(request: NextRequest): NextResponse | null {
  if (!required()) return null;
  const headerName = process.env.EDGE_ORIGIN_AUTH_HEADER_NAME || "X-ClearGlass-Edge-Origin";
  const secrets = (process.env.EDGE_ORIGIN_AUTH_SECRETS || "")
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean);
  if (
    !HEADER_NAME.test(headerName) ||
    secrets.length === 0 ||
    secrets.some((secret) => secret.length < 32 || secret.length > MAX_SECRET_LENGTH) ||
    new Set(secrets).size !== secrets.length
  ) {
    return NextResponse.json({ detail: "origin authentication is misconfigured" }, { status: 503 });
  }

  const presented = request.headers.get(headerName) || "";
  let matched = false;
  for (const secret of secrets) {
    matched = fixedWorkEqual(presented, secret) || matched;
  }
  if (!matched) {
    return NextResponse.json(
      { detail: "request did not arrive through the approved edge" },
      { status: 403 },
    );
  }
  return null;
}

import { NextResponse, type NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  if ((process.env.AUTH_MODE ?? "development") === "development") return NextResponse.next();
  if (request.nextUrl.pathname === "/api/v1/health") return NextResponse.next();

  const expected = process.env.IDENTITY_GATEWAY_SECRET;
  const presented = request.headers.get("x-cg-gateway-secret");
  const hasIdentity = Boolean(
    request.headers.get("x-cg-user-id") &&
    request.headers.get("x-cg-org-id") &&
    request.headers.get("x-cg-role")
  );

  if (!expected || !presented || expected !== presented || !hasIdentity) {
    if (request.nextUrl.pathname.startsWith("/api/")) {
      return NextResponse.json({ ok: false, error: { code: "UNAUTHENTICATED", message: "Trusted identity gateway required" } }, { status: 401 });
    }
    return new NextResponse("Authentication required", { status: 401, headers: { "Cache-Control": "no-store" } });
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"]
};

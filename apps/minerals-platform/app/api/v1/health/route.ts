import { NextResponse } from "next/server";
import { db } from "@/lib/db";

export const dynamic = "force-dynamic";

export async function GET() {
  const started = Date.now();
  let database: "healthy" | "unavailable" = "healthy";
  try { await db.$queryRaw`SELECT 1`; } catch { database = "unavailable"; }
  return NextResponse.json({
    ok: database === "healthy",
    service: "clearglass-minerals-platform",
    database,
    timestamp: new Date().toISOString(),
    latencyMs: Date.now() - started
  }, { status: database === "healthy" ? 200 : 503, headers: { "Cache-Control": "no-store" } });
}

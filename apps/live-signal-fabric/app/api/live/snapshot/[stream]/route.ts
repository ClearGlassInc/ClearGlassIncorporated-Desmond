import { NextRequest, NextResponse } from "next/server";
import { streamNames } from "@/lib/contracts";
import { getSnapshot } from "@/lib/snapshot";
export const dynamic = "force-dynamic";
export async function GET(_request: NextRequest, context: { params: Promise<{ stream: string }> }) {
  const { stream } = await context.params;
  if (!streamNames.includes(stream as (typeof streamNames)[number])) return NextResponse.json({ error: "unknown stream" }, { status: 404 });
  try { return NextResponse.json(await getSnapshot(stream as (typeof streamNames)[number]), { headers: { "Cache-Control": "private, max-age=0, must-revalidate" } }); }
  catch { return NextResponse.json({ error: "snapshot unavailable", state: "unavailable" }, { status: 503 }); }
}

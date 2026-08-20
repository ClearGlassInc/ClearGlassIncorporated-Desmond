import type { NextRequest } from "next/server";
import { db } from "@/lib/db";
import { requireRole, resolvePrincipal } from "@/lib/auth";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  try { requireRole(resolvePrincipal(request), "VIEWER"); }
  catch { return Response.json({ ok: false, error: { code: "UNAUTHENTICATED", message: "Authentication required" } }, { status: 401 }); }

  const encoder = new TextEncoder();
  let interval: ReturnType<typeof setInterval> | undefined;
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      const send = (event: string, payload: unknown) => controller.enqueue(encoder.encode(`event: ${event}\ndata: ${JSON.stringify(payload)}\n\n`));
      const publishSources = async () => {
        try {
          const sources = await db.dataSource.findMany({ where: { enabled: true }, select: { key: true, freshnessStatus: true, lastSuccessAt: true, lastAttemptAt: true } });
          send("source-health", { asOf: new Date().toISOString(), sources });
        } catch { send("degraded", { asOf: new Date().toISOString(), message: "Source health unavailable" }); }
      };
      send("connected", { asOf: new Date().toISOString() });
      await publishSources();
      interval = setInterval(() => void publishSources(), 30_000);
      request.signal.addEventListener("abort", () => { if (interval) clearInterval(interval); try { controller.close(); } catch {} }, { once: true });
    },
    cancel() { if (interval) clearInterval(interval); }
  });
  return new Response(stream, { headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache, no-transform", Connection: "keep-alive", "X-Accel-Buffering": "no" } });
}

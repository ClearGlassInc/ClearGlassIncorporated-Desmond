import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";
import { writeAudit } from "@/lib/audit";

const updateSchema = z.object({
  key: z.string().min(1).max(100),
  enabled: z.boolean().optional(),
  ttlSeconds: z.number().int().min(60).max(31_536_000).nullable().optional(),
  cadence: z.string().max(120).nullable().optional(),
  restrictions: z.string().max(4000).nullable().optional()
});

export async function GET(request: NextRequest) {
  try {
    requireRole(resolvePrincipal(request), "VIEWER");
    const sources = await db.dataSource.findMany({
      include: { ingestionRuns: { orderBy: { startedAt: "desc" }, take: 1 } },
      orderBy: { key: "asc" }
    });
    return success(sources.map((source) => ({
      ...source,
      latestRun: source.ingestionRuns[0] ?? null,
      ingestionRuns: undefined
    })));
  } catch (error) { return failure(error); }
}

export async function PATCH(request: NextRequest) {
  try {
    const principal = requireRole(resolvePrincipal(request), "ADMINISTRATOR");
    const input = updateSchema.parse(await request.json());
    const source = await db.dataSource.findUnique({ where: { key: input.key } });
    if (!source) return Response.json({ ok: false, error: { code: "NOT_FOUND", message: "Data source not found" } }, { status: 404 });
    const updated = await db.dataSource.update({ where: { key: input.key }, data: { enabled: input.enabled, ttlSeconds: input.ttlSeconds, cadence: input.cadence, restrictions: input.restrictions } });
    await writeAudit(principal, "source.update", "DataSource", updated.id, { key: updated.key, enabled: updated.enabled, ttlSeconds: updated.ttlSeconds, cadence: updated.cadence });
    return success(updated);
  } catch (error) { return failure(error); }
}

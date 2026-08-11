import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, queryObject, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";
import { assertRateLimit } from "@/lib/rate-limit";

const schema = z.object({ q: z.string().trim().min(2).max(160), limit: z.coerce.number().int().min(1).max(50).default(10) });

export async function GET(request: NextRequest) {
  try {
    const principal = requireRole(resolvePrincipal(request), "VIEWER");
    await assertRateLimit(`search:${principal.organizationId}:${principal.userId}`, 120, 60);
    const input = schema.parse(queryObject(new URL(request.url)));
    const contains = { contains: input.q, mode: "insensitive" as const };
    const [minerals, projects, mines, companies, facilities] = await Promise.all([
      db.mineral.findMany({ where: { deletedAt: null, name: contains }, take: input.limit, select: { id: true, name: true, slug: true, symbol: true } }),
      db.project.findMany({ where: { deletedAt: null, name: contains }, take: input.limit, select: { id: true, name: true, stage: true, country: { select: { name: true } } } }),
      db.mine.findMany({ where: { deletedAt: null, name: contains }, take: input.limit, select: { id: true, name: true, stage: true, country: { select: { name: true } } } }),
      db.company.findMany({ where: { deletedAt: null, name: contains }, take: input.limit, select: { id: true, name: true, ticker: true, exchange: true } }),
      db.facility.findMany({ where: { deletedAt: null, name: contains }, take: input.limit, select: { id: true, name: true, type: true, country: { select: { name: true } } } })
    ]);
    return success({ query: input.q, results: { minerals, projects, mines, companies, facilities } });
  } catch (error) { return failure(error); }
}

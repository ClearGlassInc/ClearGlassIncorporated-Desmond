import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, queryObject, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";

const schema = z.object({ mineralId: z.string().uuid().optional(), countryId: z.string().uuid().optional(), days: z.coerce.number().int().min(1).max(3650).default(180), limit: z.coerce.number().int().min(1).max(250).default(100) });

export async function GET(request: NextRequest) {
  try {
    requireRole(resolvePrincipal(request), "VIEWER");
    const input = schema.parse(queryObject(new URL(request.url)));
    const since = new Date(Date.now() - input.days * 86_400_000);
    const [projects, events] = await Promise.all([
      db.project.findMany({ where: { deletedAt: null, stage: { in: ["EXPLORATION", "DEVELOPMENT", "CONSTRUCTION"] }, ...(input.mineralId ? { mineralId: input.mineralId } : {}), ...(input.countryId ? { countryId: input.countryId } : {}) }, include: { mineral: true, country: true, operator: true, risks: { orderBy: { observedAt: "desc" }, take: 1 } }, orderBy: { updatedAt: "desc" }, take: input.limit }),
      db.event.findMany({ where: { occurredAt: { gte: since }, type: { in: ["EXPLORATION", "DISCOVERY", "PERMIT", "EXPANSION", "ACQUISITION", "SUPPLY_AGREEMENT"] } }, include: { source: true }, orderBy: { occurredAt: "desc" }, take: input.limit })
    ]);
    return success({ asOf: new Date().toISOString(), periodStart: since.toISOString(), projects, events });
  } catch (error) { return failure(error); }
}

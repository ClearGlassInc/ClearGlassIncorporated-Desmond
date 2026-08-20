import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, pageSchema, paginated, queryObject } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";

const schema = pageSchema.extend({ q: z.string().max(160).optional(), ticker: z.string().max(32).optional() });

export async function GET(request: NextRequest) {
  try {
    requireRole(resolvePrincipal(request), "VIEWER");
    const input = schema.parse(queryObject(new URL(request.url)));
    const where = {
      deletedAt: null,
      ...(input.q ? { name: { contains: input.q, mode: "insensitive" as const } } : {}),
      ...(input.ticker ? { ticker: { equals: input.ticker, mode: "insensitive" as const } } : {})
    };
    const [items, total] = await Promise.all([
      db.company.findMany({ where, include: { operatedMines: { select: { id: true, name: true, stage: true, mineral: { select: { name: true } }, country: { select: { name: true } } } }, operatedProjects: { select: { id: true, name: true, stage: true, mineral: { select: { name: true } }, country: { select: { name: true } } } }, operatedFacilities: { select: { id: true, name: true, type: true, country: { select: { name: true } } } }, ownershipAsOwner: { include: { mine: { select: { id: true, name: true } }, project: { select: { id: true, name: true } } } } }, skip: (input.page - 1) * input.pageSize, take: input.pageSize, orderBy: { name: input.order } }),
      db.company.count({ where })
    ]);
    return paginated(items, input.page, input.pageSize, total);
  } catch (error) { return failure(error); }
}

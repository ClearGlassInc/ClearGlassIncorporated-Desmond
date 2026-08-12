import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";
import { writeAudit } from "@/lib/audit";

const createSchema = z.object({ name: z.string().trim().min(1).max(120), description: z.string().max(1000).optional() });

export async function GET(request: NextRequest) {
  try {
    const principal = requireRole(resolvePrincipal(request), "VIEWER");
    const items = await db.watchlist.findMany({ where: { organizationId: principal.organizationId }, include: { items: true }, orderBy: { updatedAt: "desc" } });
    return success(items);
  } catch (error) { return failure(error); }
}

export async function POST(request: NextRequest) {
  try {
    const principal = requireRole(resolvePrincipal(request), "ANALYST");
    const input = createSchema.parse(await request.json());
    const watchlist = await db.watchlist.create({ data: { organizationId: principal.organizationId, ownerId: principal.userId, ...input }, include: { items: true } });
    await writeAudit(principal, "watchlist.create", "Watchlist", watchlist.id, { name: watchlist.name });
    return success(watchlist, { status: 201 });
  } catch (error) { return failure(error); }
}

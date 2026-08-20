import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";
import { writeAudit } from "@/lib/audit";

const actionSchema = z.discriminatedUnion("action", [
  z.object({ action: z.literal("ADD"), entityType: z.string().min(1).max(80), entityId: z.string().min(1).max(160), label: z.string().max(200).optional() }),
  z.object({ action: z.literal("REMOVE"), entityType: z.string().min(1).max(80), entityId: z.string().min(1).max(160) }),
  z.object({ action: z.literal("RENAME"), name: z.string().trim().min(1).max(120) })
]);

export async function PATCH(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  try {
    const principal = requireRole(resolvePrincipal(request), "ANALYST");
    const { id } = await context.params;
    const input = actionSchema.parse(await request.json());
    const watchlist = await db.watchlist.findFirst({ where: { id, organizationId: principal.organizationId } });
    if (!watchlist) return Response.json({ ok: false, error: { code: "NOT_FOUND", message: "Watchlist not found" } }, { status: 404 });
    if (input.action === "ADD") {
      await db.watchlistItem.upsert({ where: { watchlistId_entityType_entityId: { watchlistId: id, entityType: input.entityType, entityId: input.entityId } }, create: { watchlistId: id, entityType: input.entityType, entityId: input.entityId, label: input.label }, update: { label: input.label } });
    } else if (input.action === "REMOVE") {
      await db.watchlistItem.deleteMany({ where: { watchlistId: id, entityType: input.entityType, entityId: input.entityId } });
    } else {
      await db.watchlist.update({ where: { id }, data: { name: input.name } });
    }
    const updated = await db.watchlist.findUnique({ where: { id }, include: { items: true } });
    await writeAudit(principal, `watchlist.${input.action.toLowerCase()}`, "Watchlist", id, input);
    return success(updated);
  } catch (error) { return failure(error); }
}

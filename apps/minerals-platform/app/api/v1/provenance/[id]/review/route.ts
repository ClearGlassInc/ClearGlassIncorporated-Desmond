import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";
import { writeAudit } from "@/lib/audit";

const schema = z.discriminatedUnion("action", [
  z.object({ action: z.literal("MARK_REVIEWED") }),
  z.object({ action: z.literal("VERIFY") }),
  z.object({ action: z.literal("FLAG_UNKNOWN") })
]);

export async function POST(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  try {
    const principal = requireRole(resolvePrincipal(request), "DATA_STEWARD");
    const { id } = await context.params;
    const input = schema.parse(await request.json());
    const existing = await db.provenanceRecord.findUnique({ where: { id } });
    if (!existing) return Response.json({ ok: false, error: { code: "NOT_FOUND", message: "Provenance record not found" } }, { status: 404 });
    if (input.action === "VERIFY") requireRole(principal, "ADMINISTRATOR");
    const updated = await db.provenanceRecord.update({
      where: { id },
      data: {
        analystReviewedAt: new Date(),
        analystReviewerId: principal.userId,
        ...(input.action === "VERIFY" ? { status: "VERIFIED" as const } : {}),
        ...(input.action === "FLAG_UNKNOWN" ? { status: "UNKNOWN" as const } : {})
      },
      include: { source: true, document: true, analystReviewer: { select: { id: true, name: true, email: true } } }
    });
    await writeAudit(principal, `provenance.${input.action.toLowerCase()}`, "ProvenanceRecord", id, { previousStatus: existing.status, newStatus: updated.status, sourceId: updated.sourceId });
    return success(updated);
  } catch (error) { return failure(error); }
}

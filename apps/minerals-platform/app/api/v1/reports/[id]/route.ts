import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";
import { writeAudit } from "@/lib/audit";

const schema = z.discriminatedUnion("action", [
  z.object({ action: z.literal("REVIEW") }),
  z.object({ action: z.literal("PUBLISH") }),
  z.object({ action: z.literal("ARCHIVE") })
]);

export async function PATCH(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  try {
    const principal = requireRole(resolvePrincipal(request), "SENIOR_ANALYST");
    const { id } = await context.params;
    const input = schema.parse(await request.json());
    const report = await db.report.findFirst({ where: { id, organizationId: principal.organizationId } });
    if (!report) return Response.json({ ok: false, error: { code: "NOT_FOUND", message: "Report not found" } }, { status: 404 });
    if (input.action === "PUBLISH" && report.generatedByAi && !report.reviewedAt) {
      return Response.json({ ok: false, error: { code: "REVIEW_REQUIRED", message: "AI-generated reports require analyst review before publication" } }, { status: 409 });
    }
    const data = input.action === "REVIEW"
      ? { status: "REVIEWED", reviewedAt: new Date() }
      : input.action === "PUBLISH"
        ? { status: "PUBLISHED", publishedAt: new Date() }
        : { status: "ARCHIVED" };
    const updated = await db.report.update({ where: { id }, data });
    await writeAudit(principal, `report.${input.action.toLowerCase()}`, "Report", id, data);
    return success(updated);
  } catch (error) { return failure(error); }
}

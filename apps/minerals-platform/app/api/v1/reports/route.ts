import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, pageSchema, paginated, queryObject, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";
import { writeAudit } from "@/lib/audit";

const getSchema = pageSchema.extend({ status: z.string().max(40).optional() });
const createSchema = z.object({
  title: z.string().trim().min(1).max(240),
  body: z.record(z.string(), z.unknown()),
  sourceSnapshot: z.record(z.string(), z.unknown()).optional(),
  generatedByAi: z.boolean().default(false)
});

export async function GET(request: NextRequest) {
  try {
    const principal = requireRole(resolvePrincipal(request), "VIEWER");
    const input = getSchema.parse(queryObject(new URL(request.url)));
    const where = { organizationId: principal.organizationId, ...(input.status ? { status: input.status } : {}) };
    const [items, total] = await Promise.all([
      db.report.findMany({ where, include: { author: { select: { id: true, name: true, email: true } } }, skip: (input.page - 1) * input.pageSize, take: input.pageSize, orderBy: { createdAt: "desc" } }),
      db.report.count({ where })
    ]);
    return paginated(items, input.page, input.pageSize, total);
  } catch (error) { return failure(error); }
}

export async function POST(request: NextRequest) {
  try {
    const principal = requireRole(resolvePrincipal(request), "ANALYST");
    const input = createSchema.parse(await request.json());
    const report = await db.report.create({ data: { organizationId: principal.organizationId, authorId: principal.userId, title: input.title, status: "DRAFT", body: input.body, sourceSnapshot: input.sourceSnapshot, generatedByAi: input.generatedByAi } });
    await writeAudit(principal, "report.create", "Report", report.id, { generatedByAi: report.generatedByAi });
    return success({ ...report, publicationBlocked: report.generatedByAi && !report.reviewedAt }, { status: 201 });
  } catch (error) { return failure(error); }
}

import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, pageSchema, paginated, queryObject, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";
import { calculateRisk, riskComponentSchema } from "@/lib/risk";
import { writeAudit } from "@/lib/audit";

const getSchema = pageSchema.extend({ mineId: z.string().uuid().optional(), projectId: z.string().uuid().optional() });
const postSchema = z.object({
  mineId: z.string().uuid().optional(),
  projectId: z.string().uuid().optional(),
  methodologyVersion: z.string().max(80).default("weighted-mean-v1"),
  components: z.array(riskComponentSchema).min(1).max(40),
  persist: z.boolean().default(false),
  analystOverride: z.boolean().default(false),
  overrideReason: z.string().max(500).optional()
}).refine((value) => !value.persist || value.mineId || value.projectId, { message: "Persisted assessment requires mineId or projectId" });

export async function GET(request: NextRequest) {
  try {
    requireRole(resolvePrincipal(request), "VIEWER");
    const input = getSchema.parse(queryObject(new URL(request.url)));
    const where = { ...(input.mineId ? { mineId: input.mineId } : {}), ...(input.projectId ? { projectId: input.projectId } : {}) };
    const [items, total] = await Promise.all([
      db.riskAssessment.findMany({ where, include: { factors: true, mine: { select: { id: true, name: true } }, project: { select: { id: true, name: true } } }, skip: (input.page - 1) * input.pageSize, take: input.pageSize, orderBy: { observedAt: "desc" } }),
      db.riskAssessment.count({ where })
    ]);
    return paginated(items, input.page, input.pageSize, total);
  } catch (error) { return failure(error); }
}

export async function POST(request: NextRequest) {
  try {
    const principal = requireRole(resolvePrincipal(request), "ANALYST");
    const input = postSchema.parse(await request.json());
    const result = calculateRisk(input.components);
    if (!input.persist) return success({ persisted: false, result });
    // The initial data model stores platform-level risk history. Until tenant-specific
    // assessment ownership is added, only administrators may persist or override it.
    requireRole(principal, "ADMINISTRATOR");
    const assessment = await db.riskAssessment.create({
      data: {
        mineId: input.mineId,
        projectId: input.projectId,
        score: result.score,
        severity: result.severity,
        methodologyVersion: input.methodologyVersion,
        observedAt: new Date(),
        confidence: result.coverage,
        analystOverride: input.analystOverride,
        overrideReason: input.overrideReason,
        createdById: principal.userId,
        factors: { create: input.components.map((item) => ({ key: item.key, score: item.score, weight: item.weight, explanation: item.confidence == null ? undefined : `Input confidence ${item.confidence}` })) }
      },
      include: { factors: true }
    });
    await writeAudit(principal, "risk.assessment.create", "RiskAssessment", assessment.id, { severity: assessment.severity, score: assessment.score?.toString(), methodologyVersion: input.methodologyVersion, analystOverride: input.analystOverride });
    return success({ persisted: true, assessment }, { status: 201 });
  } catch (error) { return failure(error); }
}

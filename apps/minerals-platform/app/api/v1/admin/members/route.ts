import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";
import { writeAudit } from "@/lib/audit";

const roleSchema = z.enum(["VIEWER", "ANALYST", "SENIOR_ANALYST", "DATA_STEWARD", "ADMINISTRATOR", "API_CLIENT"]);
const createSchema = z.object({ email: z.string().email(), name: z.string().trim().min(1).max(160).optional(), subject: z.string().max(240).optional(), role: roleSchema });

export async function GET(request: NextRequest) {
  try {
    const principal = requireRole(resolvePrincipal(request), "ADMINISTRATOR");
    const members = await db.organizationMember.findMany({ where: { organizationId: principal.organizationId }, include: { user: { select: { id: true, email: true, name: true, subject: true, disabled: true, createdAt: true } } }, orderBy: { createdAt: "asc" } });
    return success(members);
  } catch (error) { return failure(error); }
}

export async function POST(request: NextRequest) {
  try {
    const principal = requireRole(resolvePrincipal(request), "ADMINISTRATOR");
    const input = createSchema.parse(await request.json());
    const user = await db.user.upsert({ where: { email: input.email.toLowerCase() }, create: { email: input.email.toLowerCase(), name: input.name, subject: input.subject }, update: { name: input.name, ...(input.subject ? { subject: input.subject } : {}) } });
    const membership = await db.organizationMember.upsert({ where: { organizationId_userId: { organizationId: principal.organizationId, userId: user.id } }, create: { organizationId: principal.organizationId, userId: user.id, role: input.role }, update: { role: input.role } });
    await writeAudit(principal, "organization.member.upsert", "OrganizationMember", membership.id, { userId: user.id, role: membership.role });
    return success({ membership, user: { id: user.id, email: user.email, name: user.name } }, { status: 201 });
  } catch (error) { return failure(error); }
}

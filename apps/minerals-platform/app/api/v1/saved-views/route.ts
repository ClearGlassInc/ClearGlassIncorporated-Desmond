import type { NextRequest } from "next/server";
import type { Prisma } from "@prisma/client";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";
import { writeAudit } from "@/lib/audit";

const schema = z.object({ name: z.string().trim().min(1).max(120), state: z.record(z.string(), z.json()), isShared: z.boolean().default(false) });

export async function GET(request: NextRequest) {
  try {
    const principal = requireRole(resolvePrincipal(request), "VIEWER");
    const views = await db.savedView.findMany({ where: { organizationId: principal.organizationId, OR: [{ ownerId: principal.userId }, { isShared: true }] }, orderBy: { updatedAt: "desc" } });
    return success(views);
  } catch (error) { return failure(error); }
}

export async function POST(request: NextRequest) {
  try {
    const principal = requireRole(resolvePrincipal(request), "ANALYST");
    const input = schema.parse(await request.json());
    const state = JSON.parse(JSON.stringify(input.state)) as Prisma.InputJsonObject;
    const view = await db.savedView.upsert({
      where: { organizationId_ownerId_name: { organizationId: principal.organizationId, ownerId: principal.userId, name: input.name } },
      create: { organizationId: principal.organizationId, ownerId: principal.userId, name: input.name, state, isShared: input.isShared },
      update: { state, isShared: input.isShared }
    });
    await writeAudit(principal, "savedView.upsert", "SavedView", view.id, { name: view.name, isShared: view.isShared });
    return success(view, { status: 201 });
  } catch (error) { return failure(error); }
}

import type { NextRequest } from "next/server";
import { failure, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";
import { verifyAuditChain, writeAudit } from "@/lib/audit";

export async function POST(request: NextRequest) {
  try {
    const principal = requireRole(resolvePrincipal(request), "ADMINISTRATOR");
    const result = await verifyAuditChain();
    if (result.valid) await writeAudit(principal, "audit.chain.verify", "AuditLog", undefined, { checkedBeforeVerificationRecord: result.checked, valid: true });
    return success(result);
  } catch (error) { return failure(error); }
}

/**
 * GET /api/veilguard/ledger — chain integrity and the anchorable checkpoint.
 *
 * Returns whether the hash chain still verifies, where it broke if it did not,
 * and the current head hash. The head is what gets published to an external
 * anchor: a chain that no longer reproduces an anchor it already emitted has
 * been rebuilt, which is the one form of tampering an internally-consistent
 * rewrite could otherwise hide.
 *
 * No entries are returned — only the verdict. Reading the record itself is a
 * separate, narrower capability than confirming it has not been altered, and
 * this endpoint only needs the latter.
 */

import { NextResponse } from "next/server";
import { getLedger } from "@/lib/veilguard/ledger";
import { resolveOperator } from "@/lib/veilguard/viewer";

export async function GET() {
  const operator = await resolveOperator();
  if (!operator) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  const ledger = getLedger();
  const [verification, checkpoint] = await Promise.all([ledger.verify(), ledger.checkpoint()]);

  return NextResponse.json(
    {
      intact: verification.ok,
      length: verification.length,
      head: checkpoint.head,
      takenAt: checkpoint.takenAt,
      ...(verification.ok ? {} : { brokenAt: verification.brokenAt, reason: verification.reason }),
    },
    // A broken chain is a 200 with `intact: false`, not an error status: the
    // request succeeded, and monitors should alert on the field rather than on
    // a status code that a network fault could also produce.
    { status: 200 },
  );
}

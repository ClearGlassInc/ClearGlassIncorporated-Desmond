import { NextResponse } from 'next/server';
import { z } from 'zod';
import { validateTarget } from '../../../../src/policy/target-policy';

const schema = z.object({
  target: z.string().min(1).max(253),
  port: z.number().int().min(1).max(65535),
  approvedHosts: z.array(z.string()).min(1),
  approvedPorts: z.array(z.number().int().min(1).max(65535)).min(1),
  ownerContact: z.string().min(1).max(256),
  purpose: z.string().min(1).max(500),
  expiresAt: z.coerce.date(),
  confirmed: z.literal(true),
});

export async function POST(req: Request) {
  const parsed = schema.safeParse(await req.json().catch(() => null));
  if (!parsed.success) return NextResponse.json({ error: 'Invalid engagement scope.' }, { status: 400 });
  const { target, port, ...scope } = parsed.data;
  const result = await validateTarget(target, port, scope);
  return NextResponse.json(result, { status: result.allowed ? 200 : 403 });
}

/**
 * VEILGUARD — tamper-evident event ledger (server only).
 *
 * Every view, export, copy, share and denial is appended to a hash chain: each
 * entry commits to the entry before it, so editing, reordering, or deleting
 * history breaks the chain at the point of the change and `verify()` reports
 * exactly where.
 *
 * This is *tamper-evident*, not tamper-proof. An attacker who owns the store
 * and the signing key can rewrite the whole chain consistently. What defeats
 * that is `checkpoint()`: publish the head hash somewhere the application
 * cannot reach back into — a WORM bucket, a second account's log, a daily
 * commit — and any wholesale rewrite stops matching the anchors it already
 * emitted. The chain makes tampering detectable; the anchor makes it provable.
 *
 * Actor identifiers are stored pseudonymously (`actorRef`, a salted digest),
 * so the ledger answers "the same viewer did these five things" without
 * carrying a plaintext identity in every row. Re-identification goes through
 * the grant store, which is separately access-controlled.
 */

import { createHash, timingSafeEqual } from "node:crypto";

export const GENESIS_HASH = "0".repeat(64);

export type LedgerAction =
  | "grant_issued"
  | "grant_denied"
  | "render_started"
  | "render_expired"
  | "export_attempted"
  | "export_blocked"
  | "copy_attempted"
  | "share_issued"
  | "capture_suspected"
  | "honeypot_touched"
  | "risk_escalated"
  | "trace_requested";

export type LedgerInput = {
  action: LedgerAction;
  /** Plaintext subject; hashed into `actorRef` on append and never stored raw. */
  subject: string;
  sessionId: string;
  assetId: string;
  grantId: string | null;
  riskScore: number;
  /** Small, non-sensitive detail bag. Keep it free of content and raw PII. */
  detail?: Record<string, string | number | boolean | null>;
  /** Overridable for deterministic tests. */
  timestamp?: Date;
};

export type LedgerEntry = {
  seq: number;
  timestamp: string;
  action: LedgerAction;
  actorRef: string;
  sessionRef: string;
  assetId: string;
  grantId: string | null;
  riskScore: number;
  detail: Record<string, string | number | boolean | null>;
  prevHash: string;
  hash: string;
};

export type VerifyResult =
  | { ok: true; length: number; head: string }
  | { ok: false; length: number; brokenAt: number; reason: string };

const PSEUDONYM_SALT_ENV = "VEILGUARD_LEDGER_SALT";

function pseudonymSalt(): string {
  const salt = process.env[PSEUDONYM_SALT_ENV];
  if (!salt && process.env.NODE_ENV === "production") {
    throw new Error(`${PSEUDONYM_SALT_ENV} must be set in production`);
  }
  return salt || "dev-only-veilguard-ledger-salt-change-me";
}

/** Stable pseudonym for an identifier. Same input, same ref, within one salt epoch. */
export function pseudonymize(value: string, kind: "actor" | "session"): string {
  return createHash("sha256").update(`${pseudonymSalt()}|${kind}|${value}`).digest("hex").slice(0, 32);
}

/**
 * Deterministic serialization. Object keys are sorted at every level so two
 * runs over the same logical entry always hash identically — otherwise the
 * chain would break on nothing more than a change in property order.
 */
function canonicalize(value: unknown): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value) ?? "null";
  if (Array.isArray(value)) return `[${value.map(canonicalize).join(",")}]`;
  const record = value as Record<string, unknown>;
  const parts = Object.keys(record)
    .sort()
    .map((key) => `${JSON.stringify(key)}:${canonicalize(record[key])}`);
  return `{${parts.join(",")}}`;
}

export function hashEntry(entry: Omit<LedgerEntry, "hash">): string {
  return createHash("sha256").update(canonicalize(entry)).digest("hex");
}

/** Durable storage boundary. The in-memory implementation is for dev and tests. */
export interface LedgerSink {
  append(entry: LedgerEntry): void | Promise<void>;
  all(): readonly LedgerEntry[] | Promise<readonly LedgerEntry[]>;
}

export class InMemoryLedgerSink implements LedgerSink {
  private readonly entries: LedgerEntry[] = [];

  append(entry: LedgerEntry): void {
    this.entries.push(entry);
  }

  all(): readonly LedgerEntry[] {
    return this.entries;
  }
}

export class Ledger {
  private head = GENESIS_HASH;
  private length = 0;

  constructor(private readonly sink: LedgerSink = new InMemoryLedgerSink()) {}

  async append(input: LedgerInput): Promise<LedgerEntry> {
    const unhashed: Omit<LedgerEntry, "hash"> = {
      seq: this.length,
      timestamp: (input.timestamp ?? new Date()).toISOString(),
      action: input.action,
      actorRef: pseudonymize(input.subject, "actor"),
      sessionRef: pseudonymize(input.sessionId, "session"),
      assetId: input.assetId,
      grantId: input.grantId,
      riskScore: input.riskScore,
      detail: input.detail ?? {},
      prevHash: this.head,
    };

    const entry: LedgerEntry = { ...unhashed, hash: hashEntry(unhashed) };
    await this.sink.append(entry);
    this.head = entry.hash;
    this.length += 1;
    return entry;
  }

  async verify(): Promise<VerifyResult> {
    const entries = await this.sink.all();
    return verifyChain(entries);
  }

  /**
   * Head hash plus length, for external anchoring. Publish this where the
   * application cannot rewrite it; a later chain that does not reproduce a
   * published anchor has been rebuilt.
   */
  async checkpoint(): Promise<{ head: string; length: number; takenAt: string }> {
    const entries = await this.sink.all();
    return {
      head: entries.length === 0 ? GENESIS_HASH : entries[entries.length - 1].hash,
      length: entries.length,
      takenAt: new Date().toISOString(),
    };
  }
}

/**
 * Walk a chain and report the first break.
 *
 * Checks three separate things, because they fail differently: sequence
 * numbers catch deletion and reordering, `prevHash` catches a spliced chain,
 * and recomputing the hash catches an edited field inside an entry whose
 * links still look right.
 */
export function verifyChain(entries: readonly LedgerEntry[]): VerifyResult {
  let expectedPrev = GENESIS_HASH;

  for (let i = 0; i < entries.length; i += 1) {
    const entry = entries[i];

    if (entry.seq !== i) {
      return { ok: false, length: entries.length, brokenAt: i, reason: `sequence gap: expected seq ${i}, found ${entry.seq}` };
    }
    if (!constantTimeEquals(entry.prevHash, expectedPrev)) {
      return { ok: false, length: entries.length, brokenAt: i, reason: `broken link at seq ${i}: prevHash does not match previous entry` };
    }

    const { hash, ...unhashed } = entry;
    const recomputed = hashEntry(unhashed);
    if (!constantTimeEquals(hash, recomputed)) {
      return { ok: false, length: entries.length, brokenAt: i, reason: `content altered at seq ${i}: entry hash does not match its contents` };
    }

    expectedPrev = entry.hash;
  }

  return { ok: true, length: entries.length, head: expectedPrev };
}

function constantTimeEquals(a: string, b: string): boolean {
  const left = Buffer.from(a);
  const right = Buffer.from(b);
  if (left.length !== right.length) return false;
  return timingSafeEqual(left, right);
}

/**
 * Process-wide ledger for the dev/mock runtime. Production wiring replaces the
 * sink with a durable append-only store — see the deployment notes in
 * `clearglass-commerce/VEILGUARD_CONTENT_SHIELD.md`.
 */
let sharedLedger: Ledger | null = null;

export function getLedger(): Ledger {
  if (!sharedLedger) sharedLedger = new Ledger();
  return sharedLedger;
}

/** Test seam: drop the process-wide ledger so each case starts from genesis. */
export function resetLedgerForTesting(): void {
  sharedLedger = null;
}

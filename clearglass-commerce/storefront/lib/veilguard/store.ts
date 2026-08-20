/**
 * VEILGUARD — grant and session state (server only).
 *
 * Holds the two things the rest of the system has to ask about at runtime:
 * which grants have been issued (so a leak can be traced back to one), and
 * what shape this session's recent activity has (so risk can be scored).
 *
 * This implementation is in-memory and per-process: correct for dev, tests and
 * a single node, and explicitly *not* sufficient for a multi-instance
 * deployment, where two replicas would score risk from half the evidence
 * each. Production swaps `GrantStore` for a shared store (Postgres alongside
 * the control plane, or Redis for the counters) — the interface is kept narrow
 * for exactly that reason.
 *
 * Retention is bounded here rather than left to the caller: risk needs a
 * rolling window, not a permanent behavioural profile, and a store that
 * quietly accumulates one is a privacy liability. Grant records outlive the
 * window because leak tracing needs them, but they hold no content and no
 * behavioural history — just the binding required to answer "whose render was
 * this?".
 */

import type { TracerBits } from "./tracer";

/** Rolling window used for every velocity/breadth signal in `risk.ts`. */
export const RISK_WINDOW_MS = 15 * 60 * 1000;

/** How long a grant binding is retained for leak tracing. */
export const GRANT_RETENTION_MS = 180 * 24 * 60 * 60 * 1000;

export type GrantRecord = {
  grantId: string;
  assetId: string;
  subject: string;
  sessionId: string;
  issuedAt: string;
  expiresAt: string;
  tracerBits: TracerBits;
};

type SessionEvent = {
  at: number;
  assetId: string;
  kind: "grant" | "refusal" | "capture_suspicion" | "honeypot" | "automation";
};

type SessionState = {
  events: SessionEvent[];
  firstSeen: number;
};

export class GrantStore {
  private readonly grants = new Map<string, GrantRecord>();
  private readonly sessions = new Map<string, SessionState>();
  private readonly knownDevices = new Map<string, number>();

  recordGrant(record: GrantRecord): void {
    this.grants.set(record.grantId, record);
    this.pruneGrants();
  }

  getGrant(grantId: string): GrantRecord | null {
    return this.grants.get(grantId) ?? null;
  }

  /**
   * Candidate grants for a leak trace.
   *
   * Scoped to one asset on purpose: tracing is an investigation of a specific
   * leaked item, and handing the tracer every grant in the system would widen
   * both the false-match surface and the privacy exposure for no benefit.
   */
  candidatesForAsset(assetId: string): GrantRecord[] {
    return [...this.grants.values()].filter((grant: GrantRecord) => grant.assetId === assetId);
  }

  /**
   * Every retained grant. Used only by beacon resolution, which starts from an
   * identifier that carries no asset context and so cannot be narrowed first.
   */
  allGrants(): GrantRecord[] {
    return [...this.grants.values()];
  }

  recordEvent(sessionId: string, event: SessionEvent): void {
    const state = this.sessions.get(sessionId) ?? { events: [], firstSeen: event.at };
    state.events.push(event);
    state.events = state.events.filter((e: SessionEvent) => event.at - e.at <= RISK_WINDOW_MS);
    this.sessions.set(sessionId, state);
  }

  /** Aggregate the rolling window into the counters `risk.ts` consumes. */
  windowFor(sessionId: string, now: number = Date.now()) {
    const state = this.sessions.get(sessionId);
    if (!state) {
      return {
        distinctAssetsInWindow: 0,
        grantsInWindow: 0,
        failedGrantsInWindow: 0,
        captureSuspicions: 0,
        honeypotTouches: 0,
        automationIndicators: 0,
      };
    }

    const live = state.events.filter((e: SessionEvent) => now - e.at <= RISK_WINDOW_MS);
    const distinct = new Set(live.map((e: SessionEvent) => e.assetId));
    const count = (kind: SessionEvent["kind"]) => live.filter((e: SessionEvent) => e.kind === kind).length;

    return {
      distinctAssetsInWindow: distinct.size,
      grantsInWindow: count("grant"),
      failedGrantsInWindow: count("refusal"),
      captureSuspicions: count("capture_suspicion"),
      honeypotTouches: count("honeypot"),
      automationIndicators: count("automation"),
    };
  }

  /**
   * Device recognition for the `deviceKnown` / `deviceAgeDays` signals.
   *
   * `deviceRef` is a salted first-party token the browser stores after the
   * viewer has been shown the protection notice — not a derived fingerprint.
   * Returns the age in days, or null the first time a token is seen.
   */
  seeDevice(deviceRef: string, now: number = Date.now()): number | null {
    const firstSeen = this.knownDevices.get(deviceRef);
    if (firstSeen === undefined) {
      this.knownDevices.set(deviceRef, now);
      return null;
    }
    return (now - firstSeen) / (24 * 60 * 60 * 1000);
  }

  private pruneGrants(now: number = Date.now()): void {
    for (const [grantId, grant] of this.grants) {
      if (now - Date.parse(grant.issuedAt) > GRANT_RETENTION_MS) this.grants.delete(grantId);
    }
  }
}

let sharedStore: GrantStore | null = null;

export function getGrantStore(): GrantStore {
  if (!sharedStore) sharedStore = new GrantStore();
  return sharedStore;
}

/** Test seam: start each case from an empty store. */
export function resetGrantStoreForTesting(): void {
  sharedStore = null;
}

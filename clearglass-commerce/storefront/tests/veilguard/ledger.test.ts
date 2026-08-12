import test from "node:test";
import assert from "node:assert/strict";

import {
  GENESIS_HASH,
  InMemoryLedgerSink,
  Ledger,
  hashEntry,
  pseudonymize,
  verifyChain,
  type LedgerEntry,
} from "../../lib/veilguard/ledger";

async function seededLedger(count = 5) {
  const sink = new InMemoryLedgerSink();
  const ledger = new Ledger(sink);
  for (let i = 0; i < count; i += 1) {
    await ledger.append({
      action: "render_started",
      subject: `viewer-${i}@example.com`,
      sessionId: `session-${i}`,
      assetId: "concept-draft-atlas",
      grantId: `grant-${i}`,
      riskScore: i * 3,
      detail: { index: i },
      timestamp: new Date(Date.UTC(2026, 0, 1, 0, i)),
    });
  }
  return { ledger, sink };
}

/** The sink stores frozen-by-convention entries; tests mutate copies in place. */
function mutableEntries(sink: InMemoryLedgerSink): LedgerEntry[] {
  return sink.all().map((entry: LedgerEntry) => ({ ...entry }));
}

test("an untouched chain verifies", async () => {
  const { ledger } = await seededLedger();
  const result = await ledger.verify();

  assert.equal(result.ok, true);
  if (result.ok) {
    assert.equal(result.length, 5);
    assert.notEqual(result.head, GENESIS_HASH);
  }
});

test("an empty chain verifies and checkpoints at genesis", async () => {
  const ledger = new Ledger(new InMemoryLedgerSink());
  const result = await ledger.verify();
  const checkpoint = await ledger.checkpoint();

  assert.equal(result.ok, true);
  assert.equal(checkpoint.head, GENESIS_HASH);
  assert.equal(checkpoint.length, 0);
});

test("editing a field inside an entry is detected at that entry", async () => {
  const { sink } = await seededLedger();
  const entries = mutableEntries(sink);

  // The classic quiet edit: downgrade a risk score after the fact, leaving
  // every link intact. Only recomputing the entry's own hash catches this.
  entries[2].riskScore = 0;

  const result = verifyChain(entries);
  assert.equal(result.ok, false);
  if (!result.ok) {
    assert.equal(result.brokenAt, 2);
    assert.match(result.reason, /content altered/);
  }
});

test("deleting an entry is detected", async () => {
  const { sink } = await seededLedger();
  const entries = mutableEntries(sink);
  entries.splice(2, 1);

  const result = verifyChain(entries);
  assert.equal(result.ok, false);
  if (!result.ok) assert.equal(result.brokenAt, 2);
});

test("reordering entries is detected", async () => {
  const { sink } = await seededLedger();
  const entries = mutableEntries(sink);
  const [a, b] = [entries[1], entries[2]];
  entries[1] = b;
  entries[2] = a;

  const result = verifyChain(entries);
  assert.equal(result.ok, false);
});

test("truncating the tail is detected against a published checkpoint", async () => {
  const { ledger, sink } = await seededLedger();
  const anchor = await ledger.checkpoint();

  const truncated = mutableEntries(sink).slice(0, 3);
  const result = verifyChain(truncated);

  // A clean truncation still verifies internally — that is exactly why the
  // external anchor exists. The chain is self-consistent; it just is not the
  // chain that was published.
  assert.equal(result.ok, true);
  if (result.ok) {
    assert.notEqual(result.head, anchor.head, "truncated chain must not reproduce the published head");
    assert.ok(result.length < anchor.length);
  }
});

test("a forged entry appended after a truncation does not reproduce the anchor", async () => {
  const { ledger, sink } = await seededLedger();
  const anchor = await ledger.checkpoint();

  const rebuilt = mutableEntries(sink).slice(0, 3);
  const unhashed = {
    seq: 3,
    timestamp: "2026-01-01T00:03:00.000Z",
    action: "render_started" as const,
    actorRef: pseudonymize("attacker@example.com", "actor"),
    sessionRef: pseudonymize("session-x", "session"),
    assetId: "concept-draft-atlas",
    grantId: "grant-forged",
    riskScore: 0,
    detail: {},
    prevHash: rebuilt[2].hash,
  };
  rebuilt.push({ ...unhashed, hash: hashEntry(unhashed) });

  // An attacker who owns the store can rebuild a *valid* chain...
  assert.equal(verifyChain(rebuilt).ok, true);
  // ...but not one that lands on the head they already published.
  const rebuiltHead = rebuilt[rebuilt.length - 1].hash;
  assert.notEqual(rebuiltHead, anchor.head);
});

test("entry hashes do not depend on property order", () => {
  const base = {
    seq: 0,
    timestamp: "2026-01-01T00:00:00.000Z",
    action: "grant_issued" as const,
    actorRef: "a",
    sessionRef: "b",
    assetId: "asset",
    grantId: "grant",
    riskScore: 12,
    detail: { alpha: 1, beta: "two" },
    prevHash: GENESIS_HASH,
  };

  const reordered = {
    prevHash: GENESIS_HASH,
    detail: { beta: "two", alpha: 1 },
    riskScore: 12,
    grantId: "grant",
    assetId: "asset",
    sessionRef: "b",
    actorRef: "a",
    action: "grant_issued" as const,
    timestamp: "2026-01-01T00:00:00.000Z",
    seq: 0,
  };

  assert.equal(hashEntry(base), hashEntry(reordered));
});

test("the ledger stores pseudonyms, not raw identities", async () => {
  const { sink } = await seededLedger(1);
  const entry = sink.all()[0];

  assert.notEqual(entry.actorRef, "viewer-0@example.com");
  assert.ok(!JSON.stringify(entry).includes("viewer-0@example.com"), "no raw subject should reach the record");
  assert.equal(entry.actorRef, pseudonymize("viewer-0@example.com", "actor"), "pseudonyms must be stable");
});

test("actor and session pseudonyms are domain-separated", () => {
  assert.notEqual(pseudonymize("same-value", "actor"), pseudonymize("same-value", "session"));
});

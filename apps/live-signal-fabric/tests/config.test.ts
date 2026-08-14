import assert from "node:assert/strict";
import test from "node:test";
import { parseEnabledStreams } from "../lib/config";

test("defaults to every declared live stream", () => {
  assert.deepEqual(
    [...parseEnabledStreams(undefined)].sort(),
    ["content", "dashboard", "performance", "public", "status"],
  );
});

test("normalizes whitespace and deduplicates configured streams", () => {
  assert.deepEqual([...parseEnabledStreams(" public, status,public ")].sort(), ["public", "status"]);
});

test("allows an explicitly empty stream set", () => {
  assert.equal(parseEnabledStreams("").size, 0);
});

test("rejects unknown stream names instead of trusting a type cast", () => {
  assert.throws(() => parseEnabledStreams("public,secret-admin"), /Invalid LIVE_FABRIC_ENABLED_STREAMS/);
});

import assert from "node:assert/strict";
import test from "node:test";
import { allowRequest } from "../lib/rate-limit";

test("enforces the configured request count per key", () => {
  const key = "rate-test-basic";
  assert.equal(allowRequest(key, 2), true);
  assert.equal(allowRequest(key, 2), true);
  assert.equal(allowRequest(key, 2), false);
});

test("keeps independent keys isolated", () => {
  assert.equal(allowRequest("rate-test-a", 1), true);
  assert.equal(allowRequest("rate-test-a", 1), false);
  assert.equal(allowRequest("rate-test-b", 1), true);
});

test("fails closed for invalid limiter configuration", () => {
  assert.equal(allowRequest("rate-test-zero", 0), false);
  assert.equal(allowRequest("rate-test-negative", -1), false);
  assert.equal(allowRequest("rate-test-window", 1, 0), false);
  assert.equal(allowRequest("", 1), false);
});

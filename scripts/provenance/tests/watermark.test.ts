// Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
import test from "node:test";
import assert from "node:assert/strict";
import { createMarker, embedWatermark, extractWatermarks, stripWatermarks } from "../watermark.js";

const SECRET = "unit-test-secret-not-for-production";
const PAYLOAD = {
  contentId: "blog/clear-glass-provenance",
  origin: "https://www.clearglassinc.com",
  issuedAt: "2026-08-11T11:41:00Z",
};

test("signed watermark round-trips and verifies", () => {
  const source = "ClearGlass provenance should survive an ordinary copy and paste cycle without changing visible prose.";
  const marked = embedWatermark(source, PAYLOAD, SECRET);
  assert.notEqual(marked, source);
  assert.equal(stripWatermarks(marked), source);

  const found = extractWatermarks(marked, SECRET);
  assert.equal(found.length, 1);
  assert.deepEqual(found[0]?.payload, PAYLOAD);
  assert.equal(found[0]?.verified, true);
});

test("wrong signing secret fails verification", () => {
  const marked = embedWatermark("A sufficiently long provenance test sentence for extraction.", PAYLOAD, SECRET);
  const found = extractWatermarks(marked, "wrong-secret");
  assert.equal(found.length, 1);
  assert.equal(found[0]?.verified, false);
});

test("unsigned inspection reports unknown verification state", () => {
  const marker = createMarker(PAYLOAD, SECRET);
  const found = extractWatermarks(`prefix${marker}suffix`);
  assert.equal(found.length, 1);
  assert.equal(found[0]?.verified, null);
});

test("multiple embedded copies deduplicate to one logical watermark", () => {
  const source = "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen";
  const marked = embedWatermark(source, PAYLOAD, SECRET, { copies: 5 });
  assert.equal(extractWatermarks(marked, SECRET).length, 1);
});

test("ordinary text without markers is unchanged", () => {
  const source = "No provenance marker exists in this text.";
  assert.deepEqual(extractWatermarks(source, SECRET), []);
  assert.equal(stripWatermarks(source), source);
});

test("truncated marker is ignored instead of producing false provenance", () => {
  const marker = createMarker(PAYLOAD, SECRET);
  const truncated = marker.slice(0, -2);
  assert.deepEqual(extractWatermarks(`before${truncated}after`, SECRET), []);
});

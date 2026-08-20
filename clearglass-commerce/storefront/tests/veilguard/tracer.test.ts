import test from "node:test";
import assert from "node:assert/strict";

import {
  TRACER_BITS,
  TRACER_CHARS,
  bitsToCode,
  falseMatchProbability,
  maskedDistance,
  parseTracerCode,
  traceLeak,
  variantsFromBits,
  type TraceCandidate,
  type TracerBits,
} from "../../lib/veilguard/tracer";

function bitsFromSeed(seed: number): TracerBits {
  // Deterministic pseudo-random bits, so a failure is reproducible.
  const bits: number[] = [];
  let state = seed >>> 0;
  for (let i = 0; i < TRACER_BITS; i += 1) {
    state = (state * 1664525 + 1013904223) >>> 0;
    bits.push((state >>> 16) & 1);
  }
  return bits;
}

function candidate(id: string, bits: TracerBits, issuedAt = "2026-01-01T00:00:00.000Z"): TraceCandidate {
  return { grantId: id, assetId: "asset-1", subject: `${id}@example.com`, sessionId: `s-${id}`, issuedAt, bits };
}

test("codes round-trip through encoding and parsing", () => {
  for (let seed = 1; seed <= 50; seed += 1) {
    const bits = bitsFromSeed(seed);
    const code = bitsToCode(bits);
    assert.equal(code.length, TRACER_CHARS);

    const recovered = parseTracerCode(code);
    assert.equal(recovered.knownBits, TRACER_BITS);
    assert.deepEqual([...recovered.bits], [...bits], `seed ${seed} did not round-trip`);
  }
});

test("parsing tolerates the transcription noise a real recovery has", () => {
  const bits = bitsFromSeed(7);
  const code = bitsToCode(bits);

  // Lowercase, hyphenated, and padded with spaces — all of which happen when a
  // code is read off a screen and typed into a form.
  const messy = `${code.slice(0, 4)}-${code.slice(4)}`.toLowerCase();
  assert.deepEqual([...parseTracerCode(messy).bits], [...bits]);
});

test("Crockford confusions decode to the same code", () => {
  // A human reading a watermark cannot reliably tell O from 0 or I from 1;
  // the alphabet excludes the ambiguous glyphs and maps them on input.
  // O→0, I→1, L→1, U→V, so "O1I0LLLU" is the same eight symbols as "0110111V".
  const withAmbiguous = parseTracerCode("O1I0LLLU");
  const canonical = parseTracerCode("0110111V");
  assert.deepEqual([...withAmbiguous.bits], [...canonical.bits]);
});

test("a partial code compares only over the characters that survived", () => {
  const bits = bitsFromSeed(11);
  const code = bitsToCode(bits);

  const partial = parseTracerCode(`${code.slice(0, 4)}????`);
  assert.equal(partial.knownBits, 20, "four legible characters is twenty known bits");
  assert.equal(maskedDistance(partial, bits), 0, "known positions should match exactly");

  // The unknown half must not be silently counted as matching zeroes.
  const decoy = [...bits];
  for (let i = 20; i < TRACER_BITS; i += 1) decoy[i] = decoy[i] ? 0 : 1;
  assert.equal(maskedDistance(partial, decoy), 0, "masked positions must be ignored, not compared");
});

test("false-match probability reflects how much evidence survived", () => {
  // A full clean code is overwhelming evidence.
  assert.ok(falseMatchProbability(40, 0) < 1e-11);
  // Four characters clean is still strong.
  assert.ok(falseMatchProbability(20, 0) < 1e-5);
  // Two characters with two bit errors is not.
  assert.ok(falseMatchProbability(10, 2) > 1e-2);
  // Nothing recovered proves nothing.
  assert.equal(falseMatchProbability(0, 0), 1);
});

test("more errors never make a match look stronger", () => {
  let previous = 0;
  for (let distance = 0; distance <= 8; distance += 1) {
    const p = falseMatchProbability(40, distance);
    assert.ok(p >= previous, `probability fell from ${previous} to ${p} at distance ${distance}`);
    previous = p;
  }
});

test("a full code traces to exactly one grant", () => {
  const target = candidate("g-target", bitsFromSeed(21));
  const others = [candidate("g-a", bitsFromSeed(22)), candidate("g-b", bitsFromSeed(23))];

  const { matches } = traceLeak(bitsToCode(target.bits), [...others, target]);

  assert.equal(matches.length, 1, "unrelated grants should not fall inside the distance bound");
  assert.equal(matches[0].candidate.grantId, "g-target");
  assert.equal(matches[0].distance, 0);
  assert.equal(matches[0].confidence, "conclusive");
});

test("an ambiguous fragment returns every candidate it cannot separate", () => {
  // One legible character is five bits — far too little to single anyone out.
  const a = candidate("g-a", bitsFromSeed(31));
  const b = candidate("g-b", bitsFromSeed(31)); // same bits: genuinely inseparable
  const { matches } = traceLeak(`${bitsToCode(a.bits)[0]}???????`, [a, b]);

  assert.equal(matches.length, 2, "both candidates match the fragment equally");
  assert.equal(matches[0].distance, matches[1].distance);
  assert.ok(
    matches.every((match) => match.confidence === "inconclusive"),
    "five known bits must never read as conclusive",
  );
});

test("tracing reports nothing rather than guessing when no candidate is close", () => {
  const { matches } = traceLeak(bitsToCode(bitsFromSeed(41)), [candidate("g-a", bitsFromSeed(42))], {
    maxDistance: 2,
  });
  assert.equal(matches.length, 0);
});

test("variants are deterministic per tracer and differ between viewers", () => {
  const bitsA = bitsFromSeed(51);
  const bitsB = bitsFromSeed(52);

  assert.deepEqual(variantsFromBits(bitsA), variantsFromBits(bitsA), "same tracer must render identically");
  assert.notDeepEqual(variantsFromBits(bitsA), variantsFromBits(bitsB), "different tracers must render differently");
  assert.equal(variantsFromBits(bitsA, 12).length, 12);
});

test("malformed codes are rejected rather than silently mis-decoded", () => {
  assert.throws(() => parseTracerCode("ABCDEFGHI"), /at most/);
  assert.throws(() => parseTracerCode("ABCDEF!G"), /invalid tracer character/);
  assert.throws(() => bitsToCode([1, 0, 1]), /40 bits/);
});

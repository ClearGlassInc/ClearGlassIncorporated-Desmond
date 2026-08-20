import test from "node:test";
import assert from "node:assert/strict";

import { bandFor, baselineSignals, scoreRisk, summarizeRisk } from "../../lib/veilguard/risk";

test("a clean session scores nominal and says why", () => {
  const assessment = scoreRisk(baselineSignals());

  assert.equal(assessment.score, 0);
  assert.equal(assessment.band, "nominal");
  assert.equal(assessment.override, null);
  assert.equal(assessment.contributions.length, 1);
  assert.match(assessment.contributions[0].reason, /no elevated signals/);
});

test("every point scored is attributed to a named signal", () => {
  const assessment = scoreRisk(
    baselineSignals({ deviceKnown: false, failedGrantsInWindow: 2, anonymizedNetwork: true }),
  );

  const attributed = assessment.contributions.reduce((sum: number, c) => sum + c.points, 0);
  assert.equal(attributed, assessment.score, "the score must equal the sum of its explanations");
  assert.ok(assessment.contributions.every((c) => c.reason.length > 0));
});

test("a honeypot touch forces critical regardless of everything else", () => {
  const assessment = scoreRisk(baselineSignals({ honeypotTouches: 1 }));

  assert.equal(assessment.band, "critical");
  assert.equal(assessment.override, "honeypot_touched");
});

test("no single ordinary signal can reach critical on its own", () => {
  const solo = [
    { deviceKnown: false },
    { distinctAssetsInWindow: 500 },
    { grantsInWindow: 5000 },
    { failedGrantsInWindow: 100 },
    { captureSuspicions: 100 },
    { automationIndicators: 100 },
    { anonymizedNetwork: true },
    { geoVelocityKmh: 40_000 },
  ];

  for (const override of solo) {
    const assessment = scoreRisk(baselineSignals(override));
    assert.notEqual(
      assessment.band,
      "critical",
      `${JSON.stringify(override)} reached critical alone — caps are not holding`,
    );
  }
});

test("signals accumulate into higher bands", () => {
  const assessment = scoreRisk(
    baselineSignals({
      deviceKnown: false,
      distinctAssetsInWindow: 30,
      captureSuspicions: 3,
      failedGrantsInWindow: 2,
    }),
  );

  assert.ok(assessment.score >= 50, `expected a high score, got ${assessment.score}`);
  assert.ok(assessment.band === "high" || assessment.band === "critical");
});

test("scoring is monotone in each signal", () => {
  const base = scoreRisk(baselineSignals()).score;

  const worse = [
    baselineSignals({ deviceKnown: false }),
    baselineSignals({ distinctAssetsInWindow: 13 }),
    baselineSignals({ captureSuspicions: 2 }),
    baselineSignals({ failedGrantsInWindow: 1 }),
  ];

  for (const signals of worse) {
    assert.ok(scoreRisk(signals).score > base, "a worse signal must never lower the score");
  }
});

test("scores are clamped to the 0-100 band range", () => {
  const assessment = scoreRisk(
    baselineSignals({
      deviceKnown: false,
      distinctAssetsInWindow: 999,
      grantsInWindow: 999,
      failedGrantsInWindow: 999,
      captureSuspicions: 999,
      automationIndicators: 999,
      anonymizedNetwork: true,
      geoVelocityKmh: 99_999,
      honeypotTouches: 9,
    }),
  );

  assert.ok(assessment.score <= 100);
  assert.ok(assessment.score >= 0);
});

test("a VPN alone is treated as uncertainty, not misuse", () => {
  const assessment = scoreRisk(baselineSignals({ anonymizedNetwork: true }));
  assert.equal(assessment.band, "nominal", "an anonymised network must not by itself degrade access");
});

test("band thresholds line up with the documented ranges", () => {
  assert.equal(bandFor(0), "nominal");
  assert.equal(bandFor(24), "nominal");
  assert.equal(bandFor(25), "elevated");
  assert.equal(bandFor(49), "elevated");
  assert.equal(bandFor(50), "high");
  assert.equal(bandFor(74), "high");
  assert.equal(bandFor(75), "critical");
  assert.equal(bandFor(100), "critical");
});

test("the ledger summary names the strongest contributors", () => {
  const assessment = scoreRisk(baselineSignals({ deviceKnown: false, captureSuspicions: 3 }));
  const summary = summarizeRisk(assessment);

  assert.match(summary, /^\d+\//);
  assert.match(summary, /captureSuspicions\+/);
});

import test from "node:test";
import assert from "node:assert/strict";

import {
  can,
  resolvePolicy,
  serializePolicy,
  type Capability,
  type Classification,
  type RiskBand,
  type ViewerPlan,
} from "../../lib/veilguard/policy";

const CLASSIFICATIONS: Classification[] = ["public", "internal", "confidential", "restricted"];
const PLANS: ViewerPlan[] = ["anonymous", "premium", "operator"];
const BANDS: RiskBand[] = ["nominal", "elevated", "high", "critical"];

/**
 * The central invariant of the whole gate: resolution only ever *subtracts*.
 * If this ever fails, some combination of tier, plan and risk is handing out a
 * capability that one of the three never granted — which is precisely the bug
 * class the design exists to make impossible.
 */
test("capabilities never exceed the anonymous-plan ceiling for any combination", () => {
  const ANONYMOUS_CEILING: Capability[] = ["view"];

  for (const classification of CLASSIFICATIONS) {
    for (const riskBand of BANDS) {
      const policy = resolvePolicy({ classification, plan: "anonymous", riskBand });
      for (const capability of policy.capabilities) {
        assert.ok(
          ANONYMOUS_CEILING.includes(capability),
          `anonymous viewer gained "${capability}" on ${classification}/${riskBand}`,
        );
      }
    }
  }
});

test("raising risk never adds a capability", () => {
  for (const classification of CLASSIFICATIONS) {
    for (const plan of PLANS) {
      for (let i = 1; i < BANDS.length; i += 1) {
        const lower = resolvePolicy({ classification, plan, riskBand: BANDS[i - 1] });
        const higher = resolvePolicy({ classification, plan, riskBand: BANDS[i] });

        for (const capability of higher.capabilities) {
          assert.ok(
            lower.capabilities.has(capability),
            `${classification}/${plan}: "${capability}" appeared when risk rose to ${BANDS[i]}`,
          );
        }
      }
    }
  }
});

test("raising classification never adds a capability", () => {
  for (const plan of PLANS) {
    for (const riskBand of BANDS) {
      for (let i = 1; i < CLASSIFICATIONS.length; i += 1) {
        const looser = resolvePolicy({ classification: CLASSIFICATIONS[i - 1], plan, riskBand });
        const tighter = resolvePolicy({ classification: CLASSIFICATIONS[i], plan, riskBand });

        for (const capability of tighter.capabilities) {
          assert.ok(
            looser.capabilities.has(capability),
            `${plan}/${riskBand}: "${capability}" appeared at ${CLASSIFICATIONS[i]}`,
          );
        }
      }
    }
  }
});

test("restricted content is never downloadable or exportable, at any plan or risk", () => {
  for (const plan of PLANS) {
    for (const riskBand of BANDS) {
      const policy = resolvePolicy({ classification: "restricted", plan, riskBand });
      assert.equal(can(policy, "download"), false, `download granted to ${plan}/${riskBand}`);
      assert.equal(can(policy, "export"), false, `export granted to ${plan}/${riskBand}`);
      assert.equal(can(policy, "share"), false, `share granted to ${plan}/${riskBand}`);
    }
  }
});

test("critical risk withdraws viewing entirely", () => {
  for (const classification of CLASSIFICATIONS) {
    for (const plan of PLANS) {
      const policy = resolvePolicy({ classification, plan, riskBand: "critical" });
      assert.equal(policy.capabilities.size, 0, `${classification}/${plan} kept capabilities at critical risk`);
      assert.equal(policy.grantTtlSeconds, 0, "a critical-risk grant must not be usable");
    }
  }
});

test("per-asset denials are honoured even when tier and plan would allow", () => {
  const policy = resolvePolicy({
    classification: "internal",
    plan: "operator",
    riskBand: "nominal",
    denyCapabilities: ["download", "copy_text"],
  });

  assert.equal(can(policy, "download"), false);
  assert.equal(can(policy, "copy_text"), false);
  assert.equal(can(policy, "view"), true, "an unrelated capability was withdrawn");
  assert.ok(
    policy.rationale.some((entry: string) => entry.startsWith("asset_denies:")),
    "the denial should be explained in the rationale",
  );
});

test("losing full-resolution always narrows the render rather than leaving it uncapped", () => {
  // `public` has no baseline cap, so this is the case where a naive
  // implementation would hand an elevated-risk viewer an unlimited edge.
  const capped = resolvePolicy({ classification: "public", plan: "anonymous", riskBand: "nominal" });

  assert.equal(can(capped, "view_full_resolution"), false, "precondition: anonymous has no full-resolution");
  assert.ok(capped.maxRenderedEdgePx !== null, "an uncapped tier must still gain a preview cap");
  assert.ok((capped.maxRenderedEdgePx ?? Infinity) <= 900);
});

test("TTLs shorten monotonically as risk rises", () => {
  let previousGrant = Infinity;
  let previousRender = Infinity;

  for (const riskBand of BANDS) {
    const policy = resolvePolicy({ classification: "confidential", plan: "operator", riskBand });
    assert.ok(policy.grantTtlSeconds <= previousGrant, `grant TTL grew at ${riskBand}`);
    assert.ok(policy.renderTtlSeconds <= previousRender, `render TTL grew at ${riskBand}`);
    previousGrant = policy.grantTtlSeconds;
    previousRender = policy.renderTtlSeconds;
  }
});

test("serialized policy is stable and carries its rationale", () => {
  const policy = resolvePolicy({ classification: "confidential", plan: "premium", riskBand: "elevated" });
  const wire = serializePolicy(policy);

  assert.deepEqual(wire.capabilities, [...wire.capabilities].sort(), "capabilities should be sorted for stable output");
  assert.ok(wire.rationale.includes("classification:confidential"));
  assert.ok(wire.rationale.includes("risk:elevated"));
  assert.equal(wire.requireVisibleWatermark, true);
});

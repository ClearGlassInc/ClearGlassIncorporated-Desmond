// Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
// Proprietary and confidential. See LICENSE for terms.
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  AmountError,
  assertMinorAmount,
  formatMinor,
  minorUnitExponent,
  normalizeCurrency,
  toMinorUnits,
} from "../money.js";

describe("currency handling", () => {
  it("normalises ISO-4217 codes to the lowercase form Stripe stores", () => {
    assert.equal(normalizeCurrency("CAD"), "cad");
    assert.equal(normalizeCurrency(" usd "), "usd");
  });

  it("rejects anything that is not a three-letter code", () => {
    assert.throws(() => normalizeCurrency("dollars"), AmountError);
    assert.throws(() => normalizeCurrency("C$"), AmountError);
    assert.throws(() => normalizeCurrency(undefined), AmountError);
  });

  it("knows which currencies have no minor unit and which have three", () => {
    assert.equal(minorUnitExponent("cad"), 2);
    assert.equal(minorUnitExponent("JPY"), 0);
    assert.equal(minorUnitExponent("kwd"), 3);
  });
});

describe("major to minor unit conversion", () => {
  it("converts the decimal prices the side store lists", () => {
    assert.equal(toMinorUnits(6.99, "cad"), 699);
    assert.equal(toMinorUnits(8.49, "cad"), 849);
    assert.equal(toMinorUnits(4.99, "cad"), 499);
    assert.equal(toMinorUnits(12, "cad"), 1200);
  });

  it("does not lose a cent to float rounding", () => {
    // 6.99 * 100 is 698.9999999999999 in IEEE-754. Every price in the side
    // store catalogue must survive the round trip exactly.
    for (const dollars of [0.01, 1.29, 6.99, 8.49, 19.99, 29.99, 129.99, 1234.56]) {
      assert.equal(toMinorUnits(dollars, "cad"), Math.round(dollars * 100));
    }
  });

  it("accepts numeric strings with thousands separators", () => {
    assert.equal(toMinorUnits("2,500.00", "cad"), 250000);
    assert.equal(toMinorUnits("249", "cad"), 24900);
  });

  it("honours zero-decimal currencies", () => {
    assert.equal(toMinorUnits(500, "jpy"), 500);
    assert.throws(() => toMinorUnits(5.5, "jpy"), AmountError);
  });

  it("rejects more precision than the currency can express", () => {
    assert.throws(() => toMinorUnits(1.005, "cad"), AmountError);
  });

  it("rejects zero, negative, and non-numeric prices", () => {
    assert.throws(() => toMinorUnits(0, "cad"), AmountError);
    assert.throws(() => toMinorUnits(-5, "cad"), AmountError);
    assert.throws(() => toMinorUnits("free", "cad"), AmountError);
    assert.throws(() => toMinorUnits(null, "cad"), AmountError);
    assert.throws(() => toMinorUnits(Number.NaN, "cad"), AmountError);
    assert.throws(() => toMinorUnits(Number.POSITIVE_INFINITY, "cad"), AmountError);
  });
});

describe("minor amount validation", () => {
  it("accepts a positive integer", () => {
    assert.equal(assertMinorAmount(24900, "cad"), 24900);
  });

  it("rejects floats, zero, negatives and oversized amounts", () => {
    assert.throws(() => assertMinorAmount(249.5, "cad"), AmountError);
    assert.throws(() => assertMinorAmount(0, "cad"), AmountError);
    assert.throws(() => assertMinorAmount(-1, "cad"), AmountError);
    assert.throws(() => assertMinorAmount(100_000_000, "cad"), AmountError);
    assert.throws(() => assertMinorAmount("24900", "cad"), AmountError);
  });

  it("enforces Stripe's multiple-of-ten rule for three-decimal currencies", () => {
    assert.equal(assertMinorAmount(1230, "kwd"), 1230);
    assert.throws(() => assertMinorAmount(1234, "kwd"), AmountError);
  });
});

describe("formatting for the report", () => {
  it("renders minor units back to a major-unit string", () => {
    assert.equal(formatMinor(699, "cad"), "6.99");
    assert.equal(formatMinor(24900, "cad"), "249.00");
    assert.equal(formatMinor(5, "cad"), "0.05");
    assert.equal(formatMinor(500, "jpy"), "500");
  });
});

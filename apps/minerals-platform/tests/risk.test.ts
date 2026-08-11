import { describe, expect, it } from "vitest";
import { calculateRisk, hhi } from "@/lib/risk";

describe("risk engine", () => {
  it("returns UNKNOWN when less than half of configured weight has evidence", () => {
    const result = calculateRisk([
      { key: "geopolitical", score: 80, weight: 0.2 },
      { key: "regulatory", score: null, weight: 0.4 },
      { key: "logistics", score: null, weight: 0.4 }
    ]);
    expect(result.score).toBeNull();
    expect(result.severity).toBe("UNKNOWN");
    expect(result.coverage).toBeCloseTo(0.2);
  });

  it("normalizes available weights without inventing missing scores", () => {
    const result = calculateRisk([
      { key: "geopolitical", score: 80, weight: 0.4 },
      { key: "regulatory", score: 40, weight: 0.4 },
      { key: "logistics", score: null, weight: 0.2 }
    ]);
    expect(result.score).toBe(60);
    expect(result.severity).toBe("MODERATE");
    expect(result.coverage).toBeCloseTo(0.8);
  });

  it("classifies critical scores at 85 or above", () => {
    expect(calculateRisk([{ key: "combined", score: 90, weight: 1 }]).severity).toBe("CRITICAL");
  });
});

describe("HHI", () => {
  it("computes concentration from normalized shares", () => {
    expect(hhi([60, 20, 10, 10])).toBe(4200);
  });

  it("returns zero for empty evidence", () => {
    expect(hhi([])).toBe(0);
  });
});

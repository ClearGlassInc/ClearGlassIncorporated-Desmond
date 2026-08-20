import { z } from "zod";

export const riskComponentSchema = z.object({
  key: z.string().min(1).max(80),
  score: z.number().min(0).max(100).nullable(),
  weight: z.number().min(0).max(1),
  confidence: z.number().min(0).max(1).optional()
});

export type RiskComponent = z.infer<typeof riskComponentSchema>;

export type RiskResult = {
  score: number | null;
  severity: "LOW" | "MODERATE" | "HIGH" | "CRITICAL" | "UNKNOWN";
  coverage: number;
  weightedInputs: Array<RiskComponent & { effectiveWeight: number }>;
  methodology: "weighted-mean-v1";
};

export function calculateRisk(components: RiskComponent[]): RiskResult {
  const parsed = z.array(riskComponentSchema).parse(components);
  const configuredWeight = parsed.reduce((sum, item) => sum + item.weight, 0);
  const usable = parsed.filter((item) => item.score !== null && item.weight > 0);
  const usableWeight = usable.reduce((sum, item) => sum + item.weight, 0);
  const coverage = configuredWeight > 0 ? usableWeight / configuredWeight : 0;
  if (!usable.length || usableWeight === 0 || coverage < 0.5) {
    return { score: null, severity: "UNKNOWN", coverage, weightedInputs: usable.map((item) => ({ ...item, effectiveWeight: 0 })), methodology: "weighted-mean-v1" };
  }
  const weightedInputs = usable.map((item) => ({ ...item, effectiveWeight: item.weight / usableWeight }));
  const score = weightedInputs.reduce((sum, item) => sum + Number(item.score) * item.effectiveWeight, 0);
  const rounded = Math.round(score * 100) / 100;
  const severity = rounded >= 85 ? "CRITICAL" : rounded >= 67 ? "HIGH" : rounded >= 34 ? "MODERATE" : "LOW";
  return { score: rounded, severity, coverage, weightedInputs, methodology: "weighted-mean-v1" };
}

export function hhi(shares: number[]): number {
  const clean = shares.filter((value) => Number.isFinite(value) && value >= 0);
  const total = clean.reduce((sum, value) => sum + value, 0);
  if (!clean.length || total <= 0) return 0;
  return Math.round(clean.reduce((sum, value) => sum + Math.pow((value / total) * 100, 2), 0) * 100) / 100;
}

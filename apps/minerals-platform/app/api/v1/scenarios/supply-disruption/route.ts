import type { NextRequest } from "next/server";
import { z } from "zod";
import { failure, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";

const scenarioSchema = z.object({
  name: z.string().trim().min(1).max(120),
  affectedSupplySharePercent: z.number().min(0).max(100),
  affectedOutputReductionPercent: z.number().min(0).max(100),
  alternativeSupplyPercentOfBaseline: z.number().min(0).max(100).default(0),
  strategicStockpilePercentOfBaseline: z.number().min(0).max(100).default(0),
  demandResponsePercentOfBaseline: z.number().min(0).max(100).default(0)
});
const schema = z.object({ baselineSupply: z.number().positive().default(100), baselineDemand: z.number().positive().default(100), scenarios: z.array(scenarioSchema).min(1).max(12) });

export async function POST(request: NextRequest) {
  try {
    requireRole(resolvePrincipal(request), "ANALYST");
    const input = schema.parse(await request.json());
    const results = input.scenarios.map((scenario) => {
      const grossLossPercent = scenario.affectedSupplySharePercent * scenario.affectedOutputReductionPercent / 100;
      const mitigationPercent = scenario.alternativeSupplyPercentOfBaseline + scenario.strategicStockpilePercentOfBaseline + scenario.demandResponsePercentOfBaseline;
      const netShortfallPercent = Math.max(0, grossLossPercent - mitigationPercent);
      const disruptedSupply = input.baselineSupply * (1 - grossLossPercent / 100) + input.baselineSupply * (scenario.alternativeSupplyPercentOfBaseline + scenario.strategicStockpilePercentOfBaseline) / 100;
      const adjustedDemand = input.baselineDemand * (1 - scenario.demandResponsePercentOfBaseline / 100);
      return {
        ...scenario,
        grossSupplyLossPercent: grossLossPercent,
        totalMitigationPercentOfBaseline: mitigationPercent,
        netShortfallPercentOfBaseline: netShortfallPercent,
        modeledAvailableSupply: disruptedSupply,
        modeledDemand: adjustedDemand,
        modeledBalance: disruptedSupply - adjustedDemand
      };
    });
    return success({
      baseline: { supply: input.baselineSupply, demand: input.baselineDemand, balance: input.baselineSupply - input.baselineDemand },
      scenarios: results,
      methodology: "Deterministic user-supplied arithmetic. Alternative supply and stockpile increase available supply; demand response reduces modeled demand.",
      warning: "SCENARIO ANALYSIS — NOT A FORECAST. No probability, price response, hidden elasticity, or unobserved supply is inferred."
    });
  } catch (error) { return failure(error); }
}

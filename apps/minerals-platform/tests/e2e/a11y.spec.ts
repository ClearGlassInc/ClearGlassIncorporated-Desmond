import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("command center has no serious or critical accessibility violations", async ({ page }) => {
  await page.goto("/");
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]).analyze();
  const blocking = results.violations.filter((violation) => violation.impact === "critical" || violation.impact === "serious");
  expect(blocking, blocking.map((item) => `${item.id}: ${item.help}`).join("\n")).toEqual([]);
});

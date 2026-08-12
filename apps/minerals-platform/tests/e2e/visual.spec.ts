import { expect, test } from "@playwright/test";

test("desktop command center visual baseline", async ({ page }) => {
  test.skip(process.env.VISUAL_REGRESSION !== "1", "Set VISUAL_REGRESSION=1 after generating reviewed baselines with --update-snapshots");
  await page.goto("/");
  await expect(page).toHaveScreenshot("command-center-desktop.png", { fullPage: true, animations: "disabled", maxDiffPixelRatio: 0.01 });
});

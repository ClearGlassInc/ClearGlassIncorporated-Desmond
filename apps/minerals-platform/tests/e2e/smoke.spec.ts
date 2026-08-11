import { expect, test } from "@playwright/test";

test("renders the enterprise command shell", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Critical minerals");
  await expect(page.getByText("SOURCE-GROUNDED MODE")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Global Mineral Map" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Market Series" })).toBeVisible();
});

test("keeps primary analytical modules discoverable on mobile", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("link", { name: "Risk Radar" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Data Sources" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Reports" })).toBeVisible();
});

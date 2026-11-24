import { test, expect } from "@playwright/test";

test("provisioned Grafana dashboards use the live local datasources", async ({
  page,
}) => {
  await page.goto("http://127.0.0.1:3000/login");
  await page.getByRole("textbox", { name: "Email or username" }).fill("admin");
  await page.getByLabel("Password", { exact: true }).fill("demo-grafana-local");
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await page.waitForURL("http://127.0.0.1:3000/");
  await page.goto("http://127.0.0.1:3000/d/ortelana-operations");
  await expect(
    page.getByRole("heading", { name: "API scrape availability", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: "Persisted execution states",
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.getByText("Data source not found")).toHaveCount(0);
  await page.screenshot({
    path: "../docs/screenshots/grafana-operations-demo.png",
    fullPage: true,
  });
  await page.goto("http://127.0.0.1:3000/d/ortelana-business");
  await expect(
    page.getByRole("heading", {
      name: "Observed reporting-year metres (latest imported snapshot)",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: "Observed branch volume, latest reporting year",
      exact: true,
    }),
  ).toBeVisible();
  await page.screenshot({
    path: "../docs/screenshots/grafana-business-demo.png",
    fullPage: true,
  });
});

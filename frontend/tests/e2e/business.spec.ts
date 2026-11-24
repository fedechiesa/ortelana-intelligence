import { test, expect } from "@playwright/test";
test("connected demo analysis and authenticated human approval", async ({
  page,
  request,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await page
    .getByRole("button", { name: "Supervisor · review & decide" })
    .click();
  await page.getByRole("button", { name: "Open workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Business overview" }),
  ).toBeVisible();
  await expect(page.getByText("Observed sales", { exact: true })).toBeVisible();
  await expect(page.getByText("Unable to complete this request")).toHaveCount(
    0,
  );
  await page.screenshot({
    path: "../docs/screenshots/overview-demo.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Run analysis", exact: true }).click();
  await page
    .getByRole("combobox", { name: "Product", exact: true })
    .selectOption("DEMO-003");
  await page.getByRole("button", { name: "Start analysis" }).click();
  const detail = page.getByRole("dialog", { name: "Analysis evidence" });
  await expect(
    detail.getByText("Pending review", { exact: true }),
  ).toBeVisible();
  await expect(detail.getByText("Checkpoint paused")).toBeVisible();
  await page.screenshot({
    path: "../docs/screenshots/critical-review-demo.png",
    fullPage: true,
  });
  await detail.getByRole("button", { name: "Close dialog" }).click();
  await page.getByRole("button", { name: /^Human review/ }).click();
  const card = page
    .locator(".review-card")
    .filter({ hasText: "DEMO-003" })
    .first();
  await card
    .getByRole("button", { name: "Review decision", exact: true })
    .click();
  const decision = page.getByRole("dialog", {
    name: "Record a human decision",
  });
  await decision
    .getByRole("textbox", { name: "Decision comment" })
    .fill("SYNTHETIC DEMO E2E: reviewed the matched evidence and policy.");
  await decision.getByRole("button", { name: "Approve simulation" }).click();
  await expect(decision).toHaveCount(0);
  await expect(
    page.getByRole("cell", { name: "Approved", exact: true }).first(),
  ).toBeVisible();
  await page.screenshot({
    path: "../docs/screenshots/decision-history-demo.png",
    fullPage: true,
  });
  const decisions = await request.get("/api/decisions", {
    headers: { Authorization: "Bearer demo-supervisor-local" },
  });
  expect(decisions.ok()).toBeTruthy();
  const latest = (await decisions.json()).items[0];
  const duplicate = await request.post("/api/decision", {
    headers: { Authorization: "Bearer demo-supervisor-local" },
    data: {
      ejecucion_id: latest.execution_id,
      decision: "APROBADO",
      comentario: "Duplicate must be rejected",
    },
  });
  expect(duplicate.status()).toBe(409);
  await page
    .getByRole("button", { name: "Sales analytics", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Product ranking" }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Product", exact: true })
    .selectOption("DEMO-002");
  await expect(
    page.getByRole("cell", { name: "Warning", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "System monitoring", exact: true })
    .click();
  await expect(page.getByText("connected", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Settings", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Independent synthetic dataset" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Switch to dark mode" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("button", { name: "Switch to light mode" }).click();
  await page.getByRole("button", { name: "Overview", exact: true }).click();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator(".toast").waitFor({ state: "hidden", timeout: 6000 });
  await page.screenshot({
    path: "../docs/screenshots/mobile-demo.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.getByRole("button", { name: "Open menu" }).click();
  await expect(
    page.getByRole("button", { name: "Sales analytics", exact: true }),
  ).toBeVisible();
});

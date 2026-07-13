const { test, expect } = require("@playwright/test");

function collectBrowserErrors(page) {
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  return errors;
}

async function expectNoHorizontalOverflow(page) {
  const dimensions = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    page: document.documentElement.scrollWidth,
    body: document.body.scrollWidth,
  }));
  expect(dimensions.page).toBe(dimensions.viewport);
  expect(dimensions.body).toBe(dimensions.viewport);
}

async function expectSelectedTrajectory(page, scenarioId) {
  const image = page.locator("#scenarioImage");
  await expect(image).toHaveAttribute("src", new RegExp(`${scenarioId}\\.svg$`));
  await expect.poll(() => image.evaluate((node) => node.naturalWidth)).toBeGreaterThan(0);
}

async function expectLinksResolve(page, selector) {
  const statuses = await page.locator(selector).evaluateAll(async (links) => Promise.all(
    links.map(async (link) => (await fetch(link.href)).status),
  ));
  expect(statuses.every((status) => status === 200)).toBe(true);
}

test("public Explorer exposes run evidence and the complete case workflow", async ({ page }) => {
  const errors = collectBrowserErrors(page);
  await page.setViewportSize({ width: 1600, height: 1000 });
  await page.goto("http://127.0.0.1:8131/demo/");

  await expect(page.locator("#runStatus")).toHaveText("Run ready");
  await expect(page.locator("#heroAnalyzedCount")).toHaveText("1,193");
  await expect(page.locator("#pipelineStatus")).toHaveText("3/3 ready");
  await expect(page.locator(".stage-card")).toHaveCount(3);
  await expect(page.locator("#resultCount")).toHaveText("14 of 14 scenarios");
  await expectSelectedTrajectory(page, "synthetic_dense_intersection_vru");

  await page.getByRole("checkbox", { name: "cyclist interaction" }).check();
  await expect(page.locator("#resultCount")).toHaveText("3 of 14 scenarios");
  await page.locator("#sortSelect").selectOption("fde-desc");
  await page.getByRole("row", { name: /Synthetic Cyclist Close Pass/ }).click();
  await expect(page.locator("#detailTitle")).toHaveText("Synthetic Cyclist Close Pass");
  await expectSelectedTrajectory(page, "synthetic_cyclist_close_pass");

  await page.getByText("Reports", { exact: true }).click();
  await expect(page.locator("#reportLinks a")).toHaveCount(7);
  await expect(
    page.getByRole("link", { name: /Frozen selector holdout/ }),
  ).toHaveAttribute("href", "../reports/waymo_selector_holdout_993.md");
  await expectLinksResolve(page, "#primaryReportLink, #reportLinks a, .stage-card a");
  await expectNoHorizontalOverflow(page);
  expect(errors).toEqual([]);
});

test("public Explorer remains contained on a mobile viewport", async ({ page }) => {
  const errors = collectBrowserErrors(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("http://127.0.0.1:8131/demo/");

  await expect(page.locator("#runStatus")).toHaveText("Run ready");
  await expect(page.locator("#heroPeakMemory")).toHaveText("1.92 GB");
  await expect(page.locator(".stage-card")).toHaveCount(3);
  await expectNoHorizontalOverflow(page);
  expect(errors).toEqual([]);
});

test("generated run Explorer loads portable assets and report links", async ({ page }) => {
  const errors = collectBrowserErrors(page);
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("http://127.0.0.1:8132/explorer/");

  await expect(page.locator("#runStatus")).toHaveText("Run ready");
  await expect(page.locator("#runSubtitle")).toContainText(
    "Local analysis: 11 scenarios across 1 source, with 6 ranked cases",
  );
  await expect(page.locator("#selectorAtlasPanel")).toBeHidden();
  await expect(page.locator("#resultCount")).toHaveText("6 of 6 scenarios");
  await expectSelectedTrajectory(page, "synthetic_dense_intersection_vru");

  await expectLinksResolve(page, "#primaryReportLink, #reportLinks a, .stage-card a");
  await expectNoHorizontalOverflow(page);
  expect(errors).toEqual([]);
});

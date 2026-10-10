/** Read-only image acceptance checks; local backend and Vite must already be running. */
import { chromium } from "../frontend/node_modules/@playwright/test/index.mjs";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import path from "node:path";
import assert from "node:assert/strict";

const root = fileURLToPath(new URL("../", import.meta.url));
const base = process.env.WUSHENG_TEST_BASE_URL || "http://127.0.0.1:5173";
const backend = process.env.WUSHENG_TEST_API_URL || "http://127.0.0.1:8000";
const output = path.join(root, "docs/competition/consumable-images");
await mkdir(output, { recursive: true });
const manifest = JSON.parse(
  await readFile(path.join(root, "docs/references/consumable-image-assets.json"), "utf8"),
);
const baselineIndex = process.argv.indexOf("--baseline");
const baselineDirectory = baselineIndex < 0 ? null : process.argv[baselineIndex + 1];
const baseline = baselineDirectory
  ? JSON.parse(await readFile(path.join(baselineDirectory, "layout-before.json"), "utf8"))
  : [
      { width: 1920, height: 1080 },
      { width: 1366, height: 768 },
      { width: 390, height: 844 },
    ].map((viewport) => ({ viewport }));
const report = {
  checkedAt: new Date().toISOString(),
  checks: [],
  assets: [],
  layouts: [],
  routes: [],
};
const check = (condition, name) => {
  assert(condition, name);
  report.checks.push(name);
};
check((await fetch(backend + "/health")).ok, "Backend /health");
check(
  (
    await fetch(backend + "/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ itemId: "headphones", question: "保修状态" }),
    })
  ).ok,
  "Backend /generate",
);
check((await fetch(base)).ok, "Frontend dev server");
const snapshot = await (await fetch(backend + "/snapshot")).json();
if (baselineDirectory) {
  assert.deepEqual(
    snapshot,
    JSON.parse(await readFile(path.join(baselineDirectory, "snapshot-before.json"), "utf8")),
  );
  report.checks.push(
    "Entire database snapshot unchanged (all item and consumable text, values and statuses)",
  );
}
for (const asset of manifest) {
  const local = await readFile(path.join(root, "frontend/public", asset.assetPath));
  check(
    createHash("sha256").update(local).digest("hex").toUpperCase() === asset.sha256,
    asset.consumableId + ": unchanged original hash",
  );
  check(
    local.readUInt32BE(16) === asset.width && local.readUInt32BE(20) === asset.height,
    asset.consumableId + ": PNG dimensions",
  );
  const response = await fetch(base + asset.assetPath);
  check(
    response.ok && response.headers.get("content-type").includes("image/png"),
    asset.consumableId + ": PNG served",
  );
  check(
    createHash("sha256")
      .update(Buffer.from(await response.arrayBuffer()))
      .digest("hex")
      .toUpperCase() === asset.sha256,
    asset.consumableId + ": HTTP original bytes",
  );
  report.assets.push(asset);
}
const browser = await chromium.launch({
  channel: "msedge",
  ...(process.env.WUSHENG_EDGE_PATH ? { executablePath: process.env.WUSHENG_EDGE_PATH } : {}),
  headless: true,
});
const errors = [];
const watch = (page) => {
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.text().includes("[Wusheng ProductImage]")) errors.push(message.text());
  });
  page.on("response", (response) => {
    if (response.url().includes("/assets/") && response.status() >= 400)
      errors.push(response.url());
  });
};
const settle = async (page) => {
  for (const frame of await page.locator(".product-image").all()) {
    if (!(await frame.isVisible())) continue;
    await frame.evaluate((el) => el.scrollIntoView({ block: "nearest", behavior: "instant" }));
    await page.waitForFunction(
      (el) => el.dataset.imageState === "loaded",
      await frame.elementHandle(),
    );
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(750);
};
const audit = async (page, route) => {
  const images = await page
    .locator(".consumable-image > img")
    .evaluateAll((nodes) =>
      nodes.map((img) => ({
        src: new URL(img.currentSrc).pathname,
        width: img.naturalWidth,
        height: img.naturalHeight,
        fit: getComputedStyle(img).objectFit,
      })),
    );
  check(
    images.every(
      (img) =>
        img.src.startsWith("/assets/consumables/") &&
        img.width === 1448 &&
        img.height === 1086 &&
        img.fit === "contain",
    ),
    route + ": HD consumables contain, no legacy images",
  );
  report.routes.push({ route, images });
};
try {
  for (const before of baseline) {
    const page = await browser.newPage({ viewport: before.viewport });
    watch(page);
    await page.goto(base + "/consumables");
    await page.locator(".consumable-card").nth(5).waitFor();
    await settle(page);
    if (before.boxes) {
      const boxes = await page.evaluate(
        (selectors) =>
          Object.fromEntries(
            selectors.map((selector) => [
              selector,
              [...document.querySelectorAll(selector)].map((n) => {
                const r = n.getBoundingClientRect();
                return { x: r.x, y: r.y, w: r.width, h: r.height };
              }),
            ]),
          ),
        Object.keys(before.boxes),
      );
      for (const selector of Object.keys(before.boxes)) {
        assert.equal(boxes[selector].length, before.boxes[selector].length);
        for (let index = 0; index < boxes[selector].length; index++)
          for (const key of ["x", "y", "w", "h"])
            check(
              Math.abs(boxes[selector][index][key] - before.boxes[selector][index][key]) < 0.5,
              `${before.viewport.width}: ${selector} ${index} preserved ${key}`,
            );
      }
      check(
        (await page.locator("main.page").innerText()) === before.text,
        before.viewport.width + ": all page text/numbers unchanged",
      );
    }
    for (const asset of manifest) {
      const card = page
        .locator(".consumable-card")
        .filter({ has: page.getByRole("heading", { name: asset.name, exact: true }) });
      const image = card.locator(".consumable-image img");
      check(
        (await image.getAttribute("src")) === asset.assetPath,
        asset.consumableId + ": correct card asset",
      );
      check(
        await card
          .locator(".consumable-image")
          .evaluate((el) => getComputedStyle(el).backgroundColor === "rgb(255, 255, 255)"),
        asset.consumableId + ": white frame",
      );
    }
    await audit(page, "/consumables " + before.viewport.width);
    await page.screenshot({
      path: path.join(output, `consumables-${before.viewport.width}.png`),
      fullPage: true,
    });
    report.layouts.push({ viewport: before.viewport, identicalToBaseline: Boolean(before.boxes) });
    if (before.viewport.width === 1920) {
      await page.locator(".consumable-card").first().hover();
      await page.waitForTimeout(400);
      check(
        await page
          .locator(".consumable-card .consumable-image img")
          .first()
          .evaluate(
            (img) => Math.abs(new DOMMatrix(getComputedStyle(img).transform).a - 1.02) < 0.001,
          ),
        "Consumable image hover scale 1.02",
      );
      for (const asset of manifest) {
        await page
          .locator(".consumable-card")
          .filter({ has: page.getByRole("heading", { name: asset.name, exact: true }) })
          .click();
        await page.locator(".consumable-drawer-hero").waitFor();
        await settle(page);
        check(
          (await page.locator(".consumable-drawer-hero img").getAttribute("src")) ===
            asset.assetPath,
          asset.consumableId + ": drawer uses same original",
        );
        await audit(page, "/consumables drawer " + asset.consumableId);
        if (asset.consumableId === "purifier-filter")
          await page.screenshot({
            path: path.join(output, "purifier-filter-drawer.png"),
            fullPage: true,
          });
        await page.getByRole("button", { name: "关闭", exact: true }).click();
      }
      await page.getByRole("textbox", { name: "搜索耗材" }).fill("滤");
      check(
        (await page.locator(".consumable-card").count()) === 3,
        "Search distinguishes purifier, robot and air-conditioner filters",
      );
      await page.getByRole("textbox", { name: "搜索耗材" }).fill("");
      await page.getByRole("combobox", { name: "耗材排序" }).selectOption("name");
      check(
        (await page.locator(".consumable-card").count()) === manifest.length,
        "Sorting retains all consumables",
      );
    }
    await page.close();
  }
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  watch(page);
  for (const asset of manifest) {
    await page.goto(base + "/items/" + asset.itemId);
    await page.getByRole("button", { name: "耗材", exact: true }).click();
    await page.locator(".record-row .consumable-image").waitFor();
    await settle(page);
    check(
      (await page.locator(".record-row .consumable-image img").getAttribute("src")) ===
        asset.assetPath,
      asset.consumableId + ": item detail tab uses same original",
    );
    await audit(page, "/items/" + asset.itemId + " consumables tab");
    if (asset.consumableId === "robot-filter")
      await page.screenshot({
        path: path.join(output, "robot-consumables-tab.png"),
        fullPage: true,
      });
  }
  for (const route of ["/", "/reminders", "/assistant?item=purifier", "/statistics", "/items"]) {
    await page.goto(base + route);
    await page.locator(".page, .home-page").first().waitFor();
    await settle(page);
    await audit(page, route);
    // Current AI/reminder/statistics surfaces show device images or text, not consumable photos.
    if (route === "/items") {
      const productSources = await page
        .locator(".item-picture img")
        .evaluateAll((nodes) => nodes.map((img) => new URL(img.currentSrc).pathname));
      check(
        productSources.length === 10 &&
          productSources.every((src) => src.startsWith("/assets/items/") || src === "/assets/no-photo.svg"),
        "Ten device slots retain reviewed photos or explicit pending placeholders",
      );
    }
  }
  await page.close();
  const slow = await browser.newPage();
  let release;
  const delayed = new Promise((resolve) => (release = resolve));
  await slow.route("**/assets/consumables/*.png", async (route) => {
    await delayed;
    await route.continue();
  });
  await slow.goto(base + "/consumables", { waitUntil: "domcontentloaded" });
  await slow.locator(".consumable-card").nth(5).waitFor();
  await slow.waitForTimeout(450);
  const frame = slow.locator(".consumable-image").first();
  check(
    (await frame.getAttribute("data-image-state")) === "loading" &&
      (await frame.locator(".product-image-skeleton").count()) === 1,
    "Delayed image shows skeleton",
  );
  const boxBefore = await slow.locator(".consumable-card").first().boundingBox();
  release();
  await settle(slow);
  const boxAfter = await slow.locator(".consumable-card").first().boundingBox();
  check(
    Math.abs(boxBefore.height - boxAfter.height) < 0.1,
    "Image loading does not change card height",
  );
  check(
    await frame
      .locator("img")
      .evaluate((img) => getComputedStyle(img).transitionDuration.includes("0.25s")),
    "250ms loaded-image fade",
  );
  await slow.close();
  const broken = await browser.newPage();
  const warnings = [];
  broken.on("console", (message) => {
    if (message.type() === "warning") warnings.push(message.text());
  });
  await broken.route("**/assets/consumables/air-purifier-filter-v3.png", (route) =>
    route.fulfill({ status: 404, body: "missing" }),
  );
  await broken.goto(base + "/consumables");
  const fallback = broken.locator(".consumable-card").filter({ hasText: "空气净化器滤芯" });
  await fallback.locator(".product-image-fallback").waitFor();
  check(
    (await fallback.locator(".consumable-image img").count()) === 0,
    "Failed image replaced by Cube, no browser broken icon",
  );
  check(
    warnings.some(
      (message) =>
        message.includes("空气净化器滤芯") && message.includes("air-purifier-filter-v3.png"),
    ),
    "Warning identifies failing consumable and URL",
  );
  await broken.close();
  const reduced = await browser.newPage({ reducedMotion: "reduce" });
  await reduced.goto(base + "/consumables");
  await settle(reduced);
  await reduced.locator(".consumable-card").first().hover();
  check(
    await reduced
      .locator(".consumable-image img")
      .first()
      .evaluate((img) => getComputedStyle(img).transform === "none"),
    "Reduced motion disables consumable zoom",
  );
  await reduced.close();
  const custom = await browser.newPage();
  await custom.route("**/api/snapshot", async (route) => {
    const response = await route.fetch();
    const data = await response.json();
    data.consumables.find((c) => c.id === "purifier-filter").coverImage =
      "/uploads/custom-consumable.png";
    await route.fulfill({ response, json: data });
  });
  await custom.route("**/uploads/custom-consumable.png", (route) =>
    route.fulfill({
      path: path.join(root, "frontend/public/assets/consumables/air-purifier-filter-v3.png"),
      contentType: "image/png",
    }),
  );
  await custom.goto(base + "/consumables");
  await settle(custom);
  check(
    (await custom
      .locator(".consumable-card")
      .filter({ hasText: "空气净化器滤芯" })
      .locator("img")
      .getAttribute("src")) === "/uploads/custom-consumable.png",
    "Custom user-uploaded photo is not overwritten by Mapping",
  );
  await custom.close();
  check(
    errors.length === 0,
    "Normal routes have zero image errors, asset 404s or runtime exceptions",
  );
  report.passed = true;
  report.errors = errors;
} catch (error) {
  report.passed = false;
  report.failure = String(error);
  throw error;
} finally {
  await browser.close();
  await writeFile(path.join(output, "verification.json"), JSON.stringify(report, null, 2));
  console.log(
    JSON.stringify(
      {
        passed: report.passed,
        assets: report.assets.length,
        layouts: report.layouts.length,
        routes: report.routes.length,
        checks: report.checks.length,
        failure: report.failure,
      },
      null,
      2,
    ),
  );
}

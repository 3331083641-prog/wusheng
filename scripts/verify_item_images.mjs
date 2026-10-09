/** Read-only browser acceptance checks. Requires running local backend and frontend. */
import { chromium } from "../frontend/node_modules/@playwright/test/index.mjs";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import path from "node:path";
import assert from "node:assert/strict";

const root = fileURLToPath(new URL("../", import.meta.url));
const output = path.join(root, "docs/competition/hd-images");
await mkdir(output, { recursive: true });
const manifest = JSON.parse(
  await readFile(path.join(root, "docs/references/hd-image-assets.json"), "utf8"),
);
const base = process.env.WUSHENG_TEST_BASE_URL || "http://127.0.0.1:5173";
const backend = process.env.WUSHENG_TEST_API_URL || "http://127.0.0.1:8000";
const report = {
  checkedAt: new Date().toISOString(),
  assets: [],
  layout: [],
  routes: [],
  checks: [],
};
const check = (value, name) => {
  assert(value, name);
  report.checks.push(name);
};

// Validation order required by project instructions. /generate only reads context.
check((await fetch(backend + "/health")).ok, "Backend /health");
check(
  (
    await fetch(backend + "/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ itemId: "headphones", question: "这台设备还在保修吗？" }),
    })
  ).ok,
  "Backend /generate",
);
check((await fetch(base)).ok, "Frontend dev server");
for (const asset of manifest) {
  const bytes = await readFile(path.join(root, "frontend/public", asset.assetPath));
  check(
    createHash("sha256").update(bytes).digest("hex").toUpperCase() === asset.sha256,
    asset.itemId + ": original PNG hash",
  );
  if (!asset.pending) assert.equal(bytes.readUInt32BE(16), 1448);
  if (!asset.pending) assert.equal(bytes.readUInt32BE(20), 1086);
  const response = await fetch(base + asset.assetPath);
  check(
    response.ok && response.headers.get("content-type")?.includes(asset.pending ? "image/svg+xml" : "image/png"),
    asset.itemId + ": served PNG",
  );
  check(
    createHash("sha256")
      .update(Buffer.from(await response.arrayBuffer()))
      .digest("hex")
      .toUpperCase() === asset.sha256,
    asset.itemId + ": served original bytes",
  );
  report.assets.push({
    itemId: asset.itemId,
    itemName: asset.itemName,
    src: asset.assetPath,
    width: asset.width,
    height: asset.height,
  });
}
const browser = await chromium.launch({
  channel: "msedge",
  ...(process.env.WUSHENG_EDGE_PATH ? { executablePath: process.env.WUSHENG_EDGE_PATH } : {}),
  headless: true,
});
const errors = [];
const watch = (page) => {
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("response", (response) => {
    if (response.url().includes("/assets/") && response.status() >= 400)
      errors.push(response.status() + " " + response.url());
  });
  page.on("console", (message) => {
    if (message.text().includes("[Wusheng ProductImage]")) errors.push(message.text());
  });
};
const settle = async (page) => {
  for (const frame of await page.locator(".product-image").all()) {
    if (!(await frame.isVisible())) continue;
    // The home demo gently floats continuously; native scroll doesn't require animation stability.
    await frame.evaluate((el) => el.scrollIntoView({ block: "nearest", behavior: "instant" }));
    await frame
      .locator("img")
      .evaluate(
        (img) =>
          img.complete ||
          new Promise((resolve) => img.addEventListener("load", resolve, { once: true })),
      );
    await page.waitForFunction(
      (el) => el.dataset.imageState === "loaded",
      await frame.elementHandle(),
    );
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(450);
};
const legacy =
  /\/assets\/(?:laptop|headphones(?:-detail)?|washer|ac|robot|coffee|toothbrush|suitcase|purifier|printer)\.jpg$/;
const audit = async (page, route) => {
  await settle(page);
  const images = await page
    .locator(".product-image > img")
    .evaluateAll((nodes) =>
      nodes.map((img) => ({
        src: new URL(img.currentSrc).pathname,
        width: img.naturalWidth,
        height: img.naturalHeight,
        fit: getComputedStyle(img).objectFit,
      })),
    );
  check(
    images.every((img) => img.width > 0 && !legacy.test(img.src)),
    route + ": no broken/legacy device images",
  );
  report.routes.push({ route, images });
};
try {
  const savedBaseline = await readFile(
    path.join(root, "backups/hd-images-20261001-185250/layout-before.json"),
    "utf8",
  ).catch(() => null);
  const baseline = savedBaseline
    ? JSON.parse(savedBaseline)
    : [
        { width: 1920, height: 1080 },
        { width: 2560, height: 1440 },
        { width: 1536, height: 864 },
        { width: 390, height: 844 },
      ].map((viewport) => ({ viewport }));
  // 125% equivalent effective viewport and DPR, not an automated browser-menu zoom claim.
  for (const [index, before] of baseline.entries()) {
    const page = await browser.newPage({
      viewport: before.viewport,
      deviceScaleFactor: index === 2 ? 1.25 : 1,
    });
    watch(page);
    await page.goto(base + "/items");
    await page.locator(".item-card").nth(9).waitFor();
    await settle(page);
    const boxes = await page.locator(".item-card").evaluateAll((nodes) =>
      nodes.map((n) => {
        const r = n.getBoundingClientRect(),
          p = n.querySelector(".item-picture").getBoundingClientRect();
        return {
          href: n.querySelector("a").getAttribute("href"),
          x: r.x,
          y: r.y,
          w: r.width,
          h: r.height,
          pw: p.width,
          ph: p.height,
        };
      }),
    );
    if (before.boxes)
      for (let i = 0; i < boxes.length; i++)
        for (const key of ["x", "y", "w", "h", "pw", "ph"])
          check(
            Math.abs(boxes[i][key] - before.boxes[i][key]) < 0.5,
            `${before.viewport.width}: card ${i} unchanged ${key}`,
          );
    for (const asset of manifest) {
      const img = page.locator(`.item-card a[href="/items/${asset.itemId}"] .item-picture img`);
      assert.equal(new URL(await img.getAttribute("src"), base).pathname, asset.assetPath);
      assert.equal(await img.evaluate((img) => img.naturalWidth), asset.width);
      assert.equal(await img.evaluate((img) => getComputedStyle(img).objectFit), "cover");
    }
    for (let i = 0; i < 10; i++)
      assert.equal(
        await page.locator(".item-picture img").nth(i).getAttribute("loading"),
        i < 3 ? "eager" : "lazy",
      );
    report.layout.push({
      viewport: before.viewport,
      deviceScaleFactor: index === 2 ? 1.25 : 1,
      identical: before.boxes ? true : "No local before-change baseline",
    });
    await page.screenshot({
      path: path.join(output, `items-${before.viewport.width}.png`),
      fullPage: true,
    });
    if (index === 0) {
      await page.locator(".item-card").first().hover();
      await page.waitForTimeout(400);
      const scale = await page
        .locator(".item-picture img")
        .first()
        .evaluate((img) => new DOMMatrix(getComputedStyle(img).transform).a);
      check(Math.abs(scale - 1.03) < 0.001, "Hover scale 1.03");
      await page.getByRole("button", { name: "列表视图", exact: true }).click();
      await settle(page);
      check(
        (await page.locator(".item-card.list").count()) === 10,
        "Grid/list toggle preserves all ten cards",
      );
      await audit(page, "/items (list)");
    }
    await page.close();
  }
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  watch(page);
  for (const config of [
    { viewport: { width: 2560, height: 1440 }, deviceScaleFactor: 2 },
    { viewport: { width: 2048, height: 1152 }, deviceScaleFactor: 1.25 },
  ]) {
    const hiDpi = await browser.newPage(config);
    watch(hiDpi);
    await hiDpi.goto(base + "/items");
    await hiDpi.locator(".item-card").nth(9).waitFor();
    await settle(hiDpi);
    const sharpCards = await hiDpi
      .locator(".item-picture img")
      .evaluateAll((nodes) =>
        nodes.every((img) => img.currentSrc.endsWith(".svg") || img.naturalWidth >= img.clientWidth * devicePixelRatio),
      );
    check(
      sharpCards,
      `${config.viewport.width}/DPR ${config.deviceScaleFactor}: native image resolution covers physical card pixels`,
    );
    await hiDpi.goto(base + "/items/headphones");
    await hiDpi.locator(".main-image img").waitFor();
    await settle(hiDpi);
    check(
      await hiDpi
        .locator(".main-image img")
        .evaluate((img) => img.currentSrc.endsWith(".svg") || img.naturalWidth >= img.clientWidth * devicePixelRatio),
      `${config.viewport.width}/DPR ${config.deviceScaleFactor}: full-resolution detail image`,
    );
    report.layout.push({ ...config, identical: "Extra resolution check (no baseline)" });
    await hiDpi.close();
  }
  for (const asset of manifest) {
    await page.goto(base + "/items/" + asset.itemId);
    await page.locator(".main-image .product-image").waitFor();
    await settle(page);
    const main = page.locator(".main-image img");
    assert.equal(new URL(await main.getAttribute("src"), base).pathname, asset.assetPath);
    assert.equal(await main.evaluate((img) => img.naturalWidth), asset.width);
    assert.equal(await main.evaluate((img) => getComputedStyle(img).objectFit), "contain");
    await audit(page, "/items/" + asset.itemId);
    if (asset.itemId === "headphones")
      await page.screenshot({ path: path.join(output, "headphones-detail.png"), fullPage: true });
  }
  for (const route of [
    "/",
    "/reminders",
    "/repairs",
    "/assistant?item=headphones",
    "/consumables",
    "/statistics",
    "/items/new",
    "/items?uiDemo=1",
  ]) {
    await page.goto(base + route);
    await page.locator("main.page, .home-page").first().waitFor();
    await page.waitForTimeout(400);
    await audit(page, route);
    if (route === "/repairs") {
      await page.locator(".repair-table tbody tr").first().click();
      await page.locator(".repair-drawer-hero").waitFor();
      await audit(page, "/repairs drawer");
    }
    if (route === "/assistant?item=headphones")
      await page.screenshot({ path: path.join(output, "assistant.png"), fullPage: true });
  }
  await page.goto(base + "/items");
  await page.getByRole("textbox", { name: "全局搜索" }).fill("Sony");
  await page.locator(".search-results .product-image").waitFor();
  await audit(page, "Global search Sony");
  await page.close();
  // Reserve image space during a real network delay and decode; no writes to the database.
  const slow = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  let release;
  const pending = new Promise((resolve) => (release = resolve));
  await slow.route("**/assets/items/*.png", async (route) => {
    await pending;
    await route.continue();
  });
  await slow.goto(base + "/items", { waitUntil: "domcontentloaded" });
  await slow.locator(".item-card").nth(9).waitFor();
  await slow.waitForTimeout(350);
  const loading = slow.locator(".item-picture .product-image").first();
  check(
    (await loading.getAttribute("data-image-state")) === "loading",
    "Delayed image shows skeleton",
  );
  check((await loading.locator(".product-image-skeleton").count()) === 1, "Skeleton present");
  const rectBefore = await slow.locator(".item-card").first().boundingBox();
  release();
  await settle(slow);
  const rectAfter = await slow.locator(".item-card").first().boundingBox();
  check(
    Math.abs(rectBefore.height - rectAfter.height) < 0.1,
    "Loading causes no card height change",
  );
  check(
    await loading
      .locator("img")
      .evaluate((img) => getComputedStyle(img).transitionDuration.includes("0.25s")),
    "250ms image fade-in",
  );
  await slow.close();
  const broken = await browser.newPage();
  const warnings = [];
  broken.on("console", (msg) => {
    if (msg.type() === "warning") warnings.push(msg.text());
  });
  await broken.route("**/assets/items/sony-wh1000xm6.png", (route) =>
    route.fulfill({ status: 404, body: "missing" }),
  );
  await broken.goto(base + "/assistant?item=headphones");
  await broken.locator(".context-item .product-image-fallback").waitFor();
  check(
    (await broken.locator(".context-item img").count()) === 0,
    "Failed photo uses Cube icon, no broken img",
  );
  check(
    warnings.some((w) => w.includes("Sony WH-1000XM6") && w.includes("sony-wh1000xm6.png")),
    "Failure warning identifies item and path",
  );
  await broken.close();
  const reduced = await browser.newPage({ reducedMotion: "reduce" });
  await reduced.goto(base + "/items");
  await settle(reduced);
  await reduced.locator(".item-card").first().hover();
  check(
    await reduced
      .locator(".item-picture img")
      .first()
      .evaluate((img) => getComputedStyle(img).transform === "none"),
    "Reduced motion disables image zoom",
  );
  await reduced.close();
  // Known seeded item with a user-uploaded replacement keeps that photo.
  const custom = await browser.newPage();
  await custom.route("**/api/snapshot", async (route) => {
    const response = await route.fetch();
    const data = await response.json();
    data.items.find((item) => item.id === "headphones").coverImage = "/uploads/custom-photo.png";
    await route.fulfill({ response, json: data });
  });
  await custom.route("**/uploads/custom-photo.png", (route) =>
    route.fulfill({
      path: path.join(root, "frontend/public/assets/items/sony-wh1000xm6.png"),
      contentType: "image/png",
    }),
  );
  await custom.goto(base + "/assistant?item=headphones");
  await settle(custom);
  check(
    (await custom.locator(".context-item img").getAttribute("src")) === "/uploads/custom-photo.png",
    "User-uploaded custom photo preserved",
  );
  await custom.close();
  check(errors.length === 0, "Normal routes have zero asset 404s, image warnings or page errors");
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
        layouts: report.layout.length,
        routes: report.routes.length,
        checks: report.checks.length,
        failure: report.failure,
      },
      null,
      2,
    ),
  );
}

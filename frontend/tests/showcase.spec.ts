import { test, expect } from "@playwright/test";
const backend = process.env.WUSHENG_TEST_API_URL || "http://127.0.0.1:8000";

test.beforeEach(async ({ page }) => { await page.emulateMedia({ reducedMotion: "reduce" }); });

test("首页真实档案可通过下一件、上一件、缩略图遍历全部数据库物品", async ({ page, request }) => {
  const data = await (await request.get(backend + "/home/showcase")).json();
  const errors: string[] = [];
  page.on("pageerror", e => errors.push(e.message));
  await page.goto("/");
  const card = page.locator(".home-showcase");
  await card.hover();
  for (let index = 0; index < data.items.length; index++) {
    await expect(card.locator("h2")).toHaveText(data.items[index].item.name);
    await expect(card.locator(".showcase-count")).toHaveText(`${index + 1} / ${data.total}`);
    await expect(card.locator(".showcase-product .product-image")).toHaveAttribute("data-image-state", "loaded");
    await card.getByRole("button", { name: "下一件物品", exact: true }).click();
  }
  await expect(card.locator("h2")).toHaveText(data.items[0].item.name);
  await card.getByRole("button", { name: "上一件物品", exact: true }).click();
  await expect(card.locator("h2")).toHaveText(data.items[data.total - 1].item.name);
  await card.locator(".showcase-thumbnails button").nth(1).click();
  await expect(card.locator("h2")).toHaveText(data.items[0].item.name);
  await expect(card.locator(".showcase-thumbnails button")).toHaveCount(Math.min(3, data.total));
  await card.getByRole("link", { name: "一物一码", exact: true }).click();
  await expect(page.locator(".drawer h2")).toHaveText("一物一码");
  expect(errors).toEqual([]);
});

for (const count of [0, 1, 2]) {
  test(`首页 ${count} 件数据库档案：没有虚构槽位或 Demo 回退`, async ({ page, request }) => {
    const data = await (await request.get(backend + "/home/showcase")).json();
    await page.route("**/api/home/showcase", route => route.fulfill({ json: { ...data, items: data.items.slice(0, count), total: count } }));
    await page.goto("/");
    if (!count) {
      await expect(page.getByText("还没有物品档案", { exact: true })).toBeVisible();
      await expect(page.locator(".showcase-empty a")).toHaveAttribute("href", "/items/new");
      await expect(page.locator(".showcase-main")).toHaveCount(0);
    } else {
      await expect(page.locator(".showcase-count")).toHaveText(`1 / ${count}`);
      await expect(page.locator(".showcase-thumbnails button")).toHaveCount(count);
      if (count === 1) await expect(page.getByRole("button", { name: "下一件物品", exact: true })).toBeDisabled();
    }
  });
}

test("新增第 11 件、改名、换封面、删除通过统一失效事件同步首页", async ({ page, request }) => {
  const initial = await (await request.get(backend + "/home/showcase")).json();
  const health = await (await request.get(backend + "/health")).json();
  const input = { name: "轮播新增测试物品", brand: "测试品牌", model: "SHOWCASE-11", purchaseDate: health.today, warrantyMonths: 0 };
  const response = await request.post(backend + "/items", { data: input });
  expect(response.ok()).toBeTruthy();
  const item = await response.json();
  try {
    await page.goto("/");
    await expect(page.locator(".showcase-count")).toHaveText(`1 / ${initial.total + 1}`);
    for (let n = 0; n < initial.total; n++) await page.getByRole("button", { name: "下一件物品", exact: true }).click();
    await expect(page.locator(".showcase-identity h2")).toHaveText(input.name);
    await expect(page.locator(".showcase-metrics")).toContainText("未记录");
    await expect(page.locator(".showcase-metrics")).toContainText("暂无耗材");
    const edited = { ...input, name: "轮播修改已同步" };
    expect((await request.put(backend + "/items/" + item.id, { data: edited })).ok()).toBeTruthy();
    await page.evaluate(() => window.dispatchEvent(new CustomEvent("wusheng:items-changed")));
    await expect(page.locator(".showcase-identity h2")).toHaveText(edited.name);
    const image = await request.post(backend + `/items/${item.id}/images`, { multipart: { type: "product", files: { name: "cover.png", mimeType: "image/png", buffer: Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aMq0AAAAASUVORK5CYII=", "base64") } } });
    expect(image.ok()).toBeTruthy();
    const uploaded = (await image.json())[0];
    await page.evaluate(() => window.dispatchEvent(new Event("focus")));
    await expect(page.locator(".showcase-product img")).toHaveAttribute("src", uploaded.filePath);
    await expect(page.locator(".showcase-product .product-image")).toHaveAttribute("data-image-state", "loaded");
    expect((await request.delete(backend + "/items/" + item.id)).ok()).toBeTruthy();
    await page.evaluate(() => window.dispatchEvent(new CustomEvent("wusheng:items-changed")));
    await expect(page.locator(".showcase-count")).toHaveText(`${initial.total} / ${initial.total}`);
    await expect(page.locator(".showcase-identity h2")).not.toHaveText(edited.name);
  } finally { await request.delete(backend + "/items/" + item.id); }
});

test("首次 skeleton、接口错误与重试均不回退到写死档案", async ({ page, request }) => {
  const data = await (await request.get(backend + "/home/showcase")).json();
  let fail = true;
  await page.route("**/api/home/showcase", async route => {
    await new Promise(resolve => setTimeout(resolve, 400));
    await route.fulfill(fail ? { status: 503, json: { detail: "测试临时不可用" } } : { json: data });
  });
  await page.goto("/");
  await expect(page.getByLabel("加载物品档案")).toBeVisible();
  await expect(page.getByText("暂时无法加载物品档案", { exact: true })).toBeVisible();
  fail = false;
  await page.getByRole("button", { name: "重新加载", exact: true }).click();
  await expect(page.locator(".showcase-count")).toHaveText(`1 / ${data.total}`);
});

test("首次加载占位与完成后的档案区域高度一致", async ({ page, request }) => {
  const data = await (await request.get(backend + "/home/showcase")).json();
  let release: () => void = () => {};
  const ready = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/home/showcase", async route => { await ready; await route.fulfill({ json: data }); });
  await page.goto("/");
  const skeleton = page.getByLabel("加载物品档案");
  await expect(skeleton).toBeVisible();
  const before = await skeleton.boundingBox();
  release();
  await expect(page.locator(".showcase-count")).toBeVisible();
  const after = await page.locator(".home-showcase").boundingBox();
  expect(Math.abs(before!.height - after!.height)).toBeLessThan(2);
});

test("轮播 6 秒、交互暂停 10 秒、后台暂停与可见刷新", async ({ page }) => {
  await page.clock.install();
  await page.goto("/");
  const count = page.locator(".showcase-count");
  await expect(count).toHaveText("1 / 10");
  await page.clock.runFor(6001);
  await expect(count).toHaveText("2 / 10");
  await page.getByRole("button", { name: "下一件物品", exact: true }).click();
  await expect(count).toHaveText("3 / 10");
  await page.mouse.move(0, 0);
  await page.clock.runFor(9999);
  await expect(count).toHaveText("3 / 10");
  await page.clock.runFor(6500);
  await expect(count).toHaveText("4 / 10");
  await page.evaluate(() => { Object.defineProperty(document, "visibilityState", { configurable: true, value: "hidden" }); document.dispatchEvent(new Event("visibilitychange")); });
  await page.clock.runFor(12000);
  await expect(count).toHaveText("4 / 10");
  const refresh = page.waitForResponse("**/api/home/showcase");
  await page.evaluate(() => { Object.defineProperty(document, "visibilityState", { configurable: true, value: "visible" }); document.dispatchEvent(new Event("visibilitychange")); });
  await refresh;
  await page.clock.runFor(6001);
  await expect(count).toHaveText("5 / 10");
});

test("主卡在桌面完整显示、移动无缩略槽，尊重 reduced motion", async ({ page }) => {
  for (const [width, height] of [[1440, 900], [1920, 1080], [1366, 768], [390, 844]]) {
    await page.setViewportSize({ width, height });
    await page.goto("/");
    await expect(page.locator(".showcase-identity h2")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
    expect(await page.locator(".showcase-float").evaluate(e => getComputedStyle(e).animationName)).toBe("none");
    if (width > 800) {
      const box = await page.locator(".showcase-main").boundingBox();
      expect(box!.y + box!.height).toBeLessThan(height);
    } else await expect(page.locator(".showcase-thumbnails")).toBeHidden();
  }
});

for (const scenario of [
  { activeProvider: "evidence", configuredProvider: "evidence", fallbackReason: "", model: null, label: "本地档案智能", subtitle: "无需大模型 · 数据不离开本机" },
  { activeProvider: "ollama", configuredProvider: "ollama", fallbackReason: "", model: "qwen-test", label: "本地模型 · qwen-test", subtitle: "Ollama 已连接 · 数据不离开本机" },
  { activeProvider: "evidence", configuredProvider: "ollama", fallbackReason: "测试模型服务未启动", model: "qwen-test", label: "本地模型未连接", subtitle: "已自动切换至本地档案智能" },
]) {
  test(`真实 API 状态驱动 AI UI：${scenario.label}`, async ({ page }) => {
    await page.route("**/api/health", route => route.fulfill({ json: { status: "ok", database: "SQLite", mode: "fixture", ...scenario } }));
    await page.goto("/assistant");
    await expect(page.locator(".provider-status")).toContainText(scenario.label);
    await expect(page.locator(".provider-status")).toContainText(scenario.subtitle);
    if (scenario.fallbackReason) {
      await page.getByText("查看原因", { exact: true }).click();
      await expect(page.locator(".provider-status details")).toContainText(scenario.fallbackReason);
    }
  });
}

test("每次回答标签依据 modelInvoked，独立于全局 Provider", async ({ page }) => {
  await page.goto("/assistant");
  await page.getByRole("button", { name: "这台设备还在保修吗？" }).click();
  await page.getByRole("button", { name: "发送问题" }).click();
  await expect(page.locator(".answer-mode").last()).toHaveText("本次回答：本地档案规则");
  await page.route("**/api/generate", route => route.fulfill({ json: { answer: "本地模型测试回答", sources: [], mode: "test", modelInvoked: true } }));
  await page.getByRole("button", { name: "查看说明书" }).click();
  await page.getByRole("button", { name: "发送问题" }).click();
  await expect(page.locator(".answer-mode").last()).toHaveText("本次回答：本地模型生成");
});

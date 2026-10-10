import { test, expect, type APIRequestContext } from "@playwright/test";
import path from "node:path";
import { readFile } from "node:fs/promises";

const root = path.resolve("..");
const backend = process.env.WUSHENG_TEST_API_URL || "http://127.0.0.1:8000";
async function share(request: APIRequestContext, item = "printer", options = {}) {
  const result = await request.post(`${backend}/items/${item}/share?regenerate=true`, { data: { options } });
  expect(result.status()).toBe(200);
  return (await result.json()).token as string;
}
async function manual(request: APIRequestContext, item: string, name: string) {
  const response = await request.post(`${backend}/items/${item}/documents/manual`, { multipart: {
    file: { name, mimeType: "application/pdf", buffer: await readFile(path.join(root, "frontend/tests/fixtures/scanned-care-guide.pdf")) },
  } });
  expect(response.status()).toBe(201);
  return (await response.json()).id as string;
}

for (const width of [375, 390, 430]) {
  test(`手机档案 ${width}px：打印机图片、中文品牌、无横向溢出`, async ({ page, request }) => {
    const errors: string[] = [];
    page.on("pageerror", e => errors.push(e.message));
    const token = await share(request, "printer", { showPurchaseDate: true, showMaintenance: true, showRepairs: true, showManualNames: true });
    await page.setViewportSize({ width, height: 844 });
    await page.goto("/share/" + token);
    await expect(page.locator(".share-identity h1")).toHaveText("惠普打印机");
    await expect(page.locator(".share-photo")).toHaveAttribute("data-image-state", "loaded");
    await expect(page.locator(".share-photo img")).toHaveAttribute("src", "/assets/items/hp-printer.png");
    await expect(page.locator(".share-brand")).not.toContainText("Wusheng");
    await expect(page).toHaveTitle("物生 · 惠普打印机 · 只读档案");
    await expect(page.locator(".share-gallery-controls")).toHaveCount(0);
    for (const title of ["基本信息", "保修与提醒", "生命周期", "维护与维修", "耗材状态", "产品说明书"]) {
      await expect(page.getByRole("heading", { name: title, exact: true })).toBeVisible();
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const image = await page.locator(".share-photo img").evaluate((img: HTMLImageElement) => ({ width: img.naturalWidth, fit: getComputedStyle(img).objectFit }));
    expect(image.width).toBeGreaterThan(1000);
    expect(image.fit).toBe("contain");
    await page.screenshot({ path: path.join(root, `docs/competition/mobile-v22-${width}.png`), fullPage: true });
    expect(errors).toEqual([]);
    await request.delete(backend + "/items/printer/share");
  });
}

test("十件 Demo 高清图片显示；未授权字段不进入手机 DOM", async ({ page, request }) => {
  const items = await (await request.get(backend + "/items")).json();
  for (const item of items.filter((i: { isDemo: boolean }) => i.isDemo)) {
    const token = await share(request, item.id);
    await page.goto("/share/" + token);
    await expect(page.locator(".share-photo")).toHaveAttribute("data-image-state", "loaded");
    await expect.poll(()=>page.locator(".share-photo img").evaluate((img:HTMLImageElement)=>img.naturalWidth)).toBe(1448);
    await expect(page.locator(".share-identity h1")).toHaveText(item.name);
    await expect(page.locator(".share-page")).not.toContainText("Wusheng");
    const labels = await page.locator(".share-facts dt").allTextContents();
    for (const hidden of ["购买价格", "购买渠道", "存放位置", "序列号", "当前库存"]) expect(labels).not.toContain(hidden);
    expect(await page.locator(".share-stage-pending time").count()).toBe(0);
    await request.delete(`${backend}/items/${item.id}/share`);
  }
});

test("用户本体照片：封面优先、相册切换、删除兜底及真实无图", async ({ page, request }) => {
  const created = await request.post(backend + "/items", { data: { name: "手机测试自有物品", purchaseDate: "2026-01-01" } });
  const id = (await created.json()).id;
  try {
    const photos: { id: string; filePath: string }[] = [];
    for (const name of ["own-photo-1.png", "own-photo-2.png"]) {
      const response = await request.post(`${backend}/items/${id}/images`, { multipart: {
        files: { name, mimeType: "image/png", buffer: await readFile(path.join(root, "frontend/public/assets/items/hp-printer.png")) }, type: "product",
      } });
      expect(response.status()).toBe(201);
      photos.push(...await response.json());
    }
    // Existing classification workflow updates the chosen cover without a new management API.
    expect((await request.patch(`${backend}/images/${photos[0].id}`, { data: { type: "label" } })).status()).toBe(200);
    expect((await request.patch(`${backend}/images/${photos[0].id}`, { data: { type: "product" } })).status()).toBe(200);
    const token = await share(request, id);
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/share/" + token);
    await expect(page.locator(".share-photo")).toHaveAttribute("data-image-state", "loaded");
    await expect(page.locator(".share-photo img")).toHaveAttribute("src", `/api/share-data/${token}/images/${photos[1].id}`);
    await page.getByRole("button", { name: "下一张本体照片" }).click();
    await expect(page.locator(".share-photo img")).toHaveAttribute("src", `/api/share-data/${token}/images/${photos[0].id}`);
    await page.locator(".share-gallery").dispatchEvent("touchstart", { touches: [{ identifier: 1, clientX: 300 }] });
    await page.locator(".share-gallery").dispatchEvent("touchend", { changedTouches: [{ identifier: 1, clientX: 80 }] });
    await expect(page.locator(".share-photo img")).toHaveAttribute("src", `/api/share-data/${token}/images/${photos[1].id}`);
    await request.delete(`${backend}/images/${photos[1].id}`);
    expect((await request.put(`${backend}/items/${id}`, { data: { name: "修改后的手机档案", purchaseDate: "2026-01-01" } })).status()).toBe(200);
    await page.reload();
    await expect(page.locator(".share-identity h1")).toHaveText("修改后的手机档案");
    await expect(page.locator(".share-photo img")).toHaveAttribute("src", `/api/share-data/${token}/images/${photos[0].id}`);
    await expect(page.locator(".share-gallery-controls")).toHaveCount(0);
    await request.delete(`${backend}/images/${photos[0].id}`);
    await page.reload();
    await expect(page.getByText("尚未添加照片", { exact: true })).toBeVisible();
  } finally { await request.delete(`${backend}/items/${id}`); }
});

test("图片请求失败显示读取错误，不伪装成没有照片", async ({ page, request }) => {
  const token = await share(request);
  await page.route("**/assets/items/hp-printer.png", route => route.fulfill({ status: 404, body: "missing" }));
  await page.goto("/share/" + token);
  await expect(page.getByRole("alert")).toContainText("照片暂时无法读取");
  await expect(page.getByText("尚未添加照片", { exact: true })).toHaveCount(0);
  await page.unroute("**/assets/items/hp-printer.png");
  await page.getByRole("button", { name: "重新加载照片" }).click();
  await expect(page.locator(".share-photo")).toHaveAttribute("data-image-state", "loaded");
  await request.delete(backend + "/items/printer/share");
});

test("PDF 手机入口、原名下载、未来授权、删除和撤销实时失效", async ({ page, request }) => {
  const created = await request.post(backend + "/items", { data: { name: "手机说明书测试", purchaseDate: "2026-01-01" } });
  const id = (await created.json()).id;
  try {
    const first = await manual(request, id, "授权合成说明书.pdf");
    await manual(request, id, "未授权合成说明书.pdf");
    const token = await share(request, id, { showManualFiles: true, showManualDownloads: true, manualDocumentIds: [first] });
    await page.goto("/share/" + token);
    await expect(page.getByRole("link", { name: "在线查看" })).toHaveCount(1);
    await expect(page.getByText("未授权合成说明书.pdf", { exact: true })).toHaveCount(0);
    const url = await page.getByRole("link", { name: "在线查看" }).getAttribute("href");
    const response = await request.get(backend + url!.replace(/^\/api/, ""));
    expect(response.headers()["content-type"]).toBe("application/pdf");
    expect(response.headers()["cache-control"]).toBe("no-store");
    const download = page.waitForEvent("download");
    await page.getByRole("link", { name: "下载 PDF" }).click();
    const file = await download;
    expect(file.suggestedFilename()).toBe("授权合成说明书.pdf");
    expect((await readFile((await file.path())!)).subarray(0, 4).toString()).toBe("%PDF");
    await expect(page.getByText(/部分微信内置浏览器/)).toBeVisible();
    await manual(request, id, "后来上传仍私有.pdf");
    await page.reload();
    await expect(page.getByText("后来上传仍私有.pdf", { exact: true })).toHaveCount(0);
    const future = await share(request, id, { showManualFiles: true, shareFutureManuals: true, manualDocumentIds: [first] });
    const newest = await manual(request, id, "持续授权新增.pdf");
    await page.goto("/share/" + future);
    await expect(page.getByText("持续授权新增.pdf", { exact: true })).toBeVisible();
    await expect(page.getByText("后来上传仍私有.pdf", { exact: true })).toHaveCount(0);
    await request.delete(`${backend}/documents/${newest}`);
    await page.reload();
    await expect(page.getByText("持续授权新增.pdf", { exact: true })).toHaveCount(0);
    const currentUrl = await page.getByRole("link", { name: "在线查看" }).getAttribute("href");
    await request.delete(`${backend}/items/${id}/share`);
    await page.evaluate(() => window.dispatchEvent(new Event("focus")));
    await expect(page.getByRole("alert")).toContainText("已过期或已撤销");
    await expect(page.getByRole("link", { name: "在线查看" })).toHaveCount(0);
    expect((await request.get(backend + currentUrl!.replace(/^\/api/, ""))).status()).toBe(404);
  } finally { await request.delete(`${backend}/items/${id}`); }
});

test("所有者明确选择具体 PDF；新权限及持续授权默认关闭", async ({ page, request }) => {
  const created = await request.post(backend + "/items", { data: { name: "分享权限 UI 测试", purchaseDate: "2026-01-01" } });
  const id = (await created.json()).id;
  try {
    const doc = await manual(request, id, "仅选此文件.pdf");
    await manual(request, id, "不要公开.pdf");
    await page.goto("/items/" + id);
    await page.getByRole("button", { name: "生成二维码", exact: true }).click();
    await expect(page.getByLabel("允许查看所选说明书 PDF", { exact: true })).not.toBeChecked();
    await page.getByLabel("允许查看所选说明书 PDF", { exact: true }).check();
    await expect(page.getByLabel("持续授权：以后新增或替换上传的说明书也自动共享", { exact: true })).not.toBeChecked();
    await expect(page.getByLabel("允许下载已授权说明书 PDF", { exact: true })).not.toBeChecked();
    await page.getByLabel("仅选此文件.pdf", { exact: true }).check();
    await page.getByRole("button", { name: "生成只读二维码", exact: true }).click();
    await expect(page.getByRole("img", { name: "物品档案二维码" })).toBeVisible();
    const link = await (await request.post(`${backend}/items/${id}/share`)).json();
    expect(link.options.manualDocumentIds).toEqual([doc]);
    const data = await (await request.get(`${backend}/share-data/${link.token}`)).json();
    expect(data.manuals.map((d: { name: string }) => d.name)).toEqual(["仅选此文件.pdf"]);
  } finally { await request.delete(`${backend}/items/${id}`); }
});

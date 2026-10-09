import { test, expect } from "@playwright/test";
import path from "node:path";
import { readFile, mkdir, writeFile, truncate } from "node:fs/promises";
const root = path.resolve("..");
const backend = process.env.WUSHENG_TEST_API_URL || "http://127.0.0.1:8000";
const testDataRoot = process.env.WUSHENG_TEST_DATA_DIR || path.join(root, "data");
const jpg = path.join(root, "frontend/public/assets/headphones-detail.jpg");
const png = path.join(root, "docs/references/demo-receipt.png");
const manual = path.join(testDataRoot, "uploads/demo-care-guide.pdf");
const today = new Intl.DateTimeFormat("en-CA", {
  timeZone: "Asia/Shanghai",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
}).format(new Date());

test("原生文件选择请求、四类入口、多图预览、拖拽及删除草稿", async ({ page, request }) => {
  const errors: string[] = [];
  const external: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("request", (r) => {
    if (/^https?:/.test(r.url()) && new URL(r.url()).hostname !== "127.0.0.1")
      external.push(r.url());
  });
  await page.goto("/items/new");
  await expect(page.getByRole("button", { name: "开始识别", exact: true })).toBeDisabled();
  let chooser = page.waitForEvent("filechooser");
  await page.getByRole("button", { name: "选择图片", exact: true }).click();
  const first = await chooser;
  expect(first.isMultiple()).toBeTruthy();
  await first.setFiles(jpg);
  await expect(page.locator(".uploaded-images > div")).toHaveCount(1);
  await expect(page.locator(".uploaded-images")).toContainText("本地已保存");
  chooser = page.waitForEvent("filechooser");
  await page
    .getByRole("button", { name: "点击上传图片或拖拽到此处", exact: true })
    .click({ position: { x: 20, y: 20 } });
  await (await chooser).setFiles([jpg, png]);
  await expect(page.locator(".uploaded-images > div")).toHaveCount(3);
  await expect(page.getByRole("button", { name: "开始识别", exact: true })).toBeEnabled();
  for (const [name, kind] of [
    ["物品本体照片", "product"],
    ["小票 / 发票", "receipt"],
    ["包装盒 / 铭牌", "label"],
    ["说明书照片", "manual_image"],
  ]) {
    chooser = page.waitForEvent("filechooser");
    await page.getByRole("button", { name, exact: true }).click();
    await (await chooser).setFiles(png);
    await expect(page.locator(".uploaded-images > div").last()).toContainText("本地已保存");
    await expect(page.locator(".uploaded-images select").last()).toHaveValue(kind);
  }
  const bytes = await readFile(jpg);
  const transferred = await page.evaluateHandle(
    (bytes) => {
      const dt = new DataTransfer();
      dt.items.add(new File([new Uint8Array(bytes)], "拖拽.jpg", { type: "image/jpeg" }));
      return dt;
    },
    [...bytes],
  );
  await page.locator(".dropzone").dispatchEvent("dragenter", { dataTransfer: transferred });
  await expect(page.locator(".dropzone")).toHaveClass(/dragging/);
  await page.locator(".dropzone").dispatchEvent("dragover", { dataTransfer: transferred });
  await page.locator(".dropzone").dispatchEvent("drop", { dataTransfer: transferred });
  await expect(page.locator(".uploaded-images > div")).toHaveCount(8);
  await expect(page.locator(".uploaded-images > div").last()).toContainText("本地已保存");
  await page.getByRole("button", { name: "移除图片 8", exact: true }).click();
  await expect(page.locator(".uploaded-images > div")).toHaveCount(7);
  // Browsing away disposes object URLs and deletes the unsaved draft.
  const deleted = page.waitForResponse(
    (r) =>
      r.url().includes("/api/drafts/") &&
      r.request().method() === "DELETE" &&
      !r.url().includes("/images/"),
  );
  await page.getByRole("navigation").getByRole("link", { name: "我的物品", exact: true }).click();
  const response = await deleted;
  expect(response.ok()).toBeTruthy();
  const draftId = response.url().split("/").pop();
  expect((await request.get(`${backend}/drafts/${draftId}/images`)).status()).toBe(404);
  expect(errors).toEqual([]);
  expect(external).toEqual([]);
});

test("无文字照片本地 OCR、人工确认保存、档案图片和提醒持久", async ({ page, request }) => {
  let id = "";
  try {
    await page.goto("/items/new");
    const chooser = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: "选择图片", exact: true }).click();
    await (
      await chooser
    ).setFiles(path.join(root, "frontend/public/assets/items/sony-wh1000xm6.png"));
    await expect(page.getByRole("button", { name: "开始识别", exact: true })).toBeEnabled();
    await page.getByRole("button", { name: "开始识别", exact: true }).click();
    await expect(page.getByText(/该图片未检测到可识别文字/)).toBeVisible({ timeout: 60000 });
    await page.getByLabel("商品名称", { exact: true }).fill("本地附件验收耳机");
    await page.getByLabel("品牌", { exact: true }).fill("Sony");
    await page.getByLabel("型号", { exact: true }).fill("人工确认型号");
    await page.getByLabel("购买日期", { exact: true }).fill(today);
    await page.getByRole("button", { name: "确认并保存", exact: true }).click();
    await page.waitForURL(/\/items\/(?!new$)[^/]+$/);
    id = page.url().split("/").pop()!;
    await expect(page.locator(".detail-title h1")).toHaveText("本地附件验收耳机");
    const detail = await (await request.get(`${backend}/items/${id}`)).json();
    expect(detail.images).toHaveLength(1);
    expect(detail.images[0].originalFilename).toContain("sony-wh1000xm6.png");
    expect(detail.images[0].filePath).toMatch(/^\/api\/images\//);
    await page.reload();
    await expect(page.locator(".detail-title h1")).toHaveText("本地附件验收耳机");
    await expect
      .poll(() =>
        page.locator(".main-image img").evaluate((img: HTMLImageElement) => img.naturalWidth),
      )
      .toBe(1448);
    await page.getByRole("navigation").getByRole("link", { name: "我的物品", exact: true }).click();
    await expect(page.locator(".item-card").filter({ hasText: "本地附件验收耳机" })).toHaveCount(1);
    const snapshot = await (await request.get(`${backend}/snapshot`)).json();
    expect(snapshot.reminders.filter((r: { itemId: string }) => r.itemId === id)).toHaveLength(2);
  } finally {
    if (id) await request.delete(`${backend}/items/${id}`);
  }
});

test("PDF 原生选择、上传、查看下载、刷新、AI 引用及确认删除", async ({ page, request }) => {
  let documentId = "";
  try {
    await page.goto("/items/laptop");
    await page.getByRole("button", { name: "说明书", exact: true }).click();
    const count = await page.locator(".document-card").count();
    const chooser = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: /^(继续)?上传 PDF$/ }).click();
    await (await chooser).setFiles(manual);
    await expect(page.locator(".document-card")).toHaveCount(count + 1);
    const documents = await (await request.get(`${backend}/items/laptop/documents`)).json();
    const doc = documents.find(
      (d: { originalFilename: string }) => d.originalFilename === "demo-care-guide.pdf",
    );
    documentId = doc.id;
    const card = page.locator(".document-card").filter({ hasText: "demo-care-guide.pdf" });
    await expect(card).toContainText("1 页");
    const popup = page.waitForEvent("popup");
    await card.getByRole("link", { name: "查看 demo-care-guide.pdf" }).click();
    const viewer = await popup;
    await viewer.waitForLoadState("domcontentloaded");
    expect(viewer.url()).toContain(`/api/documents/${documentId}/file`);
    await viewer.close();
    const appBase = process.env.WUSHENG_TEST_BASE_URL || "http://127.0.0.1:5173";
    const bytes = await (await request.get(new URL(doc.filePath, appBase).toString())).body();
    expect(bytes.subarray(0, 5).toString()).toBe("%PDF-");
    const download = page.waitForEvent("download");
    await card.getByRole("link", { name: "下载 demo-care-guide.pdf" }).click();
    expect((await download).suggestedFilename()).toBe("demo-care-guide.pdf");
    await page.reload();
    await page.getByRole("button", { name: "说明书", exact: true }).click();
    await expect(card).toBeVisible();
    const answer = await (
      await request.post(`${backend}/generate`, {
        data: { itemId: "laptop", question: "说明书里怎样清洁？" },
      })
    ).json();
    expect(answer.answer).toContain("依据已上传说明书");
    await card.getByRole("button", { name: "删除 demo-care-guide.pdf" }).click();
    await expect(page.getByRole("dialog")).toContainText("一并删除");
    await page.getByRole("button", { name: "关闭", exact: true }).click();
    await expect(card).toBeVisible();
    await card.getByRole("button", { name: "删除 demo-care-guide.pdf" }).click();
    await page.getByRole("button", { name: "确认删除", exact: true }).click();
    await expect(card).toHaveCount(0);
    expect((await request.get(`${backend}${doc.filePath}`)).status()).toBe(404);
    documentId = "";
  } finally {
    if (documentId) await request.delete(`${backend}/documents/${documentId}`);
  }
});

test("六种耗材字段明确、关联链接和 Item 耗材 Tab 同源", async ({ page }) => {
  const pairs = [
    ["空气净化器滤芯", "小米空气净化器4", "purifier"],
    ["蓝月亮洗衣液", "海尔滚筒洗衣机", "washer"],
    ["打印机墨盒", "惠普打印机", "printer"],
    ["E.S.E. 咖啡易理包", "德龙半自动意式咖啡机", "coffee"],
    ["电动牙刷刷头", "飞利浦 HX3671/13 电动牙刷", "toothbrush"],
    ["扫地机器人滤网", "小米扫地机器人 S10", "robot"],
  ];
  for (const [name, item, id] of pairs) {
    await page.goto("/consumables");
    await page.locator(".consumable-card").filter({ hasText: name }).click();
    const dialog = page.getByRole("dialog");
    await expect(dialog.locator(".consumable-drawer-hero")).toContainText("耗材名称" + name);
    await expect(dialog.locator(".consumable-drawer-hero")).toContainText("关联物品" + item);
    await dialog.getByRole("link", { name: item, exact: true }).click();
    await page.waitForURL(`**/items/${id}`);
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await page.getByRole("button", { name: "耗材", exact: true }).click();
    await expect(page.locator(".record-row")).toContainText(name);
  }
});

test("错误状态可见：图片类型与数量、PDF 类型与大小", async ({ page }, testInfo) => {
  await page.goto("/items/new");
  await page
    .getByLabel("上传物品图片")
    .setInputFiles({ name: "bad.txt", mimeType: "text/plain", buffer: Buffer.from("bad") });
  await expect(page.getByRole("alert")).toContainText("仅支持");
  await expect(page.locator(".uploaded-images > div")).toHaveCount(0);
  await page
    .getByLabel("上传物品图片")
    .setInputFiles(
      Array.from({ length: 11 }, (_, n) => ({
        name: `${n}.png`,
        mimeType: "image/png",
        buffer: Buffer.from("bad"),
      })),
    );
  await expect(page.getByRole("alert")).toContainText("最多上传 10");
  await page.goto("/items/laptop");
  await page.getByRole("button", { name: "说明书", exact: true }).click();
  await page
    .getByLabel("上传说明书 PDF")
    .setInputFiles({
      name: "bad.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("not a pdf"),
    });
  await expect(page.getByRole("alert")).toContainText("有效 PDF");
  const oversized = testInfo.outputPath("large.pdf");
  await mkdir(path.dirname(oversized), { recursive: true });
  await writeFile(oversized, "");
  await truncate(oversized, 50 * 1024 * 1024 + 1);
  await page.getByLabel("上传说明书 PDF").setInputFiles(oversized);
  await expect(page.getByRole("alert")).toContainText("PDF 不超过 50MB");
});

test("手动录入无需图片，也能创建真实档案", async ({ page, request }) => {
  let id = "";
  try {
    await page.goto("/items/new");
    await page.getByRole("button", { name: /手动录入/ }).click();
    await page.getByLabel("商品名称", { exact: true }).fill("本地手动验收档案");
    await page.getByLabel("购买日期", { exact: true }).fill(today);
    await page.getByRole("button", { name: "确认并保存", exact: true }).click();
    await page.waitForURL(/\/items\/(?!new$)[^/]+$/);
    id = page.url().split("/").pop()!;
    const detail = await (await request.get(`${backend}/items/${id}`)).json();
    expect(detail.item.name).toBe("本地手动验收档案");
    expect(detail.images).toEqual([]);
  } finally {
    if (id) await request.delete(`${backend}/items/${id}`);
  }
});

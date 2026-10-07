import { test, expect, type APIRequestContext } from "@playwright/test";
import path from "node:path";
const backend = process.env.WUSHENG_TEST_API_URL || "http://127.0.0.1:8000";
const today = new Intl.DateTimeFormat("en-CA", {
  timeZone: "Asia/Shanghai",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
}).format(new Date());
const itemPayload = (name: string) => ({
  name,
  brand: "Sony",
  model: "WH-1000XM6",
  category: "数码",
  purchaseDate: today,
  purchasePrice: 2999,
  warrantyMonths: 12,
  returnWindowDays: 7,
});
async function create(request: APIRequestContext, name: string) {
  const response = await request.post(backend + "/items", {
    data: itemPayload(name),
  });
  expect(response.ok()).toBeTruthy();
  return (await response.json()).id as string;
}
const root = path.resolve("..");

test("统一导航、桌面与移动路由、筛选和搜索不刷新", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(page.locator(".hero-copy h1")).toBeVisible();
  await page.evaluate(() => {
    (window as Window & { wushengProbe?: string }).wushengProbe = "alive";
  });
  await page.getByRole("navigation").getByRole("link", { name: "我的物品", exact: true }).click();
  await expect(page.getByRole("heading", { name: "我的物品", exact: true })).toBeVisible();
  expect(
    await page.evaluate(() => (window as Window & { wushengProbe?: string }).wushengProbe),
  ).toBe("alive");
  await page.getByRole("button", { name: "列表视图", exact: true }).click();
  await expect(page.locator(".list-view")).toBeVisible();
  await page.getByRole("button", { name: "网格视图", exact: true }).click();
  await page.getByRole("button", { name: "家居", exact: true }).click();
  await expect(page.locator(".items-grid .item-card")).toHaveCount(1);
  await page.getByLabel("全局搜索").fill("WH-1000XM6");
  const headphones = page.locator('.search-results a[href="/items/headphones"]');
  await expect(headphones).toBeVisible();
  await headphones.click();
  await expect(page.locator(".detail-title h1")).toContainText("Sony");
  await page.setViewportSize({ width: 1366, height: 768 });
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
  ).toBeTruthy();
  for (const route of [
    "/",
    "/items",
    "/items/new",
    "/items/headphones",
    "/reminders",
    "/consumables",
    "/repairs",
    "/assistant",
    "/statistics",
  ]) {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(route);
    await expect(page.locator(".sidebar")).toBeVisible();
    await page.locator("main h1,.hero h1").first().waitFor();
    await page.waitForTimeout(300);
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
      route + " mobile overflow",
    ).toBeTruthy();
  }
  expect(errors).toEqual([]);
});

test("Case A：真实本地 OCR，多图确认保存，自动提醒", async ({ page, request }) => {
  let id = "";
  try {
    await page.goto("/items/new");
    await page
      .getByLabel("上传物品图片")
      .setInputFiles([
        path.join(root, "frontend/public/assets/headphones-detail.jpg"),
        path.join(root, "docs/references/demo-receipt.png"),
      ]);
    await page.getByLabel("图片 2 类型").selectOption("receipt");
    await page.getByRole("button", { name: "开始识别", exact: true }).click();
    await expect(page.getByLabel("品牌", { exact: true })).toHaveValue("Sony", {
      timeout: 60000,
    });
    await expect(page.getByLabel("型号", { exact: true })).toHaveValue("WH-1000XM6");
    await page.getByLabel("商品名称").fill("UI Case A 耳机");
    await page.getByLabel("购买日期", { exact: true }).fill(today);
    await page.getByRole("button", { name: "确认并保存" }).click();
    await page.waitForURL(/\/items\/(?!new$)[^/]+$/);
    id = page.url().split("/").pop()!;
    await expect(page.locator(".detail-title h1")).toHaveText("UI Case A 耳机");
    const snapshot = await (await request.get(backend + "/snapshot")).json();
    expect(snapshot.reminders.filter((r: { itemId: string }) => r.itemId === id)).toHaveLength(2);
  } finally {
    if (id) await request.delete(backend + "/items/" + id);
  }
});

test("档案编辑、PDF/JSON 导出、说明书与维护真实保存", async ({ page, request }) => {
  const id = await create(request, "UI 档案测试");
  try {
    await page.goto("/items/" + id);
    await page.getByRole("button", { name: "编辑信息" }).click();
    await page.getByLabel("商品名称").fill("UI 已编辑档案");
    await page.getByRole("button", { name: "保存修改" }).click();
    await expect(page.locator(".detail-title h1")).toHaveText("UI 已编辑档案");
    await page.getByRole("button", { name: "生成二维码" }).click();
    await expect(page.getByText("当前未检测到可用分享网络，请连接 Wi-Fi 后重新检测。")).toBeVisible();
    await expect(page.getByRole("img", { name: "物品档案二维码" })).toHaveCount(0);
    await page.getByRole("button", { name: "关闭", exact: true }).click();
    const archive = page.waitForEvent("download");
    await page.getByRole("button", { name: "导出档案" }).click();
    expect((await archive).suggestedFilename()).toMatch(/-物品档案\.pdf$/);
    const raw = page.waitForEvent("download");
    await page.getByRole("button", { name: "导出原始数据 JSON", exact: true }).click();
    expect((await raw).suggestedFilename()).toMatch(/\.json$/);
    await page.getByRole("button", { name: "说明书", exact: true }).click();
    await page
      .getByLabel("上传说明书 PDF")
      .setInputFiles(path.join(root, "frontend/tests/fixtures/demo-care-guide.pdf"));
    await expect(page.locator(".document-card")).toHaveCount(1);
    await page.getByRole("button", { name: "维护记录", exact: true }).click();
    await page.getByRole("button", { name: "记录维护", exact: true }).click();
    await page.getByLabel("维护内容").fill("UI 清洁");
    await page.getByRole("button", { name: "保存维护记录" }).click();
    await expect(page.locator(".record-row")).toContainText("UI 清洁");
    const detail = await (await request.get(backend + "/items/" + id)).json();
    expect(detail.maintenance).toHaveLength(1);
    expect(detail.documents).toHaveLength(1);
    expect(detail.events.some((e: { type: string }) => e.type === "maintenance")).toBeTruthy();
  } finally {
    await request.delete(backend + "/items/" + id);
  }
});

test("提醒延后与完成状态持久", async ({ page, request }) => {
  const id = await create(request, "UI 提醒测试");
  try {
    await page.goto("/reminders");
    const row = page.locator(".reminder-row").filter({ hasText: "UI 提醒测试" }).first();
    await row.getByRole("button", { name: "延后 7 天" }).click();
    await expect(page.getByRole("status")).toContainText("已延后");
    await row.getByRole("button", { name: "已处理" }).click();
    await expect(page.getByRole("status")).toContainText("已处理");
    const data = await (await request.get(backend + "/snapshot")).json();
    expect(
      data.reminders.some(
        (r: { itemId: string; status: string }) => r.itemId === id && r.status === "completed",
      ),
    ).toBeTruthy();
  } finally {
    await request.delete(backend + "/items/" + id);
  }
});

test("Case B：滤芯实时历史预测、抽屉趋势，库存补给同步", async ({ page, request }) => {
  const id = await create(request, "UI 耗材设备");
  try {
    await page.goto("/consumables");
    const card = page.locator(".consumable-card").filter({ hasText: "空气净化器滤芯" });
    const current = (await (await request.get(backend + "/snapshot")).json()).consumables.find(
      (c: { id: string }) => c.id === "purifier-filter",
    );
    await expect(card).toContainText(`${current.estimatedDaysLeft} 天`);
    await card.click();
    await expect(page.getByRole("dialog")).toContainText(current.method);
    await expect(page.locator(".drawer-chart svg")).toBeVisible();
    await page.getByRole("button", { name: "关闭", exact: true }).click();
    await page.getByRole("button", { name: "关联耗材", exact: true }).click();
    await page.getByLabel("关联设备", { exact: true }).selectOption(id);
    await page.getByLabel("耗材名称").fill("UI 测试耗材");
    await page.getByLabel("当前库存", { exact: true }).fill("3");
    await page.getByRole("button", { name: "保存记录", exact: true }).click();
    await page.locator(".consumable-card").filter({ hasText: "UI 测试耗材" }).click();
    await page.getByLabel("消耗数量", { exact: true }).fill("1");
    await page.getByRole("button", { name: "保存记录", exact: true }).click();
    await expect(page.getByRole("dialog")).toContainText("2 个");
    await page.getByRole("button", { name: "补充库存", exact: true }).click();
    await page.getByLabel("补货数量").fill("2");
    await page.getByLabel("补货费用（元）").fill("60");
    await page.getByRole("button", { name: "保存记录", exact: true }).click();
    await expect(page.getByRole("dialog")).toContainText("4 个");
  } finally {
    await request.delete(backend + "/items/" + id);
  }
});

test("Case C：洗衣机报修至完成，生命周期与支出同步", async ({ page, request }) => {
  const id = await create(request, "UI Case C 洗衣机");
  try {
    const before = (await (await request.get(backend + "/snapshot")).json()).stats.repairSpend;
    await page.goto("/repairs?item=" + id);
    await page.getByRole("button", { name: "新增维修记录" }).click();
    await page.getByLabel("问题描述", { exact: true }).fill("脱水时异响");
    await page.getByRole("button", { name: "创建报修记录" }).click();
    for (const state of ["诊断中", "维修中", "已完成"]) {
      await page.getByRole("row").filter({ hasText: "UI Case C 洗衣机" }).click();
      await page.getByLabel("更新进度").selectOption(state);
      await page.getByLabel("费用（元）", { exact: true }).fill("450");
      await page.getByLabel("维修说明").fill("合成演示：更换轴承组件");
      await page.getByRole("button", { name: "保存维修进度" }).click();
      await expect(page.getByRole("row").filter({ hasText: "UI Case C 洗衣机" })).toContainText(
        state,
      );
    }
    const snapshot = await (await request.get(backend + "/snapshot")).json();
    expect(snapshot.stats.repairSpend).toBe(before + 450);
    const detail = await (await request.get(backend + "/items/" + id)).json();
    expect(detail.events.filter((e: { type: string }) => e.type === "repair")).toHaveLength(2);
    expect(detail.item.status).toBe("正常使用");
  } finally {
    await request.delete(backend + "/items/" + id);
  }
});

test("当前物品助手查询保修、引用说明书、缺少记录明确未知", async ({ page }) => {
  await page.goto("/assistant?item=headphones");
  await page.getByRole("button", { name: "这台设备还在保修吗？" }).click();
  await page.getByRole("button", { name: "发送问题" }).click();
  await expect(page.locator(".chat-message.assistant").last()).toContainText("仍在保修期内");
  await page.getByRole("button", { name: "多久需要清洁一次？" }).click();
  await page.getByRole("button", { name: "发送问题" }).click();
  await expect(page.locator(".chat-message.assistant").last()).toContainText("说明书");
  await page.getByLabel("选择当前物品").selectOption("suitcase");
  await page.getByRole("button", { name: "之前维修过什么？" }).click();
  await page.getByRole("button", { name: "发送问题" }).click();
  await expect(page.locator(".chat-message.assistant").last()).toContainText("没有找到");
});

test("截图证据：1440、1920、1366与移动首页", async ({ page }) => {
  for (const [width, height] of [
    [1440, 900],
    [1920, 1080],
    [1366, 768],
    [390, 844],
  ]) {
    await page.setViewportSize({ width, height });
    await page.goto("/");
    await page.locator(".hero h1").waitFor();
    await page.waitForTimeout(850);
    await page.screenshot({
      path: path.join(root, `docs/references/home-${width}.png`),
      fullPage: true,
    });
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  for (const [route, name] of [
    ["/items", "items"],
    ["/items/new", "add"],
    ["/items/headphones", "detail"],
    ["/reminders", "reminders"],
    ["/consumables", "consumables"],
    ["/repairs", "repairs"],
    ["/assistant", "assistant"],
    ["/statistics", "statistics"],
  ]) {
    await page.goto(route);
    await page.locator("main h1").waitFor();
    await page.waitForTimeout(850);
    await page.screenshot({
      path: path.join(root, `docs/references/${name}-1440.png`),
      fullPage: true,
    });
  }
});

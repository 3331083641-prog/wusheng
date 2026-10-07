import { test, expect } from "@playwright/test";
import path from "node:path";
import { readFile } from "node:fs/promises";
import { spawn } from "node:child_process";
import net from "node:net";
const root = path.resolve("..");
const backend = process.env.WUSHENG_TEST_API_URL || "http://127.0.0.1:8000";
const image = path.join(root, "docs/references/demo-receipt.png");
test("字段来源追溯、人工修改及后置相机选择器", async ({ page, request }) => {
  const draft = (await (await request.post(backend + "/drafts")).json()).id;
  await request.post(backend + `/drafts/${draft}/images`, {
    multipart: {
      files: {
        name: "synthetic-receipt.png",
        mimeType: "image/png",
        buffer: await readFile(image),
      },
      type: "receipt",
    },
  });
  const recognized = await (await request.post(backend + `/drafts/${draft}/recognize`)).json();
  const result = await request.post(backend + "/items", {
    data: {
      name: "V2 UI 来源",
      purchaseDate: "2026-01-01",
      draftSessionId: draft,
      recognitionSessionId: recognized.sessionId,
    },
  });
  const id = (await result.json()).id;
  try {
    await page.goto("/items/" + id);
    await page.getByRole("button", { name: "凭证资料", exact: true }).click();
    await expect(page.getByText("已人工修改", { exact: false }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: "来源图片" }).first()).toBeVisible();
    await page.goto("/items/new");
    const chooser = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: "拍照添加" }).click();
    await chooser;
    await expect(page.getByLabel("上传物品图片")).toHaveAttribute("capture", "environment");
  } finally {
    await request.delete(backend + "/items/" + id);
  }
});
test("凭证补充、分类、售后 ZIP、日历与完整备份真实下载", async ({ page, request }) => {
  const r = await request.post(backend + "/items", {
    data: { name: "V2 UI 资料", purchaseDate: "2026-01-01", warrantyMonths: 24 },
  });
  const id = (await r.json()).id;
  try {
    await page.goto("/items/" + id);
    await page.getByRole("button", { name: "凭证资料", exact: true }).click();
    await page.getByLabel("添加资料类型").selectOption("invoice");
    const chooser = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: "添加资料", exact: true }).click();
    await (await chooser).setFiles(image);
    await expect(page.locator(".evidence-card")).toHaveCount(1);
    await expect(page.locator(".evidence-card select")).toHaveValue("invoice");
    await page.locator(".evidence-card select").selectOption("warranty_card");
    await expect
      .poll(async () => (await (await request.get(backend + "/items/" + id)).json()).images[0].type)
      .toBe("warranty_card");
    let download = page.waitForEvent("download");
    await page.getByRole("link", { name: "售后证据包", exact: true }).click();
    let file = await download;
    expect((await readFile((await file.path())!)).subarray(0, 2).toString()).toBe("PK");
    await page.goto("/reminders");
    download = page.waitForEvent("download");
    await page.getByRole("link", { name: "导出全部提醒到日历" }).click();
    file = await download;
    expect(await readFile((await file.path())!, "utf8")).toContain("BEGIN:VEVENT");
    await page.goto("/statistics");
    download = page.waitForEvent("download");
    await page.getByRole("link", { name: "下载完整备份" }).click();
    file = await download;
    expect((await readFile((await file.path())!)).subarray(0, 2).toString()).toBe("PK");
    page.once("dialog", (dialog) => dialog.accept());
    await page.getByLabel("选择备份 ZIP").setInputFiles((await file.path())!);
    await expect(page.getByRole("heading", { name: "数据统计", exact: true })).toBeVisible();
  } finally {
    await request.delete(backend + "/items/" + id);
  }
});

test("扫描 PDF 本地 OCR 状态与说明书引用", async ({ page, request }) => {
  const r = await request.post(backend + "/items", {
    data: { name: "V2 UI 扫描", purchaseDate: "2026-01-01" },
  });
  const id = (await r.json()).id;
  try {
    await page.goto("/items/" + id);
    await page.getByRole("button", { name: "说明书", exact: true }).click();
    await page
      .getByLabel("上传说明书 PDF")
      .setInputFiles(path.join(root, "frontend/tests/fixtures/scanned-care-guide.pdf"));
    await expect(page.getByText("扫描型 PDF / 暂无可提取文字")).toBeVisible();
    await page.getByRole("button", { name: "本地识别文本" }).click();
    await expect(page.getByText("已提取文字，可供 AI 引用")).toBeVisible({ timeout: 60000 });
    const answer = await (
      await request.post(backend + "/generate", {
        data: { itemId: id, question: "说明书电池保养" },
      })
    ).json();
    expect(answer.sources.some((s: { type: string }) => s.type === "说明书")).toBeTruthy();
  } finally {
    await request.delete(backend + "/items/" + id);
  }
});

test("维护编辑删除与耗材消耗撤销真实同步", async ({ page, request }) => {
  const r = await request.post(backend + "/items", {
    data: { name: "V2 UI 纠错", purchaseDate: "2026-01-01" },
  });
  const id = (await r.json()).id;
  try {
    await request.post(backend + `/items/${id}/maintenance`, {
      data: { type: "V2 清洁", date: "2026-01-01", intervalDays: 30 },
    });
    await page.goto("/items/" + id);
    await page.getByRole("button", { name: "维护记录", exact: true }).click();
    await page.getByRole("button", { name: "编辑维护" }).click();
    await page.getByLabel("周期天数").fill("60");
    await page.getByRole("button", { name: "保存维护修改" }).click();
    await expect(page.locator(".record-row")).toContainText("2026-03-02");
    page.once("dialog", (d) => d.accept());
    await page.getByRole("button", { name: "删除维护" }).click();
    await expect(page.locator(".record-row")).toHaveCount(0);
    const c = await (
      await request.post(backend + "/consumables", {
        data: { itemId: id, name: "V2 UI 测试耗材", currentStock: 5 },
      })
    ).json();
    await request.post(backend + `/consumables/${c.id}/consume`, {
      data: { date: "2026-01-01", quantity: 1 },
    });
    await page.goto("/consumables");
    await page.locator(".consumable-card").filter({ hasText: "V2 UI 测试耗材" }).click();
    page.once("dialog", (d) => d.accept());
    await page.getByRole("button", { name: "撤销消耗" }).click();
    await expect(page.getByRole("button", { name: "撤销消耗" })).toHaveCount(0);
    const detail = await (await request.get(backend + "/items/" + id)).json();
    expect(detail.consumables[0].currentStock).toBe(5);
  } finally {
    await request.delete(backend + "/items/" + id);
  }
});

test("实际局域网服务、生产 SPA、只读 QR PNG 与撤销", async ({ page, request }) => {
  const port = await new Promise<number>((resolve) => {
    const server = net.createServer();
    server.listen(0, "127.0.0.1", () => {
      const p = (server.address() as net.AddressInfo).port;
      server.close(() => resolve(p));
    });
  });
  const python = process.env.WUSHENG_PYTHON || path.join(root, ".venv/Scripts/python.exe");
  const data = path.join(
    process.env.WUSHENG_TEST_DATA_DIR || path.join(root, "tmp"),
    "lan-validation",
  );
  const child = spawn(
    python,
    [
      "-m",
      "uvicorn",
      "backend.main:app",
      "--host",
      "0.0.0.0",
      "--port",
      String(port),
      "--no-proxy-headers",
    ],
    {
      cwd: root,
      env: {
        ...process.env,
        WUSHENG_DATA_DIR: data,
        WUSHENG_SHARE_MODE: "lan",
        WUSHENG_PORT: String(port),
      },
      stdio: "ignore",
      windowsHide: true,
    },
  );
  const base = `http://127.0.0.1:${port}`;
  try {
    await expect
      .poll(
        async () => {
          try {
            return (await request.get(base + "/health")).status();
          } catch {
            return 0;
          }
        },
        { timeout: 60000 },
      )
      .toBe(200);
    const info = await (await request.get(base + "/network/share-info")).json();
    expect(info.reachable).toBeTruthy();
    await page.goto(base + "/items/headphones");
    await expect(page.locator(".detail-title h1")).toHaveText("Sony WH-1000XM6");
    await page.getByRole("button", { name: "生成二维码" }).click();
    await expect(page.getByLabel("分享有效期")).toHaveValue("7d");
    await expect(page.getByText("分享内容预览", { exact: true })).toBeVisible();
    await page.getByLabel("耗材状态", { exact: true }).uncheck();
    await page.getByRole("button", { name: "生成只读二维码" }).click();
    await expect(page.getByRole("img", { name: "物品档案二维码" })).toBeVisible();
    const link = await (await request.post(base + "/items/headphones/share")).json();
    expect(link.url).not.toContain("127.0.0.1");
    expect(link.url).not.toContain("localhost");
    const readonly = await request.get(link.url.replace("/share/", "/api/share-data/"));
    expect(readonly.status()).toBe(200);
    const shared = await readonly.json();
    expect(shared.item).not.toHaveProperty("purchaseDate");
    expect(shared.item).not.toHaveProperty("serialNumber");
    expect(shared.consumables).toHaveLength(0);
    expect(link.expiresAt).toBeTruthy();
    expect((await request.get(info.recommendedBaseUrl + "/api/snapshot")).status()).toBe(403);
    const download = page.waitForEvent("download");
    await page.getByRole("link", { name: "下载 PNG" }).click();
    const png = await readFile((await (await download).path())!);
    expect(png.subarray(1, 4).toString()).toBe("PNG");
    // Decode the actual generated PNG with a preinstalled local QR decoder, not the label text.
    const { execFileSync } = await import("node:child_process");
    const decoded = execFileSync(
      python,
      [
        "-c",
        "import cv2,sys; print(cv2.QRCodeDetector().detectAndDecode(cv2.imread(sys.argv[1]))[0])",
        (await (await download).path())!,
      ],
      { encoding: "utf8" },
    ).trim();
    expect(decoded).toBe(link.url);
    await page.goto(link.url);
    await expect(page.locator(".share-page h1")).toHaveText("Sony WH-1000XM6");
    await expect(page.getByRole("button")).toHaveCount(0);
    await request.delete(base + "/items/headphones/share");
    await page.reload();
    await expect(page.getByRole("alert")).toContainText("已过期或已撤销");
  } finally {
    child.kill();
    await new Promise<void>((resolve) => {
      if (child.exitCode !== null) resolve();
      else child.once("exit", () => resolve());
    });
  }
});

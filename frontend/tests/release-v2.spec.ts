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

test("普通 start.ps1、生产 SPA、LAN QR 解码与远程管理隔离", async ({ page, request }) => {
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
    "powershell.exe",
    [
      "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
      path.join(root, "scripts/start.ps1"), "-NoBrowser", "-Port",
      String(port),
      "-Python", python,
    ],
    {
      cwd: root,
      env: {
        ...process.env,
        WUSHENG_DATA_DIR: data,
      },
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    },
  );
  let output = "";
  child.stdout?.on("data", (chunk) => { output += chunk.toString(); });
  child.stderr?.on("data", (chunk) => { output += chunk.toString(); });
  const base = `http://127.0.0.1:${port}`;
  try {
    await expect.poll(() => child.exitCode, { timeout: 60000, message: "Normal startup must complete successfully" }).toBe(0);
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
    expect(info.mode).toBe("lan-ready");
    expect(info.reachable).toBeTruthy();
    await page.goto(base + "/items/headphones");
    await expect(page.locator(".detail-title h1")).toHaveText("Sony WH-1000XM6");
    await page.getByRole("button", { name: "生成二维码" }).click();
    await expect(page.getByRole("status").filter({ hasText: "局域网分享已就绪" })).toBeVisible();
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
    for (const endpoint of ["items", "backup", "generate", "reminders", "documents", "repairs", "consumables", "drafts"]) {
      expect((await request.get(info.recommendedBaseUrl + "/api/" + endpoint, { headers: { "X-Forwarded-For": "127.0.0.1" } })).status()).toBe(403);
      expect((await request.post(info.recommendedBaseUrl + "/api/" + endpoint, { data: {} })).status()).toBe(403);
    }
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
    // Exercise the actual LAN URL using an isolated production database, not mocked HTTP.
    const pdfUpload = await request.post(base + "/items/printer/documents/manual", { multipart: {
      file: { name: "LAN合成说明书.pdf", mimeType: "application/pdf", buffer: await readFile(path.join(root, "frontend/tests/fixtures/scanned-care-guide.pdf")) },
    } });
    expect(pdfUpload.status()).toBe(201);
    const document = await pdfUpload.json();
    const printerLink = await (await request.post(base + "/items/printer/share?regenerate=true", { data: {
      options: { showManualFiles: true, showManualDownloads: true, manualDocumentIds: [document.id] },
    } })).json();
    const lanBase = new URL(printerLink.url).origin;
    expect(lanBase).not.toContain("127.0.0.1");
    const printerDataResponse = await request.get(printerLink.url.replace("/share/", "/api/share-data/"));
    expect(printerDataResponse.status()).toBe(200);
    const printerData = await printerDataResponse.json();
    const cover = await request.get(lanBase + printerData.item.coverImage);
    expect(cover.status()).toBe(200);
    expect(cover.headers()["content-type"]).toBe("image/png");
    expect(printerData.item.coverImage).toBe("/assets/items/hp-printer.png");
    const pdfUrl = lanBase + printerData.manuals[0].viewUrl;
    const pdfResponse = await request.get(pdfUrl);
    expect(pdfResponse.status()).toBe(200);
    expect(pdfResponse.headers()["content-type"]).toBe("application/pdf");
    expect(pdfResponse.headers()["cache-control"]).toBe("no-store");
    expect((await pdfResponse.body()).subarray(0, 4).toString()).toBe("%PDF");
    expect((await request.get(pdfUrl + "?download=true")).headers()["content-disposition"]).toContain("attachment;");
    expect((await request.get(lanBase + "/api/documents/" + document.id + "/file")).status()).toBe(403);
    const html = await request.get(printerLink.url, { headers: { Accept: "text/html" } });
    expect((await html.text()).match(/<title>(.*?)<\/title>/)?.[1]).not.toContain("Wusheng");
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(printerLink.url);
    await expect(page.locator(".share-photo")).toHaveAttribute("data-image-state", "loaded");
    await expect(page.getByRole("link", { name: "在线查看" })).toBeVisible();
    await request.delete(base + "/items/printer/share");
    expect((await request.get(pdfUrl)).status()).toBe(404);
    await page.reload();
    await expect(page.getByRole("alert")).toContainText("已过期或已撤销");
  } finally {
    const serverPid = output.match(/WUSHENG_SERVER_PID=(\d+)/)?.[1];
    if (serverPid) process.kill(Number(serverPid));
    child.kill();
    await new Promise<void>((resolve) => {
      if (child.exitCode !== null) resolve();
      else child.once("exit", () => resolve());
    });
  }
});

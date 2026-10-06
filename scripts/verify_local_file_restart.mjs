/** Two-stage real browser persistence check. Run prepare, restart servers, then verify.
 * Uses only synthetic test records; verify deletes its own fixture and attachments.
 */
import { chromium } from "../frontend/node_modules/@playwright/test/index.mjs";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import assert from "node:assert/strict";
import { tmpdir } from "node:os";
import { createHash } from "node:crypto";
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const stateFile = process.env.WUSHENG_RESTART_STATE_FILE || path.join(tmpdir(), "wusheng-local-file-restart.json");
const reportDir = path.join(root, "docs/competition/local-files");
const base = process.env.WUSHENG_TEST_BASE_URL || "http://127.0.0.1:5173";
const backend = process.env.WUSHENG_TEST_API_URL || "http://127.0.0.1:8000";
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
async function api(url, options) {
  const response = await fetch(backend + url, options);
  assert.ok(response.ok, `HTTP ${response.status}: ${url}`);
  return response.json();
}
const browser = await chromium.launch({
  headless: true,
  channel: "msedge",
  ...(process.env.WUSHENG_EDGE_PATH ? { executablePath: process.env.WUSHENG_EDGE_PATH } : {}),
});
let fixtureId;
try {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  if (process.argv[2] === "prepare") {
    await page.goto(base + "/items/new");
    const chooser = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: "选择图片", exact: true }).click();
    await (
      await chooser
    ).setFiles([
      path.join(root, "frontend/public/assets/headphones-detail.jpg"),
      path.join(root, "docs/references/demo-receipt.png"),
    ]);
    await page.getByRole("button", { name: "开始识别", exact: true }).waitFor({ state: "visible" });
    await page.waitForFunction(() => !document.querySelector(".recognize-button")?.disabled);
    await page.getByLabel("图片 2 类型").selectOption("receipt");
    await page.waitForFunction(() => !document.querySelector(".recognize-button")?.disabled);
    await page.getByRole("button", { name: "开始识别", exact: true }).click();
    await page.getByText("本地 OCR", { exact: true }).waitFor();
    await page.getByLabel("商品名称", { exact: true }).fill("重启验证临时耳机（自动清理）");
    await page
      .getByLabel("购买日期", { exact: true })
      .fill(
        new Intl.DateTimeFormat("en-CA", {
          timeZone: "Asia/Shanghai",
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
        }).format(new Date()),
      );
    await page.getByRole("button", { name: "确认并保存", exact: true }).click();
    await page.waitForURL(/\/items\/(?!new$)[^/]+$/);
    const id = page.url().split("/").pop();
    fixtureId = id;
    await page.getByRole("button", { name: "说明书", exact: true }).click();
    const pdfChooser = page.waitForEvent("filechooser");
    await page.getByRole("button", { name: "上传 PDF", exact: true }).click();
    await (await pdfChooser).setFiles(path.join(root, "data/uploads/demo-care-guide.pdf"));
    await page.locator(".document-card").waitFor();
    const detail = await api("/items/" + id);
    assert.equal(detail.images.length, 2);
    assert.equal(detail.documents.length, 1);
    const files = [...detail.images, ...detail.documents];
    for (const file of files)
      assert.equal(
        hash(Buffer.from(await (await fetch(backend + file.filePath)).arrayBuffer())),
        file.sha256,
      );
    await writeFile(
      stateFile,
      JSON.stringify({ id, files, preparedAt: new Date().toISOString() }, null, 2),
    );
    console.log(JSON.stringify({ prepared: true, itemId: id, images: 2, manuals: 1, errors }));
    assert.deepEqual(errors, []);
  } else if (process.argv[2] === "verify") {
    const state = JSON.parse(await readFile(stateFile, "utf8"));
    try {
      await page.goto(base + "/items/" + state.id);
      await page.locator(".detail-title h1").waitFor();
      await page.waitForFunction(() =>
        [...document.querySelectorAll(".main-image img")].every(
          (image) => image.complete && image.naturalWidth > 0,
        ),
      );
      await page.reload();
      await page.getByRole("button", { name: "说明书", exact: true }).click();
      await page.locator(".document-card").waitFor();
      const detail = await api("/items/" + state.id);
      assert.equal(detail.images.length, 2);
      assert.equal(detail.documents.length, 1);
      for (const file of state.files) {
        const response = await fetch(backend + file.filePath);
        assert.ok(response.ok);
        assert.equal(hash(Buffer.from(await response.arrayBuffer())), file.sha256);
      }
      const answer = await api("/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ itemId: state.id, question: "说明书里如何清洁？" }),
      });
      assert.ok(answer.answer.includes("依据已上传说明书"));
      await mkdir(reportDir, { recursive: true });
      await page.screenshot({ path: path.join(reportDir, "after-restart.png"), fullPage: true });
      assert.deepEqual(errors, []);
      const report = {
        passed: true,
        preparedAt: state.preparedAt,
        verifiedAt: new Date().toISOString(),
        images: 2,
        manuals: 1,
        originalHashesPreserved: true,
        refreshPassed: true,
        aiManualEvidence: true,
        consoleErrors: errors,
        fixtureDeleted: true,
      };
      await api("/items/" + state.id, { method: "DELETE" });
      for (const file of state.files)
        assert.equal((await fetch(backend + file.filePath)).status, 404);
      await writeFile(
        path.join(reportDir, "restart-verification.json"),
        JSON.stringify(report, null, 2),
      );
      console.log(JSON.stringify(report));
    } catch (e) {
      await api("/items/" + state.id, { method: "DELETE" }).catch(() => {});
      throw e;
    }
  } else throw new Error("Use prepare or verify");
} catch (e) {
  if (process.argv[2] === "prepare" && fixtureId)
    await api("/items/" + fixtureId, { method: "DELETE" }).catch(() => {});
  throw e;
} finally {
  await browser.close();
}

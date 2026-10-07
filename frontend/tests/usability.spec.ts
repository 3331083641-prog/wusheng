import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";

test("MacBook 主导出为 PDF，次级原始数据为 JSON", async ({ page }) => {
  await page.goto("/items/laptop");
  const pdf = page.waitForEvent("download");
  await page.getByRole("button", { name: "导出档案", exact: true }).click();
  const archive = await pdf;
  expect(archive.suggestedFilename()).toBe("物生-MacBook Air M2-物品档案.pdf");
  expect((await readFile((await archive.path())!)).subarray(0, 4).toString()).toBe("%PDF");
  const json = page.waitForEvent("download");
  await page.getByRole("button", { name: "导出原始数据 JSON", exact: true }).click();
  const raw = await json;
  expect(raw.suggestedFilename()).toBe("物生-MacBook Air M2.json");
  expect(JSON.parse(await readFile((await raw.path())!, "utf8")).item.name).toBe("MacBook Air M2");
});

test("1440/1920 品牌只有 Logo 与物生，原有导航尺寸保持", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  for (const [width, height] of [[1440, 900], [1920, 1080]]) {
    await page.setViewportSize({ width, height });
    await page.goto("/");
    const logo = page.locator(".sidebar .logo");
    await expect(logo).toHaveText("物生");
    await expect(logo.locator(".logo-symbol img")).toBeVisible();
    const size = await logo.locator(".logo-symbol").boundingBox();
    expect(size?.width).toBe(36);
    expect(size?.height).toBe(36);
    expect(await logo.evaluate((element) => getComputedStyle(element).gap)).toBe("11px");
    await expect(page.getByRole("navigation").getByRole("link", { name: "我的物品", exact: true })).toBeVisible();
  }
  expect(errors).toEqual([]);
});

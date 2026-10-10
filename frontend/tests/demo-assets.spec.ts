import { test, expect } from "@playwright/test";
import path from "node:path";
const backend=process.env.WUSHENG_TEST_API_URL || "http://127.0.0.1:8000";
test("新版 Demo 的相册只包含本体，合成票据分类展示且不当作正式 PDF", async ({ page,request })=>{
  await page.emulateMedia({reducedMotion:"reduce"});
  const data=await (await request.get(backend+"/items/printer")).json();
  const papers=data.images.filter((i:{source:string})=>i.source==="synthetic-demo-v3");
  expect(papers).toHaveLength(4);
  for(const width of [1440,390]){
    await page.setViewportSize({width,height:900});await page.goto("/items/printer");
    await expect(page.locator(".main-image img")).toHaveAttribute("src","/assets/items/hp-printer.png");
    await expect(page.locator(".thumbnails img")).toHaveCount(1);
    await page.getByRole("button",{name:"凭证资料",exact:true}).click();
    await expect(page.locator(".evidence-card")).toHaveCount(4);
    await expect(page.getByText("合成演示资料 · 非真实购物凭证",{exact:true})).toHaveCount(4);
    for(const a of await page.locator(".evidence-card img").all()){
      await a.scrollIntoViewIfNeeded();
      await expect.poll(()=>a.evaluate((img:HTMLImageElement)=>img.naturalWidth)).toBeGreaterThan(300);
    }
    await page.screenshot({path:path.resolve(`../docs/competition/demo-assets-detail-${width}.png`),fullPage:true});
    await page.getByRole("button",{name:"说明书",exact:true}).click();
    await expect(page.locator(".document-card")).toHaveCount(data.documents.length);
  }
});
test("最终 Demo 的型号、高清主图和耗材关联同源",async({page,request})=>{
  const images:Record<string,string>={ac:"midea-ac-final.png",coffee:"delonghi-ec680-illustration.png",toothbrush:"philips-toothbrush-final.png",suitcase:"silver-suitcase-final.png"};
  for(const [id,model] of [["ac","KFR-35GW/N8KS1-1U"],["coffee","EC680.S"],["toothbrush","HX6850"],["suitcase","TR-2001"]]){
    const d=await (await request.get(backend+"/items/"+id)).json();expect(d.item.model).toBe(model);
    await page.goto("/items/"+id);await expect(page.locator(".detail-info")).toContainText(model);
    await expect(page.locator(".main-image img")).toHaveAttribute("src","/assets/items/"+images[id]);
    await expect.poll(()=>page.locator(".main-image img").evaluate((img:HTMLImageElement)=>img.naturalWidth)).toBe(1448);
  }
  await page.goto("/consumables");
  await expect(page.locator(".consumable-card")).toHaveCount(7);
  await expect(page.locator(".consumable-card").filter({hasText:"空调滤尘网"})).toContainText("美的空调");
  await expect(page.locator(".consumable-card").filter({hasText:"打印机墨盒"})).toContainText("适配性待核实");
  await expect(page.locator(".consumable-card").filter({hasText:"E.S.E."})).toContainText("44mm");
});

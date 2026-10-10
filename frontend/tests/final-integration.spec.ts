import { test, expect } from "@playwright/test";
const backend=process.env.WUSHENG_TEST_API_URL || "http://127.0.0.1:8000";

test("三组最终凭证和主相册分离，高清资料可打开",async({page,request})=>{
  for(const id of ['ac','toothbrush','suitcase']){
    const data=await(await request.get(backend+'/items/'+id)).json();
    await page.goto('/items/'+id);
    await expect(page.locator('.thumbnails img')).toHaveCount(1);
    await page.getByRole('button',{name:'凭证资料',exact:true}).click();
    await expect(page.locator('.evidence-card')).toHaveCount(4);
    await expect(page.getByText('合成演示资料 · 非真实购物凭证',{exact:true})).toHaveCount(4);
    await expect(page.locator('.evidence-grid')).not.toContainText('待核实');
    for(const image of data.images.filter((a:{source:string})=>a.source==='synthetic-demo-v3')){
      const response=await request.get(image.filePath);
      expect(response.ok()).toBeTruthy();expect(response.headers()['content-type']).toContain('image/png');
      expect((await response.body()).readUInt32BE(16)).toBeGreaterThan(300);
    }
  }
});

test("二维码重新检测保留有效地址，IP 改变清除旧码并要求重新生成",async({page})=>{
  let address='192.168.1.10';
  await page.route('**/api/network/share-info',route=>route.fulfill({json:{mode:'lan-ready',reachable:true,port:8002,lanAddresses:[address],interfaces:[{address,name:'WLAN'}],recommendedBaseUrl:`http://${address}:8002`}}));
  await page.route('**/api/items/ac/share?*',route=>route.fulfill({json:{url:`http://${address}:8002/share/test-token`,expiresAt:null}}));
  await page.goto('/items/ac');
  await page.getByRole('button',{name:'生成二维码',exact:true}).click();
  await page.getByRole('button',{name:'生成只读二维码',exact:true}).click();
  await expect(page.getByAltText('物品档案二维码')).toBeVisible();
  await page.getByRole('button',{name:'重新检测网络',exact:true}).click();
  await expect(page.getByAltText('物品档案二维码')).toBeVisible();
  address='192.168.1.20';
  await page.getByRole('button',{name:'重新检测网络',exact:true}).click();
  await expect(page.getByAltText('物品档案二维码')).toHaveCount(0);
  await expect(page.getByRole('alert')).toContainText('IP 或端口已改变');
  await page.getByRole('button',{name:'生成只读二维码',exact:true}).click();
  await expect(page.getByRole('link',{name:'http://192.168.1.20:8002/share/test-token',exact:true})).toBeVisible();
  await expect(page.getByRole('alert')).toHaveCount(0);
});

test("AI 前端真实请求九类档案问题，Provider 与无证据状态可见",async({page,request})=>{
  const item=await(await request.get(backend+'/items/ac')).json();
  const cases=[['当前物品是什么品牌和型号？',item.item.model],['当前物品有哪些说明书资料？','说明书'],['根据当前 PDF，该怎样使用或维护？','说明书'],['什么时候需要进行下一次维护？',item.item.nextMaintenance],['我的保修是否还有效？','保修'],['目前有哪些关联耗材？','空调滤尘网'],['空调滤尘网预计什么时候需要补充？','历史不足'],['当前物品有什么维修记录？','没有找到'],['火星上的未知面积是多少？','没有找到']];
  await page.goto('/assistant?item=ac');
  for(const [question,expected] of cases){
    const reply=page.waitForResponse(r=>r.url().endsWith('/api/generate') && r.request().method()==='POST');
    await page.getByRole('textbox',{name:'向当前物品助手提问'}).fill(question);
    await page.getByRole('button',{name:'发送问题'}).click();
    const response=await reply;expect(response.ok()).toBeTruthy();
    const data=await response.json();expect(data.activeProvider).toBe('evidence');expect(data.modelInvoked).toBe(false);
    await expect(page.locator('.chat-message.assistant').last()).toContainText(expected);
    await expect(page.locator('.chat-message.assistant').last()).toContainText('本地档案规则');
    await expect(page.getByRole('button',{name:'发送问题'})).toBeDisabled(); // empty input after successful send
    await expect(page.locator('.typing')).toHaveCount(0);
  }
});

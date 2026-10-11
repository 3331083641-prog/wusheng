import {createRequire} from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const ROOT=path.dirname(fileURLToPath(import.meta.url));
const require=createRequire(path.join(ROOT,'../frontend/package.json'));
const {chromium}=require('@playwright/test');
const base=process.env.VIDEO_BASE||'http://127.0.0.1:8006';
const stage=process.argv[2]||'create';
fs.mkdirSync(`${ROOT}/recordings/raw`,{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
const context=await browser.newContext({viewport:{width:1920,height:1080},recordVideo:{dir:`${ROOT}/recordings/raw`,size:{width:1920,height:1080}},acceptDownloads:true,locale:'zh-CN'});
await context.addInitScript(()=>{
 window.addEventListener('DOMContentLoaded',()=>{
  const pointer=document.createElement('div');pointer.id='recording-pointer';
  pointer.style.cssText='position:fixed;left:960px;top:540px;width:18px;height:18px;border:3px solid #247b57;background:#ffffff99;border-radius:50%;pointer-events:none;z-index:2147483647;box-shadow:0 1px 6px #0003;transform:translate(-50%,-50%)';document.body.appendChild(pointer);
  document.addEventListener('mousemove',e=>{pointer.style.left=e.clientX+'px';pointer.style.top=e.clientY+'px'});
  document.addEventListener('mousedown',()=>{pointer.style.background='#6abb8b';pointer.style.width='27px';pointer.style.height='27px'});
  document.addEventListener('mouseup',()=>{pointer.style.background='#ffffff99';pointer.style.width='18px';pointer.style.height='18px'});
 });
});
const page=await context.newPage();page.setDefaultTimeout(20000);
const started=Date.now(), marks=[],responses=[];
const reportFile=`${ROOT}/reports/capture-${stage}-raw.json`;
const stateFile=`${ROOT}/runtime/recording-state.json`;
let state=fs.existsSync(stateFile)?JSON.parse(fs.readFileSync(stateFile,'utf8')):{};
page.on('response',async r=>{if(r.url().includes('/api/') && r.request().method()!=='GET'){let data;try{data=await r.json()}catch{}responses.push({time:(Date.now()-started)/1000,url:r.url(),status:r.status(),method:r.request().method(),data});}});
page.on('pageerror',e=>console.log('PAGE ERROR',e.message));
const mark=(name,extra={})=>{let m={name,time:(Date.now()-started)/1000,...extra};marks.push(m);console.log(JSON.stringify(m));};
const pause=async(ms=1400)=>page.waitForTimeout(ms);
async function click(locator,name){await locator.scrollIntoViewIfNeeded();const b=await locator.boundingBox();if(b){await page.mouse.move(b.x+b.width/2,b.y+b.height/2,{steps:14});mark(name||'click',{x:b.x+b.width/2,y:b.y+b.height/2});}await pause(250);await locator.click();await pause(800);}
const button=n=>page.getByRole('button',{name:n,exact:true});
const go=async(url)=>{await page.goto(base+url);await page.waitForLoadState('networkidle');await pause();};
async function upload(kind,files){const chooser=page.waitForEvent('filechooser');await click(button(kind),'upload '+kind);await (await chooser).setFiles(files.map(n=>`${ROOT}/assets/${n}`));await page.waitForFunction(()=>!document.body.innerText.includes('上传中… 图片正保存'));await pause(1000);}
async function field(name,value){const l=page.getByRole('textbox',{name,exact:true});await click(l,'confirm '+name);await l.fill(value);await pause(450);}
try{
 if(stage==='home'){
  await go('/');mark('home start');await pause(9000);await page.mouse.move(1420,480,{steps:30});await pause(5500);await page.mouse.wheel(0,440);await pause(4200);await page.mouse.wheel(0,-440);await pause(4500);mark('home end');
 }
 if(stage==='create'){
  await go('/');mark('create start');await click(page.getByRole('link',{name:'添加物品',exact:true}).first(),'add item');
  await upload('物品本体照片',['product.png','scene.png']);
  await upload('包装盒 / 铭牌',['package.png']);
  await upload('小票 / 发票',['order.png']);
  await upload('说明书照片',['manual_image.png']);
  await upload('包装盒 / 铭牌',['warranty.png']);
  mark('ocr begin');const recognized=page.waitForResponse(r=>r.url().includes('/recognize')&&r.request().method()==='POST',{timeout:180000});
  await click(button('开始识别'),'recognize');const ocr=await recognized;state.ocrStatus=ocr.status();state.ocr=await ocr.json();mark('ocr complete',{status:ocr.status()});await pause(2500);
  const evidence=page.locator('summary').filter({hasText:'查看原始识别文字与字段来源'});if(await evidence.count()){await click(evidence,'field sources');await pause(2500);await click(evidence,'close field sources');}
  await field('商品名称','飞利浦电动剃须刀');await field('品牌','Philips 飞利浦');await field('型号','S5898/35');
  await page.getByLabel('类别',{exact:true}).selectOption('家电');
  await page.getByLabel('购买价格（元）',{exact:true}).fill('799');await page.getByLabel('购买日期',{exact:true}).fill('2024-08-23');
  await page.getByLabel('保修期限（月）',{exact:true}).fill('24');
  const note=page.getByPlaceholder('使用场景、特殊情况等…');if(await note.count())await note.fill('比赛演示档案；指定 Demo 素材，不代表已验证真实交易。');
  await pause(2200);await click(button('确认并保存'),'save confirmed item');await page.waitForURL(/\/items\/(?!new)[^/]+$/);state.itemId=page.url().split('/').pop();mark('saved',{itemId:state.itemId});
  fs.writeFileSync(stateFile,JSON.stringify(state,null,2));await pause(3000);await click(page.getByRole('link',{name:'我的物品',exact:true}).first(),'item list');await pause(2500);mark('create end');
 }
 if(stage==='detail'){
  await go(`/items/${state.itemId}`);mark('detail start');const thumbs=page.locator('.thumbnails button');if(await thumbs.count()>1){await click(thumbs.nth(1),'scene photograph');await pause(1400);await click(thumbs.first(),'product photograph');}
  await click(button('凭证资料'),'evidence documents');await pause(1800);
  const detail=await (await context.request.get(`${base}/api/items/${state.itemId}`)).json();
  const warranty=detail.images.find(i=>i.originalFilename==='warranty.png');if(warranty)await page.getByLabel(`资料 ${warranty.id} 类型`,{exact:true}).selectOption('warranty_card');
  await pause(2000);await click(button('说明书'),'manual tab');mark('pdf upload start');
  await page.getByLabel('上传说明书 PDF',{exact:true}).setInputFiles(`${ROOT}/assets/电动剃须刀说明书.pdf`);
  await page.getByText('已提取文字，可供 AI 引用',{exact:true}).waitFor({timeout:60000});mark('pdf upload complete');await pause(1800);
  const d=await (await context.request.get(`${base}/api/items/${state.itemId}`)).json();state.document=d.documents.find(x=>(x.originalFilename||x.filename).includes('电动剃须刀'));fs.writeFileSync(stateFile,JSON.stringify(state,null,2));
  const pdf=await context.request.get(base+state.document.filePath);fs.writeFileSync(`${ROOT}/runtime/manual-downloaded.pdf`,await pdf.body());mark('pdf download verified',{status:pdf.status(),pages:state.document.pageCount,textLength:state.document.extractedText.length});
  const popupPromise=page.waitForEvent('popup');await click(page.getByLabel('查看 电动剃须刀说明书.pdf',{exact:true}),'open manual PDF');
  const popup=await popupPromise;await popup.waitForTimeout(6000);await popup.screenshot({path:`${ROOT}/reports/pdf-viewer.png`});state.pdfPopupVideo=await popup.video().path();await popup.close();
  await page.reload();await page.waitForLoadState('networkidle');await pause(1800);mark('refresh persisted');
  await click(button('基本信息'),'lifecycle');await page.mouse.wheel(0,480);await pause(2000);await page.mouse.wheel(0,-480);await pause(1200);
  const dl=page.waitForEvent('download');await click(button('导出档案'),'export archive');await(await dl).saveAs(`${ROOT}/runtime/剃须刀物品档案.pdf`);mark('archive PDF saved');await pause(2500);mark('detail end');
 }
 if(stage==='evidence'||stage==='qwen'){
  await go(`/assistant?item=${state.itemId}`);mark(stage+' start');
  const qs=stage==='qwen'?[process.env.VIDEO_QWEN_QUESTION||'请只依据档案，整理已上传说明书名称、最近维护记录和两类耗材库存。历史不足不估算补货天数，不提供清洁步骤，100字以内。']:['这件剃须刀有哪些相关耗材？','什么时候需要进行下一次维护？','这件剃须刀的内部芯片是什么？'];
  for(const q of qs){const l=page.getByRole('textbox',{name:'向当前物品助手提问'});await click(l,'question');await l.pressSequentially(q,{delay:60});await pause(700);const response=page.waitForResponse(r=>r.url().endsWith('/api/generate')&&r.request().method()==='POST',{timeout:120000});mark('AI request',{question:q});await click(button('发送问题'),'send question');const rr=await response;const data=await rr.json();mark('AI response',{provider:data.activeProvider,modelInvoked:data.modelInvoked,model:data.model,status:rr.status()});await pause(stage==='qwen'?12000:5500);}
  mark(stage+' end');
 }
 if(stage==='consumable-create'){
  await go('/consumables');mark('consumable create start');
  for(const [name,unit,stock] of [['剃须刀清洁液','瓶','3'],['旋转式替换刀头 SH71','枚','3']]){
   await click(button('关联耗材'),'associate consumable');await page.getByLabel('关联设备',{exact:true}).selectOption(state.itemId);
   await page.locator('input[name=name]').fill(name);await page.locator('input[name=unit]').fill(unit);await page.locator('input[name=stock]').fill(stock);await pause(1800);await click(button('保存记录'),'save consumable');await pause(1800);
  }
  mark('consumable create end');
 }
 if(stage==='consumables'){
  await go('/consumables');mark('consumables start');await page.getByLabel('搜索耗材',{exact:true}).fill('剃须刀');await pause(2300);
  await click(page.locator('.consumable-card').filter({hasText:'剃须刀清洁液'}),'cleaner inventory');await pause(2200);
  await page.locator('input[name=quantity]').fill('1');await pause(900);await click(button('保存记录'),'record actual consumption');await pause(1500);
  await click(button('补充库存'),'restock');await page.locator('input[name=quantity]').fill('2');await page.locator('input[name=cost]').fill('59');await pause(800);await click(button('保存记录'),'record restock');await pause(1600);
  await page.keyboard.press('Escape');await page.getByLabel('搜索耗材',{exact:true}).fill('空气净化器滤芯');await pause(1000);await click(page.locator('.consumable-card').first(),'historical prediction');await pause(3800);await page.keyboard.press('Escape');
  await go(`/items/${state.itemId}`);await click(button('维护记录'),'maintenance tab');await click(button('记录维护'),'record maintenance');
  await page.locator('input[name=type]').fill('刀头清洁维护');await page.locator('input[name=date]').fill('2026-10-11');await page.locator('input[name=interval]').fill('7');await page.locator('textarea[name=description]').fill('比赛演示：完成刀头清洁，晾干后装回；记录下一次维护日期。');await pause(1200);await click(button('保存维护记录'),'save maintenance');await pause(2400);
  await go('/reminders');await pause(3000);mark('consumables end');
 }
 if(stage==='share'){
  await go(`/items/${state.itemId}`);mark('share start');await click(button('生成二维码'),'one item one code');await pause(1800);
  await page.getByLabel('分享有效期',{exact:true}).selectOption('7d');await page.getByLabel('允许查看所选说明书 PDF',{exact:true}).check();await page.getByLabel('电动剃须刀说明书.pdf',{exact:true}).check();await pause(1400);
  const r=page.waitForResponse(r=>r.url().includes('/share?')&&r.request().method()==='POST');await click(button('生成只读二维码'),'generate QR');state.share=await (await r).json();fs.writeFileSync(stateFile,JSON.stringify(state,null,2));await pause(1300);await page.getByRole('img',{name:'物品档案二维码'}).scrollIntoViewIfNeeded();mark('QR fully visible');await pause(9500);mark('share generated');
 }
 if(stage==='mobile'){
  throw new Error('Use record_mobile.mjs for mobile viewport capture');
 }
 if(stage==='repairs'){
  await go(`/repairs?item=${state.itemId}`);mark('repairs start');await click(button('新增维修记录'),'new repair');await page.locator('input[name=issue]').fill('使用噪声检查（比赛演示）');await page.locator('select[name=serviceType]').selectOption('自行检查');await page.locator('textarea[name=description]').fill('隔离演示数据，用于展示报修和状态流转。');await pause(900);await click(button('创建报修记录'),'create repair');await pause(1400);
  await click(page.getByLabel('查看飞利浦电动剃须刀维修详情',{exact:true}),'repair details');await page.locator('select[name=status]').selectOption('诊断中');await pause(1400);await click(button('保存维修进度'),'save repair status');await pause(1600);
  await go('/statistics');mark('statistics');await pause(3500);await page.mouse.wheel(0,380);await pause(2500);mark('repairs end');
 }
 if(stage==='close'){await go('/');mark('closing home');await pause(15000);}
 if(stage==='github'){
  await page.goto('https://github.com/3331083641-prog/wusheng',{waitUntil:'domcontentloaded',timeout:60000});await pause(4000);mark('GitHub public repository');await page.mouse.wheel(0,580);await pause(3000);await page.screenshot({path:`${ROOT}/reports/github-current.png`});
 }
}catch(e){mark('ERROR',{message:e.message});await page.screenshot({path:`${ROOT}/reports/capture-${stage}-error.png`,fullPage:true});throw e;}
finally{
 const latest=fs.existsSync(stateFile)?JSON.parse(fs.readFileSync(stateFile,'utf8')):{};fs.writeFileSync(stateFile,JSON.stringify({...latest,...state},null,2));await page.close();const video=await page.video().path();await context.close();await browser.close();fs.writeFileSync(reportFile,JSON.stringify({stage,base,video,marks,responses,duration:(Date.now()-started)/1000},null,2));console.log('VIDEO',video);
}

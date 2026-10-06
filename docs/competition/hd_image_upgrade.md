# 高清物品图片替换验收

日期：2026-10-01。范围为图片资产、显示与加载；保持物生现有页面结构、卡片尺寸、导航、字体、颜色、功能与数据库业务记录。

## 原图与物品绑定

目录：`frontend/public/assets/items/`。10 张原图均为 **1448×1086 PNG**，字节复制后 SHA256 与用户提供源文件一致；没有压缩、缩小、重绘、蒙版或图片色彩处理。

| Item ID    | 当前物品        | 文件                            |
| ---------- | --------------- | ------------------------------- |
| laptop     | MacBook Air M2  | macbook-air-m2.png              |
| headphones | Sony WH-1000XM6 | sony-wh1000xm6.png              |
| washer     | 海尔滚筒洗衣机  | haier-washer.png                |
| ac         | 美的空调        | midea-air-conditioner.png       |
| robot      | 小米扫地机器人  | xiaomi-robot-vacuum.png         |
| coffee     | 德龙咖啡机      | delonghi-coffee-machine.png     |
| toothbrush | 飞利浦电动牙刷  | philips-electric-toothbrush.png |
| suitcase   | 行李箱          | rimowa-suitcase.png             |
| purifier   | 空气净化器      | xiaomi-air-purifier.png         |
| printer    | 惠普打印机      | hp-printer.png                  |

逐图源文件名、大小与哈希见 [来源清单](../references/hd-image-assets.json)。

## 显示实现

- `frontend/src/assets/itemAssets.ts` 提供唯一 `ITEM_ASSETS` 与历史路径解析；没有修改数据库、Seed 或 API。自定义上传路径继续使用原图，墨盒耗材继续使用墨盒照片。
- `frontend/src/components/ProductImage.tsx` 提供共享加载骨架、原图解码后 250ms 淡入、缓存图片处理、失败 Cube 图标与包含物品名称/路径的 console warning。
- 保留已有图片框：网格默认宽高比 1.65、列表 1.75、窄屏 1.8，所有物品在同一布局中比例一致；`object-fit: cover` 和逐图 `object-position` 保持主体居中。详情主图仍采用原有 `contain`，直接读取 1448×1086 原图。
- 首屏前三张卡片 eager/high，其他 lazy；悬停到 1.03 的动画为 350ms。支持 `prefers-reduced-motion`，关闭缩放与骨架动画。

## 浏览器与数据验证

执行顺序：后端 `/health` → 后端只读 `/generate` → 已运行的前端 dev 服务 → Edge 浏览器验证。

验收脚本：`node scripts/verify_item_images.mjs`，**309 项断言通过**，10 张原图、6 组视口/DPI 配置、21 个页面/状态检查。完整机器可读结果：[verification.json](hd-images/verification.json)。

- 1920×1080、2560×1440、1536×864/DPR 1.25、390×844：10 张卡片的 x/y、宽高及图片框宽高与修改前基线一致（容差 0.5 CSS px）。1536×864/DPR 1.25 是 1920×1080 在 125% 缩放下的等效渲染配置，未自动操作浏览器菜单缩放。
- 补充 2560×1440/DPR 2 和 2048×1152/DPR 1.25（2560 屏的 125% 等效配置）：卡片和耳机详情原图分辨率均覆盖实际显示所需的物理像素。
- 逐件核对我的物品和 10 个详情页面的实际 URL、1448 像素原始宽度与 fit；全站首页、提醒、维修列表与抽屉、AI 助手、耗材、统计、添加页、纯 UI Demo 与全局搜索均检查，无旧设备照片在这些页面显示。
- 慢网络下显示骨架且卡片高度不变；模拟 404 后显示 Cube，不出现破图；warning 可识别物品与路径。正常路由无图片 404、图片 warning 或页面异常。
- 网格/列表切换正常；减弱动态时图片不缩放；模拟用户自定义上传图没有被演示图片 Mapping 覆盖。
- 修改前后对 SQLite 所有表排序后的记录做只读哈希比较：**完全一致**。未改变名称、型号、状态、日期、价格或生命周期逻辑。
- `npm run build` 与 `npm run lint` 通过。

验收截图见此目录的 `hd-images/`，包含 1920、2560、125% 等效视口、窄屏、耳机详情和 AI 助手。

## 旧资源检查与保留

应用运行界面中，这 10 件物品已统一使用高清 PNG。历史 JPG 路径仍存在于数据库、`backend/seed.py` 和早期 UI Demo 中，由 Mapping 转换为新图；`headphones-detail.jpg` 还被真实 OCR 测试引用。旧资源因此保留，不删除仍有引用的文件。耗材照片、植物背景与上传预览不属于本次 10 件物品资产，继续使用原有素材。

## 修改文件

- 新增：10 张高清 PNG、`frontend/src/assets/itemAssets.ts`、`frontend/src/components/ProductImage.tsx`。
- 图片引用接入：`frontend/src/components/ui.tsx`、`AppShell.tsx`；`frontend/src/pages/Home.tsx`、`Items.tsx`、`ItemDetail.tsx`、`Reminders.tsx`、`Consumables.tsx`、`Repairs.tsx`、`Assistant.tsx`。
- 显示样式：`frontend/src/styles.css`。原有尺寸、导航与页面布局声明保持不变。
- 来源/验收：`docs/references/hd-image-assets.json`、本文件、`hd-images/verification.json` 与截图、`scripts/verify_item_images.mjs`；更新 `README.md`、`THIRD_PARTY.md` 中过时的图片说明。

修改前关键文件备份保留在本机 `backups/` 目录。

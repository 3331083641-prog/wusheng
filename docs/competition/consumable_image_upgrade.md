# 耗材高清图片替换验收

2026-10-01。范围仅为耗材图片资产、显示与加载。页面布局、卡片和图片框尺寸、筛选/排序、导航、字体、现有文字、库存、预测日期及状态保持不变。

## 来源与绑定

资源目录：`frontend/public/assets/consumables/`。

| 耗材 ID         | 耗材           | 关联设备 ID | 图片文件                         |
| --------------- | -------------- | ----------- | -------------------------------- |
| purifier-filter | 空气净化器滤芯 | purifier    | air-purifier-filter-cylinder.png |
| detergent       | 洗衣液         | washer      | laundry-detergent-blue.png       |
| ink-cartridge   | 打印机墨盒     | printer     | printer-ink-cartridges-cmy.png   |
| capsules        | 咖啡胶囊       | coffee      | coffee-capsules-metallic.png     |
| brushhead       | 电动牙刷刷头   | toothbrush  | toothbrush-heads-dual.png        |
| robot-filter    | 扫地机器人滤网 | robot       | robot-vacuum-filter-rect.png     |

6 张图均为 **1448×1086 原始 PNG**，原样复制、保留图片自身的白底和自然静物细节。源文件与正式资源 SHA256 一致；没有截图、压缩、重绘、Base64 或色彩/背景加工。详细源文件名、尺寸、字节数与哈希见 [来源清单](../references/consumable-image-assets.json)。

## 统一显示

`frontend/src/assets/consumableAssets.ts` 定义 `CONSUMABLE_ASSETS`。按耗材 ID 或设备与名称组合解析旧路径，特别区分原来共用 `/assets/filter.jpg` 的圆柱滤芯和矩形滤网；不会只凭同名文件猜测。用户上传的自定义图片路径继续使用。

`ConsumableImage` 复用已有 `ProductImage` 的骨架、图片解码、250ms 淡入、Lazy Loading、错误 Cube 图标与包含名称/路径的 console warning。全部采用 `object-fit: contain` 和居中显示；保持既有图片框尺寸，仅将耗材图片框底色统一为 `#fff`。卡片原有动画保留，图片 Hover 为 1.02/350ms；减弱动态模式关闭缩放。

统一接入耗材管理的卡片和 6 个抽屉、6 个关联设备的物品详情耗材 Tab。当前首页、AI 助手、提醒和统计中不存在这些耗材的独立图片卡；逐页检查未发现旧耗材照片展示，没有新增模块。

## 验收

验证顺序：后端 `/health` → 后端只读 `/generate` → 已运行的前端 dev 服务 → Edge 浏览器。

- `npm run build`：通过；`npm run lint`：通过。
- 验收脚本 **315 项断言通过**：6 张图、3 组视口布局、20 个页面/抽屉/详情状态。
- 1920×1080、1366×768、390×844 下：侧栏、工具栏、标题、统计、6 个卡片及图片框、底部文字的位置和宽高与修改前基线一致（容差 0.5 CSS px）；页面文字和数字逐字一致。
- 6 张原图本地与 HTTP 响应字节哈希一致；卡片、抽屉、详情 Tab 的实际 URL 与身份对应正确，原始分辨率 1448×1086，fit 为 contain，图片框背景为纯白。
- 慢加载有骨架且卡片高度不变；250ms 淡入；故障图片显示 Cube，不留下破图；console warning 指出耗材名称及路径。
- 搜索、排序保持正常；自定义上传图片不会被覆盖；减弱动态模式无图片缩放；10 件物品此前的高清图仍正常。
- 正常页面图片错误、资源 404 与页面运行异常：**0**。模拟 404 仅用于验证回退，不计入正常页面。
- SQLite 全部表的只读记录哈希与修改前完全一致，API 完整快照一致：没有修改 Demo 数据或数据逻辑。

完整结果：[verification.json](consumable-images/verification.json)。截图：[耗材页面](consumable-images/consumables-1920.png)、[窄屏](consumable-images/consumables-390.png)、[滤芯抽屉](consumable-images/purifier-filter-drawer.png)、[扫地机器人耗材 Tab](consumable-images/robot-consumables-tab.png)。

复现：服务运行后，`node scripts/verify_consumable_images.mjs`。本机修改前布局比较可附加 `--baseline <本地备份目录>`。

## 旧图引用与修改文件

当前 6 种耗材所有图片展示均使用新的 PNG。旧 JPG 路径仍在 SQLite、`backend/seed.py`、`backend/models.py` 默认值、历史提取脚本以及 Mapping 兼容表中。依照“不能删除仍有代码引用的旧资源”，保留旧文件，没有修改这些业务文件；不能宣称整个项目中不存在旧路径。

本次新增：6 张 PNG、`frontend/src/assets/consumableAssets.ts`、`frontend/src/components/ConsumableImage.tsx`、`scripts/verify_consumable_images.mjs`、`docs/references/consumable-image-assets.json`、本验收记录及截图/验证 JSON。

本次修改：`frontend/src/components/ProductImage.tsx`（增加可选已解析 asset 参数）、`frontend/src/pages/Consumables.tsx`、`frontend/src/pages/ItemDetail.tsx`（仅耗材图片引用）、`frontend/src/styles.css`（仅耗材图片白底和 Hover）、`README.md`、`THIRD_PARTY.md`。

修改前备份保留在本机 `backups/` 目录。本次未删除旧图，未改其他物品图，未变更后端和数据库。

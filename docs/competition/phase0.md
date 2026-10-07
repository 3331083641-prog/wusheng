# Phase 0 调研与实施计划

此文件是早期历史计划，不作为 V2.1 功能或测试状态依据。调研溯源已合并到 [开源融合说明](../../OPEN_SOURCE_USAGE.md)；当前架构见 [architecture.md](architecture.md)，测试见 [test_results.md](test_results.md)，实际 Schema 以 [models.py](../../backend/models.py) 为准。

检查日期：2026-10-01（Asia/Shanghai）。初始工作区无工程文件；无需覆盖已有工程。
环境 Node v24.15.0 / npm 11.12.1 / Python 3.12.4 / Git 2.54.0。
阅读全部九张用户设计稿，逐页分析见 DESIGN.md。用户已经授权技术选型与后续实施，不重复询问。

## 源码调研
Warden 63d6032777c64a953d6432c62fb97cc96ed31548：读取 README、LICENSE、src/services/receipt-parser.ts、src/lib/warranty.ts、src/db/schema.ts、src/services/item-reminders.ts。Expo/React Native + Drizzle，本地 ML Kit。学习金额关键词置信度、自然月截断、双期限与提醒协调。手机原生代码不适合直接移植 Web。

HomeInventory 66e9dc6a338fc6287600c1ed28b3f5cea8780da8：读取 README、LICENSE、database.js、routes/maintenance.js、utils/warrantyValidation.js，搜索客户端 QR 和维护结构。React + Express + SQLite，账户/家庭隔离与库存强耦合，保留其工程思想而自行实现轻量数据模型。

HomeAsset 5955a2f58f3b41ca1e828c3aa27fd2aec5f05260：读取 README、app/models.py、app/database.py、app/routers/items.py。FastAPI + SQLAlchemy + SQLite；无登录、附件与关联删除可参考。当前树未发现 LICENSE，README MIT 声明不能代替完整授权文本，不复用其代码。

开发期间使用的研究快照保存在仓库外，仅用于功能调研，不进入交付包。

## 最终架构
React SPA → 同源 /api 代理 → FastAPI → SQLAlchemy SQLite + 本地 uploads。
服务层：LifecycleEngine / consumptionPrediction / RecognitionProvider / ContextBuilder / AIProvider。
OCR：RapidOCR ONNX 中文本地推理 + 中文字段规则；未识别字段留空。视觉识别不伪装已实现，不从文件名猜测。
AI 默认 evidence/rule 模式；可替换本地 Ollama provider，在线 provider 不默认启用。
图表 Recharts，动画 Framer Motion，图标 Lucide，QR qrcode，状态 Zustand。

## 模块边界
借鉴：Warden OCR 候选与双期限；HomeInventory 附件/维护/QR；HomeAsset 无账号本地架构。
直接复用参考项目源代码：无。
复用开源库：React、FastAPI、SQLAlchemy、RapidOCR、pypdf、Recharts、qrcode 等，许可及版本另行记录。
自主开发：生命周期事务与事件图、多图字段融合与证据、设备耗材模型、预测、上下文回答、说明书引用、统一统计与全部 UI。

## 路由树
AppShell（固定 Sidebar + UtilityBar）
- / 首页
- /items 我的物品
- /items/new 添加物品
- /items/:id 档案（基本/说明书/维护/维修/耗材/建议）
- /reminders 提醒中心
- /consumables 耗材管理
- /repairs 维修记录
- /assistant?item=:id AI 助手
- /statistics 数据统计
- * 404

## Schema
普通业务实体 UUID 主键，演示种子使用明确的可读 ID；日期 ISO 日历日；时间 UTC ISO；金钱内部整数分（API 元）；外键级联，文件保留本地。
Item(id,name,brand,model,category,description,purchaseDate,purchasePrice,purchaseChannel,serialNumber,warrantyMonths,warrantyEndDate,returnWindowDays,returnDeadline,status,coverImage,location,createdAt,updatedAt,isDemo)
ItemImage(id,itemId,filePath,type,source)
Document(id,itemId,type,filename,filePath,extractedText,uploadedAt)
LifecycleEvent(id,itemId,type,date,title,description,source,relatedId)；相关事件唯一键，防重复。
MaintenanceRecord(id,itemId,type,date,intervalDays,nextDueDate,description,cost)
RepairRecord(id,itemId,issue,reportDate,status,serviceType,cost,description,completionDate,progress[])
Consumable(id,itemId,name,unit,currentStock,warningStock,leadDays,coverImage)；estimatedDaysLeft/suggestedPurchaseDate 由历史计算，不写死缓存。
ConsumptionRecord(id,consumableId,date,quantityUsed)
RestockRecord(id,consumableId,date,quantity,cost)；真实耗材支出来源。
Reminder(id,itemId,type,title,dueDate,status,priority,relatedId,originalDueDate)；有唯一来源键，延后和完成不被重算覆盖。
RecognitionResult(id,sessionId,field,value,confidence,sourceImage,rawText)；候选全部保存，冲突降低置信度。

## 实际执行顺序及验收
|阶段|实施|验收|
|---|---|---|
|0|环境、源码许可、Git、架构与设计记录|可追溯 commit 和授权边界|
|1|统一组件、九页面、合成 Demo、设计稿照片提取|所有路由、表单/抽屉可操作；不使用截图背景|
|2|SQLite 与 API；替换 UI 数据适配层|CRUD 后页面同步，重启持久|
|3|生命周期、自然月、提醒、维护维修事务|日期、事件、提醒测试；维修统计同步|
|4|真实多图 OCR 与字段证据|照片+票据→人工确认→保存→提醒|
|5|独立 consumptionPrediction|零记录/零消耗/不足库存测试；滤芯 12 天案例|
|6|PDF 本地存档/文本解析/上下文|数据库与说明书引用，无记录明确未知|
|7|微动、路由、图表、减弱动态|桌面与移动基础验证|
|8|单测、UI workflow、README 与参赛材料|/health→/generate→npm run dev→浏览器；三个闭环与局限明确|

全流程不删除大量文件、不读取或输出密钥、不使用付费 API。关键源文件修改前备份到本机项目 `backups/`（Git 忽略）。

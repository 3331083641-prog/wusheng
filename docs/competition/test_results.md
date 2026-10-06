# 验证结果

## 最新发布验收：2026-10-06

图片草稿/建档、PDF 上传与查看/下载/删除、六种耗材关联跳转已接通，保持既有视觉与业务数据。

|检查|结果|证据|
|---|---|---|
|TypeScript/Vite build|通过，2652 modules；最大独立 chunk 约415KB|npm run build|
|ESLint|通过|npm run lint|
|后端单元与集成|50 passed，24.98 秒|backend/tests/test_attachments.py + 既有 engine/workflows|
|浏览器流程|14 passed，83.8 秒|ui-test-results.json、frontend/tests/local-files.spec.ts|
|Demo 初始化|隔离数据库首次启动生成10件合成物品；/health、/generate 均成功|scripts/test_ui.ps1，临时数据目录|
|发布目录保护|原始 data/ 与 backups/ 未触碰；浏览器测试使用项目 tmp/ 下专用数据库|git status 与隔离测试配置|
|真实服务重启|2 张原图、1 份 PDF 刷新及重启后可读，SHA256 一致|local-files/restart-verification.json|
|说明书 AI 引用|本地文本按当前 Item 隔离，返回说明书来源|后端测试与重启检查|
|删除/失败回滚|记录与文件同步；Item 级联；写入/提交错误恢复原文件|test_attachments.py|
|格式与大小|图片 JPG/JPEG/PNG/WebP≤10MB，PDF≤50MB，拒绝伪造内容|后端与浏览器错误流程|
|耗材关联|6 组 Drawer 字段与跳转、Item Tab 同源通过|local-files.spec.ts|
|当前数据|10 Items、6 Consumables、3 Repairs 保留|临时验证档案删除后 snapshot|

具体接口、元数据、修改文件与自动化验证边界见 [本地上传与关联验收](local_file_workflows.md)。浏览器自动化验证原生 filechooser 事件，未人工目视桌面 Windows 文件窗口。此次隔离运行的14组流程均通过，正常路径无新增页面错误；负例返回预期 HTTP 校验错误。Node 显示环境颜色变量警告，Python 测试有一条已有的 Starlette/httpx 弃用警告，均不影响检查结果。

## 初期验收记录（2026-10-01，保留历史）

日期：2026-10-01，Windows / Python 3.12.4 / Node 24.15.0 / Microsoft Edge。

## 实际运行结果
|检查|结果|证据|
|---|---|---|
|后端 /health|status=ok，SQLite，本地 OCR / 证据回答模式|本机 HTTP 实测|
|后端 /generate|耳机保修查询返回档案日期和来源|HTTP + workflow test|
|后端单元 / 集成|26 passed，12.29 秒|backend/tests/，pytest 实际输出|
|TypeScript + Vite 构建|通过，vendor 拆分最大 chunk 约415KB|npm run build|
|ESLint|通过|npm run lint|
|核心浏览器流程|8 passed，56.8 秒，0 flaky|ui-test-results.json|
|响应式|1440×900、1920×1080、1366×768、390×844|docs/references/home-{width}.png|
|九个主要页面|可导航，移动端无横向溢出，未发现 pageerror|UI workflow 与截图|
|路由连续性|侧栏跳转后 window 探针仍保留，证明 SPA 未刷新|workflows.spec.ts|
|Windows PowerShell 启动脚本|实测 health → generate → dev → 打开浏览器；退出清理自己的 Vite 子进程|scripts/start.ps1，Windows PowerShell 5.1|

验证顺序已执行：/health → /generate → npm run dev → 浏览器。数据库最终恢复为10件合成Demo，6种耗材，3条维修；测试自己的临时档案清理，不重置用户数据库。

## 覆盖
- 保修自然月、月末与闰年截断；零保修、跨年退换、维护周期。
- 耗材60天/5单位/1库存=12天；无历史、同日、零消耗、不包含未来记录；库存不足回滚、补货支出与库存变化。
- Reminder 幂等；延后与完成持久，不被读取覆盖。
- Lifecycle purchase/return/use/maintenance/repair/completion/retired；维修顺序限制与跨页年度费用同步。
- 真正 RapidOCR 对两张图片本地推理、字段提取、来源置信度、人工修改、建档、防重复保存、自动提醒。
- UI 编辑、QR PNG 下载、JSON 导出、PDF 上传、维护记录、提醒、耗材抽屉趋势与库存、完整维修流转。
- 物品上下文隔离、说明书来源、缺少记录拒绝编造。
- 错误字段、日期、负价格、无效图片与PDF；空白扫描 PDF 不标记为已解析文本。

## 实际问题与修正
初轮UI测试5/8通过：识别结果置信度导致label名称改变、选择框缺少固定aria标签、测试将/items/new误当详情；维修完成事件原先覆盖报修事件。分别固定标签、排除new路由并保留报修/完成两条事件。一次测试期间格式化触发热重载导致抽屉丢失，最终固定源码后整组重跑通过。小屏横向溢出、上传按钮默认submit、统计入口整页刷新均已修正。

独立视觉检查的七项修复完成：场景照片去除 UI 残留、详情完整首图、可见植物摄影、完整圆环、统计右列密度、搜索焦点、移动导航可访问名称。最终复核 disposition=ship。未拍摄产品的档案显示明确照片空状态。

启动脚本在 Windows PowerShell 5.1 实测发现 UTF-8 无 BOM 与 REST 数组包装差异，已保存 UTF-8 BOM、修正数组读取并复测启动及退出。既有后端服务不被退出脚本停止。

## 局限与未验证范围
1. 26项与8组测试证明当前原型闭环，不证明商业级可靠性或大规模识别精度。
2. 未进行用户操作时间或真实小票大样本准确率评测，不虚构92%等指标。
3. 无文字照片视觉识别、扫描PDF OCR、向量RAG、在线生成模型、后台系统提醒尚未启用。
4. 外部和Ollama provider 仅有可替换适配器，未连接真实模型验证。
5. QR默认本机回环地址，手机需另配可访问的局域网地址。
6. 此初期记录之后，10 件物品与 6 种耗材已升级为用户提供的 1448×1086 PNG；来源与授权单独登记，见 hd_image_upgrade.md / consumable_image_upgrade.md。
7. pytest有1条Starlette/httpx测试适配弃用警告，不影响26项通过。当前无需更改系统依赖。
8. 抽屉与图表为真实组件；统计缺少历史的月份显示0，不能为让图漂亮编造记录。

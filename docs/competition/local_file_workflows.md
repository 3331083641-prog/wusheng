# 本地上传与关联功能验收

日期：2026-10-02。增量修复，沿用现有页面、导航、配色和卡片布局。所有上传只发送回环地址的本机 FastAPI；未调用外部模型或云存储。

## 1—8：图片上传

1. 「选择图片」通过 `inputRef.current?.click()` 触发浏览器原生文件选择请求。大虚线区域及四个图片类型入口同样触发。浏览器测试实际捕获 filechooser 事件并选择本地文件；不绘制伪 Windows 文件窗口。自动化在 Edge headless 运行，未人工目视桌面 Windows 对话框。
2. JPG/JPEG、PNG、WebP；前后端均校验格式、扩展名、MIME、真实图片内容。单张 ≤10MB，最大 2000 万像素。HEIC 暂不支持。
3. multiple，最多 10 张，可多次补选。超过数量或大小会提示并保留已上传图片。
4. 支持 dragenter/dragover/dragleave/drop，拖入反馈沿用现有淡绿样式。
5. Draft 图片真实目录：`data/uploads/drafts/<draftId>\`。`POST /api/drafts` 创建 UUID 会话，`POST /api/drafts/{draftId}/images` 接收多个 files 和 type，原文件按 UUID+原格式后缀保存。预览立即出现文件名、类型、大小和上传状态，Object URL 只用于临时显示，删除与卸载时释放。
6. 确认建档通过 `POST /api/items`，携带 draftSessionId 及可选 recognitionSessionId。一笔事务创建 Item、迁移原图到 `data/images/items/<itemId>\`、创建 ItemImage、计算日期、生成事件和提醒，再跳转详情。草稿图片目录清空；会话留 sealed 标记防止重复建档。不需要假 Item ID。纯照片无文字仍保留原图，可以手动补充并保存；手动模式可以不带图片。
7. ItemImage：`id / itemId / originalFilename / storedFilename / filePath / mimeType / fileSize / type / sha256 / source / createdAt`。文件原字节保存，不转 JPG、不缩小、不二次压缩。API 返回 `/api/images/{id}`；内部相对磁盘路径不返回给前端。
8. 已保存图片刷新与实际前后端重启后仍存在。未保存草稿本轮不提供刷新恢复入口；离开添加页面会尝试清理，浏览器强关遗留草稿超过 24 小时后在下次启动或新建草稿时清理。

图片类型为 `product / receipt / label / manual_image`；兼容旧客户端 package/manual。OCR 根据类型筛选相应字段，始终保留可修改的候选、来源和置信度。没有可读文字返回明确提示；OCR 服务暂不可用也不会丢失上传原图，可以重试或手动确认。

草稿接口：

|方法|路径|用途|
|---|---|---|
|POST|/api/drafts|创建草稿|
|POST|/api/drafts/{id}/images|多文件上传|
|GET|/api/drafts/{id}/images|读取持久化图片列表|
|GET|/api/drafts/{id}/images/{imageId}/file|读取图片|
|PATCH|/api/drafts/{id}/images/{imageId}|修改图片类型|
|DELETE|/api/drafts/{id}/images/{imageId}|删除图片记录和磁盘原文件|
|DELETE|/api/drafts/{id}|取消未保存草稿|
|POST|/api/drafts/{id}/recognize|读取已保存图片，执行本地 RapidOCR|

## 9—16：PDF

9. 上传：`POST /api/items/{itemId}/documents/manual`，multipart 的 file 字段。列表：`GET /api/items/{itemId}/documents`。保留原先 `/items/{id}/documents` 上传兼容接口。
10. 本地目录：`data/documents/manuals/<itemId>\`，磁盘使用 UUID.pdf。先确认 Item 存在，仅接收 .pdf + application/pdf，最大 50MB，并验证真实 PDF 可读取。文件名按 basename 清理，不作为磁盘路径；拒绝无效/加密文件。旧说明书通过增量迁移补充元数据和管理目录；演示 PDF 原位置继续作为自动化测试 fixture。
11. Document：`id / itemId / type / originalFilename / storedFilename / filePath / mimeType / fileSize / sha256 / pageCount / extractedText / uploadedAt / updatedAt`；保留 filename 字段兼容旧档案。type=manual；API 的 filePath 为 `/api/documents/{id}/file`。同一 Item 可有多份同名说明书，每份 UUID 各自独立。
12. 查看：该文件接口返回 inline application/pdf，在新页用浏览器原生 PDF Viewer 打开。
13. 下载：`GET /api/documents/{id}/file?download=true` 返回 attachment，Content-Disposition 使用 originalFilename，保存原文件字节。
14. 删除：用户二次确认后调用 `DELETE /api/documents/{id}`，记录及真实 PDF 同步删除，UI 刷新。文件先暂存删除状态，数据库提交失败时恢复原文件；上传/绑定失败同样回滚文件和记录。`DELETE /api/images/{id}` 同步删除图片。删除 Item 会级联清理图片、PDF、维护、维修、耗材、消耗/补货、提醒和生命周期记录，静态 Demo assets 不删除。删除提示已同步为实际行为。
15. 使用已有开源 pypdf，提取文字附页号，保存页数和文本；扫描 PDF 或单页提取异常仍存档，可直接查看，显示“扫描型 PDF / 暂无可提取文字”。扫描 PDF 图片 OCR 暂未启用。
16. ContextBuilder 查询当前 Item 的 Document、维护、维修与耗材。规则助手对电池/清洁等问题匹配当前说明书片段，回答“依据已上传说明书”并列出来源；未上传说明书明确说明未找到，当前资料无相关文字明确未知。没有增加外部生成服务，也没有把关键词检索称为向量 RAG。

前端通过 Vite `/api` 代理访问本地 API；后端附件路由同时提供带 `/api` 和不带前缀的地址，兼容已有客户端。所有页面不暴露 D 盘绝对路径。

## 17—18：耗材关联

Consumable 继续使用真实外键 itemId→Item.id，新增 createdAt/updatedAt；estimatedDaysLeft/suggestedPurchaseDate 由同一数据库消费记录和当天日期计算，避免存储过期预测。Drawer 明确显示耗材名称、关联物品、当前库存、预计可用、建议购买；关联物品从统一 snapshot 查找，可点击关闭 Drawer 后进入 `/items/{itemId}`。详情耗材 Tab 读取相同数据库关系，未写死一套重复数据。

|耗材|关联 Item|Item ID|
|---|---|---|
|空气净化器滤芯|空气净化器|purifier|
|洗衣液|海尔滚筒洗衣机|washer|
|打印机墨盒|惠普打印机|printer|
|咖啡胶囊|德龙咖啡机|coffee|
|电动牙刷刷头|飞利浦电动牙刷|toothbrush|
|扫地机器人滤网|小米扫地机器人|robot|

## 19：本轮文件

后端：backend/attachments.py（新增）、storage.py（新增）、database.py、models.py、schemas.py、serializers.py、main.py、recognition.py、providers.py；backend/tests/test_attachments.py（新增）、conftest.py。

前端：components/ImageUploader.tsx、DocumentCard.tsx；pages/AddItem.tsx、ItemDetail.tsx、Consumables.tsx；types.ts、styles.css；tests/local-files.spec.ts（新增）、workflows.spec.ts。另加 index.html 与 public/favicon.svg，消除原先 favicon.ico 404。

工程与文档：.gitignore 忽略用户 images/documents；scripts/backup.py 备份新附件目录；scripts/verify_local_file_restart.mjs（新增）；README.md；本文件、test_results.md、local-files/ 下报告/截图、ui-test-results.json 和测试生成的 docs/references 截图。之前高清图片替换的未提交更改原样保留。

修改前备份：`本机 backups/ 目录`，含 SQLite backup 快照，不覆盖既有数据。

## 20—24：验收

- 所有关键按钮排查：没有空 onClick、TODO、假 Toast、console.log/alert 占位操作；disabled 仅用于无图片、处理中、校验或状态限制。QR PNG 与 JSON 档案导出通过原有 UI workflow 验证。
- 前端 TypeScript/Vite build、ESLint 通过。
- 后端 50 项单元/集成测试通过，覆盖旧库增量迁移、文件类型/大小、Document 创建/删除/归属、ItemImage 原字节创建/绑定、六种耗材关系、真实 OCR、扫描 PDF、文件事务回滚、磁盘错误、过期草稿、级联清理及新 lifespan 重读磁盘。
- 浏览器 14 组 workflow 最终结果见 ui-test-results.json；新增 6 组覆盖原生 filechooser 事件、多图/拖拽/类型入口、无文字照片 OCR→保存、PDF 查看/下载/删除、六种耗材跳转、错误提示及手动无图建档。
- 实际停止并重新启动 uvicorn 和 Vite，浏览器上传建立的 2 张图片及 1 份 PDF 均仍存在，SHA256 原字节一致，说明书 AI 引用通过，临时档案及附件最终清理。证据：[重启报告](local-files/restart-verification.json) 与 [重启后截图](local-files/after-restart.png)。
- 正常工作流未发现 pageerror、控制台错误和附件路径错误；原先 favicon 404 已修复。无效文件验证会返回预期 415/413/422 并在界面提示；这种测试响应不属于正常页面故障。pytest 仍有一条既有 Starlette/httpx 弃用警告。
- 数据库最终保留原有 10 件物品、6 种耗材、3 条维修；未重置库、未修改名称、价格、库存或历史记录。日期跨过午夜后耗材预测按数据库动态计算，UI 测试随之从固定 12 天改为核对实时值。

## 运行与复核

先启动服务，再运行：

```powershell
cd <project-root>
`.venv\Scripts\python.exe -m pytest backend/tests -q`
cd frontend
npm run build
npm run lint
npm run test:ui
```

实际重启检查：运行 `node scripts/verify_local_file_restart.mjs prepare`，按 /health→/generate→npm run dev 顺序重新启动服务，再运行 `node scripts/verify_local_file_restart.mjs verify`。脚本只创建、清理自己的合成档案，不重置用户数据库。备份脚本已同时复制 uploads/images/documents。

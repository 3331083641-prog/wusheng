# 功能终版验收（2026-10-07）

仓库：https://github.com/3331083641-prog/wusheng ，Public / main。此次验证的业务代码提交为 `0ccc9ba6b3654ffe9d6e9a123b52b1066ebdae23`，后续提交仅更新验收文档和 CI 徽章。

## 已接通的工作流

| 范围 | 实现及边界 | 主要源码 |
|---|---|---|
| 一物一码 | 默认本机模式不生成手机不可用二维码；LAN 动态私人 IPv4、单端口生产 SPA、安全随机令牌、只读投影、序列号掩码、稳定令牌/重生成/撤销/PNG。管理 API 限本机，不改防火墙 | backend/sharing.py、ShareItem.tsx、ShareQR.tsx、scripts/start_lan.ps1 |
| 凭证 | product / receipt / label / manual_image / invoice / package / warranty_card / other；后置原图上传、分类、删除；封面回退；字段候选/当前值/原文/置信度/图片/人工修改 | attachments.py、EvidenceCenter.tsx |
| PDF | 文本层 pypdf，扫描页 pypdfium2 + RapidOCR；用户触发，text_ready / needs_ocr / ocr_processing / ocr_ready / ocr_failed；失败保留原件 | storage.py、manual_ocr.py、DocumentCard.tsx |
| 本机 AI | evidence 默认；可选 Ollama、OpenAI-compatible；HTTP 回环限定，相关有限证据、当前 Item 隔离、来源列表、危险维修拒绝；故障回退 | ai_engine.py、context.py、AIChat.tsx |
| 售后包 | ZIP 含 JSON 档案、维修维护生命周期、原图、可选说明书、中文摘要 PDF、SHA256 manifest；不含磁盘绝对路径 | evidence_pack.py |
| 纠错 | 维护编辑/删除及重算；消耗和补货历史/撤销，拒绝负库存；维修费用/说明/方式更正，状态严格顺序 | corrections.py、RecordTools.tsx |
| 提醒 | 全部/单条待处理 ICS；用户主动授权浏览器通知。关闭应用后依赖系统日历 | calendar_export.py、NotificationOptIn.tsx |
| 备份 | 数据库一致快照与引用附件 ZIP、路径/大小/版本/SQLite/哈希校验、恢复前备份、失败回滚。单进程运行；恢复保留旧附件 | backup_restore.py、LocalData.tsx |
| 预测 | low/medium/high 数据质量、有效记录数/观察周期/波动依据、经验区间；不宣称统计置信区间 | consumptionPrediction.py |
| PWA | manifest 与静态 JS/CSS Service Worker，在 localhost 生产页实际注册；不缓存档案/PDF。拍照入口通过原生 filechooser + capture=environment | main.tsx、manifest.webmanifest、sw.js、ImageUploader.tsx |

## 实际验证

- 本地与冷克隆后端均 71 passed；浏览器均完整 19 passed；lint/build 通过；10 件物品与 6 件耗材图片检查通过。
- Linux Actions 完整通过后端 71 项、lint/build：[CI](https://github.com/3331083641-prog/wusheng/actions/runs/37573023368)。最终提交状态以 README 的实时徽章为准。
- `D:\wusheng-v2-release-test` 从 GitHub 重克隆，依 README 的 setup/start/start_lan 重新安装和启动；Demo/EvidenceProvider、只读 LAN、QR PNG 解码、PDF、售后、备份、耗材、提醒均经过真实接口与浏览器测试。
- 两张原图、一份 PDF 在真实服务重启及浏览器刷新后仍可读取，SHA256 一致；见 local-files/restart-verification.json。
- 本机已有 Qwen3-VL-4B-Instruct 两次真实证据问答通过；未下载或提交权重；OpenAI-compatible 用模拟协议验证，未连接实际兼容服务。模型验证见 local_model_validation.json。
- OCR 基准实际执行，3 张合成英文标签、15 字段、14 完全匹配；precision/recall/F1=0.9333；不是真实票据大样本准确率。
- 对发布文件及全部可达 Git 文本 blob 执行基础密钥/本机用户路径扫描，未发现密钥或本机用户目录；未提交运行数据库、PDF、小票、模型权重或大于 10MB 的文件。第三方许可原文保留，无新增直接 GPL/AGPL 组件；依赖许可与素材边界见 THIRD_PARTY.md。
- 原项目 14 张既有业务表与修改前备份一致；测试只写隔离合成数据。未强推、未重写 Git 历史。

## 未完成与问题记录

真实手机扫码/相机、HTTPS/PWA 实机安装、中文复杂票据大样本评测、生成模型大样本质量评测、无文字物品视觉识别、应用关闭后的后台通知未完成。普通 LAN HTTP 不承诺 PWA 可安装。扫描 OCR 最多50页，不提供实时精确百分比；大任务会占用单进程档案操作门控。

首轮 CI 的测试目录父目录缺失已修复；冷克隆首轮 Windows Node worker 以 native code 3221226505 异常退出，完整重跑19组通过，根因未确认。保留这些结果，不伪称首轮全绿或物理手机测试通过。Starlette/httpx 有一条已有测试适配弃用警告，npm 安装有锁定 ESLint 版本弃用提示，npm audit 为0漏洞。

## 手机人工验收

1. 电脑在仓库根目录运行 `powershell -ExecutionPolicy Bypass -File .\scripts\start_lan.ps1`。
2. 电脑与手机连接同一私人 Wi-Fi。
3. 手机先打开脚本动态输出的 `http://<电脑LAN-IP>:8000`，确认网页可到达；管理数据仍限电脑本机。
4. 在电脑 `http://127.0.0.1:8000` 打开某件物品。
5. 选择“生成二维码”，确认局域网模式，点击“生成只读二维码”。
6. 手机扫码，进入 `/share/<token>`，应可查看、不能修改。
7. 在电脑撤销或重新生成；旧码应失效。若不能打开，先核对私人网络防火墙放行，再检查两端 Wi-Fi、访客/AP 隔离和选中的 LAN 适配器地址；脚本不替你修改系统。

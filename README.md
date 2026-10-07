# 物生 Wusheng

**AI 驱动的家庭物品全生命周期智能管理平台**

参赛方向：2026 第八届全球校园人工智能算法精英大赛 AIC「AI+开源」算法主题赛 · 开源赋能的 AI 应用创新 / 日常生活。团队名称：物生智联。方向与开源资源披露要求参照[组委会赛事通知](https://www.aicomp.cn/notice/notice-3/4890.html)；技术报告及具体提交规则以官网通知附件为准。

物生把家庭物品从购买、退换、使用、维护、保修、维修、耗材补给到淘汰的过程放进一份连续档案。库存软件回答“家里有什么”；物生关注“一件物品进入生活后发生了什么，以及接下来要照顾什么”。

## 要解决的问题

购买凭证容易丢，保修期限容易忘，说明书散落，耗材更换和维护常被遗漏，维修记录难以和物品对应。物生使用本地档案、生命周期规则、OCR 辅助建档和设备耗材关系，把这些零散信息重新连起来。

## 核心功能

- 多张物品照片、小票、铭牌及包装图片辅助建档；本地 OCR 提供可编辑的字段候选和来源信息。
- 生命周期档案、退换与保修期限、维护提醒、维修进度和费用记录。
- 凭证中心、建档后资料补充、字段级来源追溯及人工修改标记。
- PDF 说明书保存、查看、下载、删除；文本提取与用户触发的扫描件本地 OCR。
- 售后证据 ZIP、中文 PDF 摘要、附件 SHA256 manifest。
- 设备与耗材关联、库存记录、历史消耗趋势和补给日期估算。
- 面向单件物品的助手上下文，可读取本地说明书、维修、维护及耗材记录。
- 随机令牌保护的局域网只读二维码、撤销与重生成，支持 JSON 档案导出。
- 维护编辑/删除、耗材消耗与补货撤销、维修资料纠正。
- ICS 日历导出、主动授权的浏览器通知、完整本地备份与校验恢复。
- Local First：数据库、照片、票据和 PDF 默认保存在运行本机；没有账号、会员或云同步。

## 自主实现与创新边界

1. **Item Lifecycle Engine**：把购买、退换、使用、维护、保修、维修与淘汰连成可追溯事件，并同步计算期限和提醒。
2. **Device–Consumable 关系模型**：耗材通过 `relatedItemId` 绑定设备，详情页和耗材管理共同读取这一关系。
3. **消耗趋势估算**：结合库存和历史消耗观察窗口估算可用天数与建议采购日；没有足够历史时不伪造预测。
4. **多模态辅助建档**：本地 OCR 处理图片文字、按图片类型关联候选字段并融合冲突，候选始终由用户确认。
5. **本地说明书上下文**：从 PDF 文本提取与当前物品相关的段落，交给 Item-specific ContextBuilder 和本地证据助手。
6. **Local First 架构**：SQLite 与附件文件共同保存在本机，通过本地 API 管理；默认不调用外部模型或服务。
7. **Field-level Evidence Provenance**：逐字段保留候选、来源图、OCR 原文、启发式置信度与人工修改状态。
8. **售后证据与只读分享**：可核验附件哈希、汇总凭证及维修维护记录，用可撤销令牌分享精简档案。

规则、边界和技术细节见[创新说明](docs/competition/innovation.md)与[架构说明](docs/competition/architecture.md)。Warden 和 HomeInventory 仅用于产品功能与交互思路参考，未直接复制源代码；本项目没有把第三方库能力宣称为自研算法。完整使用清单见 [THIRD_PARTY.md](THIRD_PARTY.md)。

## 页面截图

以下截图来自 1440 像素宽的本地运行界面。

| 首页 | 我的物品 |
|---|---|
| ![首页](docs/references/home-1440.png) | ![我的物品](docs/references/items-1440.png) |

| 添加物品 | 物品详情 |
|---|---|
| ![添加物品](docs/references/add-1440.png) | ![物品详情](docs/references/detail-1440.png) |

| 耗材管理 | AI 助手 |
|---|---|
| ![耗材管理](docs/references/consumables-1440.png) | ![AI 助手](docs/references/assistant-1440.png) |

## 技术架构

| 层 | 技术 |
|---|---|
| 前端 | React 19、TypeScript、Vite、React Router、Zustand、Framer Motion、Lucide、Recharts、qrcode |
| 后端 | Python 3.12、FastAPI、Uvicorn、SQLAlchemy、SQLite |
| 识别与文件 | RapidOCR ONNX Runtime、pypdf、pypdfium2/PDFium、Pillow、ReportLab |
| AI | 默认本地证据规则；可选回环 Ollama / OpenAI-compatible，检索当前物品证据并保留来源，失败回退 |
| 存储 | SQLite 和 `data/` 本地文件目录；没有外部云存储 |

## 项目结构

```text
frontend/                 React/Vite 前端、正式图片资源、UI 测试
backend/                  FastAPI、SQLite Schema、生命周期和识别逻辑、pytest
data/                     本机运行数据；数据库和用户上传内容不进入 Git
docs/competition/         架构、创新边界、演示脚本与验收记录
docs/references/          README 截图、合成 Demo 凭证和素材登记
scripts/                  Windows 安装/启动、备份及资源校验工具
LICENSE                   项目自主源码和文档的 MIT 许可
LICENSES/                 第三方库、OCR 模型与参考项目的许可记录
THIRD_PARTY.md            第三方资源、版本、许可及自主开发边界
AI_USAGE.md               生成式 AI 和 Agent 辅助使用披露
```

## 快速开始（Windows）

需要 Windows 10/11、Python 3.12、Node.js 20 或更新的 LTS 版本、npm。首次安装需要网络；安装后可以在本机离线运行，RapidOCR 模型随 Python 依赖安装。默认服务只监听 `127.0.0.1`。

克隆并安装锁定依赖：

```powershell
git clone https://github.com/3331083641-prog/wusheng.git
cd wusheng
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

启动并自动检查后端健康状态、档案问答、前端服务，再打开浏览器：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

访问 [物生首页](http://127.0.0.1:5173)，API 文档位于 [本机 OpenAPI](http://127.0.0.1:8000/docs)。脚本只停止自己启动的进程；若相同端口已有其他程序，脚本会报告并退出，不会终止其他程序。

也可分开运行服务：

```powershell
cd wusheng
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements-lock.txt
cd .\frontend
npm ci
```

终端一（后端）：

```powershell
cd wusheng
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

终端二（前端）：

```powershell
cd wusheng\frontend
npm run dev
```

首次启动会在 `data/` 创建本地 SQLite 数据库、生成 10 件合成 Demo 档案，并生成标明为 Demo 的示例护理 PDF。之后启动不会覆盖现有档案。仓库不包含数据库或真实上传文件。

## AI 与识别的实际边界

多图建档使用本地 RapidOCR 中文 ONNX，再经过字段规则解析、候选融合和用户确认；没有文字的图片仍可保存并手动填写。字段置信度是启发式分值，不代表基准数据集上的识别准确率。当前版本不包含纯图像视觉品牌识别。

物品助手默认读取当前 Item、维护、维修、耗材和说明书可提取文字，回答来源是本地档案证据。没有本地说明书或可用证据时会明确提示。可选本机模型已接入 `/generate`，使用有界关键词检索与证据约束 Prompt；协议、隔离和回退有模拟服务测试。本次未安装大型模型，不能把模拟测试当作实际模型质量验证；基本功能不依赖 AI API。

PDF 文本层由 pypdf 提取；扫描件使用 pypdfium2 + RapidOCR，最多 50 页，失败仍保留原文件。耗材预测显示数据质量与经验预测区间；该区间不是统计置信区间或厂家寿命保证。

## 一物一码与局域网分享

默认本机模式不生成声称手机可用的二维码。明确开启分享：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_lan.ps1
# 默认端口被占用时可指定 -Port 8001
```

脚本构建前端，由 FastAPI 单端口托管 SPA，监听本机所有 IPv4 网络接口，不修改防火墙。电脑使用脚本显示的回环地址管理，手机通过 `/share/<token>` 查看只读档案。管理 API 限回环访问；分享隐藏完整序列号、内部路径、凭证和 PDF 正文。多网卡时可在 Drawer 选择地址。

同一物品保持有效随机令牌，重新生成或撤销后旧令牌立即失效。服务关闭后不可访问；IP 改变后需重新下载二维码。手机实机步骤：电脑运行脚本 → 手机同一 Wi-Fi → 手机先打开脚本显示的 LAN 地址 → 电脑打开物品生成二维码 → 手机扫码。失败时核对私人网络防火墙、同一 Wi-Fi、访客网络隔离和网卡地址。自动化验证不等于手机实机验证。

## 可追溯建档与凭证中心

资料类型包括物品照片、小票、发票、包装盒、铭牌、保修卡、说明书照片和其他资料。建档后仍可添加、分类、查看与删除。识别依据逐字段显示候选、当前值、来源图、OCR 原文及分值；人工修改明确标注，删除来源图片后仍标明来源已删除。

## 可选本地模型

在启动服务前设置环境变量；不自动下载模型：

```powershell
$env:WUSHENG_AI_PROVIDER = 'ollama'
$env:WUSHENG_OLLAMA_URL = 'http://127.0.0.1:11434'
$env:WUSHENG_OLLAMA_MODEL = '<本机已安装的模型名称>'
```

默认 `evidence`。另支持 `openai-compatible`，配置 `WUSHENG_AI_BASE_URL`、`WUSHENG_AI_MODEL`、`WUSHENG_AI_API_KEY`，只允许回环本机服务。不会自动发送档案到外部服务。模型缺失、不可访问或调用失败会回退；`/health` 返回 configuredProvider、activeProvider、fallbackReason。无相关证据或涉及危险维修时使用规则边界回答，不让模型猜测。来源代表输入证据，不能保证生成答案无幻觉，用户仍需核对。

## 扫描说明书、售后证据包与备份

扫描 PDF 先保存，再点击“本地识别文本”；状态为 needs_ocr、ocr_processing、ocr_ready、ocr_failed，文本 PDF 为 text_ready。OCR 有页数和像素上限，原文件保留。

售后 ZIP 包含中文 PDF 摘要、档案 JSON、维护维修资料、原始图片及哈希清单，说明书可选。材料来自用户档案，售后政策以厂家/商家为准；不包含绝对磁盘路径。

统计页可导出数据库及数据库引用的附件。恢复检查 ZIP 路径、大小、Schema、SQLite 完整性与 SHA256，自动在 `data/backups/` 保存恢复前备份；失败回滚。备份上限 300MB，售后附件上限 250MB。恢复不会主动删除旧附件，保留旧文件以便从恢复前备份找回。请只恢复可信的本人备份。服务按单进程协调档案操作，不支持多 worker。

## 提醒、手机与 PWA

提醒中心支持单条/全部待处理提醒 ICS 导出；用户主动点击才请求通知权限。关闭浏览器后不能通知，请使用系统日历。手机“拍照添加”请求后置相机，普通选择图片仍支持相册，实际行为依浏览器而定。

生产模式提供 manifest 和 Service Worker，仅缓存静态 JS/CSS，不缓存档案 API 或用户附件。安装需要支持 PWA 的浏览器和安全上下文：localhost 可用，普通 LAN HTTP 通常不能安装。HTTPS 部署、真实手机安装测试未完成；PWA 不把数据库移到手机，不提供离线数据库管理。

## OCR 基准与 Known Limitations

运行 `python scripts/benchmark_ocr.py` 可生成 3 张合成英文标签图片并执行真实 OCR，结果见[基准报告](docs/competition/ocr_benchmark.md)。15 个字段的冒烟基准不能推断真实家庭收据准确率。无文字视觉识别、中文/复杂票据大样本评测、LLM 大样本质量评测和手机实机验证均未完成。OCR、期限、耗材估算和生成回答仍需用户核对。

## Demo 数据与图片

已用本机原先安装的 `qwen3-vl:4b-instruct-q4_K_M` 完成两次真实 `/generate` 验证：保修日期查询与说明书清洁建议均返回对应来源，见[实际模型验证](docs/competition/local_model_validation.json)。仅测试文本证据问答，没有启用该模型的视觉输入，也未将权重放入仓库。可配置已有模型后运行 `python scripts/verify_local_model.py` 复核。

种子数据由 `backend/seed.py` 生成，内容为合成示例；演示凭证和护理 PDF 同样是合成资料，不是真实发票或品牌官方手册。数据库已有用户数据时不会自动重置。

项目使用的物品图、耗材图、Logo 和植物素材由用户提供，并说明为 ChatGPT 生成；图片与源代码分别处理许可。产品展示图为本地静态 PNG，业务上传照片和 PDF 只保存在运行本机。详情见 [图片来源登记](docs/references/hd-image-assets.json)、[耗材图片登记](docs/references/consumable-image-assets.json) 和 [THIRD_PARTY.md](THIRD_PARTY.md)。

## 检查与测试

```powershell
cd wusheng
.\.venv\Scripts\python.exe -m pytest backend/tests -q
cd .\frontend
npm run build
npm run lint
cd ..
powershell -ExecutionPolicy Bypass -File .\scripts\test_ui.ps1
```

`scripts/test_ui.ps1` 使用隔离 SQLite Demo 数据，在空闲测试端口启动后端和前端，验证 `/health`、`/generate` 后运行 Playwright，并在测试通过后只清理本次生成的测试目录；失败时保留隔离数据和日志供排查。需要本机 Microsoft Edge。也可在手动启动默认前后端服务后于 `frontend/` 执行 `npm test`。Python 测试使用隔离的 SQLite 临时数据库。详细限制与验证记录见[测试报告](docs/competition/test_results.md)。

## 隐私与本地数据

应用数据默认位于 `data/`：`wusheng.db`、`images/items/`、`documents/manuals/` 与 `uploads/drafts/`。运行时数据库、照片、票据、PDF、日志和备份均被 `.gitignore` 排除，不提交到公共仓库。用户自行备份数据库和附件；`python scripts/backup.py` 可创建本机备份。上传文件默认不会发送至外部云端或外部 AI Provider。

如需将运行目录移到其他位置，可在启动服务前设置 `WUSHENG_DATA_DIR`；可通过 `WUSHENG_DB_URL` 指定 SQLite 数据库 URL。仓库提供 `.env.example` 作为配置说明，应用不会自动加载 `.env` 文件。

## 开源与竞赛资料

- [项目源码许可](LICENSE)：MIT，仅涵盖本项目自主源码和文档，不自动覆盖第三方组件、模型、商标或用户提供的图像。
- [第三方资源与许可清单](THIRD_PARTY.md)
- [生成式 AI 与 Agent 使用披露](AI_USAGE.md)
- [贡献与本地验证说明](CONTRIBUTING.md)
- [发布整理记录](docs/RELEASE_CLEANUP.md)
- [参赛创新边界](docs/competition/innovation.md)

仓库披露第三方依赖、模型和素材来源，并说明 AI 辅助开发和团队自主实现边界。报名状态、成员权属确认与正式材料提交由参赛团队完成；本项目不宣称获奖或已有上游贡献被接纳。

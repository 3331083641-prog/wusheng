# 物生 Wusheng

**AI 驱动的家庭物品全生命周期智能管理平台**

参赛方向：2026 第八届全球校园人工智能算法精英大赛 AIC「AI+开源」算法主题赛 · 开源赋能的 AI 应用创新 / 日常生活。团队名称：物生智联。

物生把家庭物品从购买、退换、使用、维护、保修、维修、耗材补给到淘汰的过程放进一份连续档案。库存软件回答“家里有什么”；物生关注“一件物品进入生活后发生了什么，以及接下来要照顾什么”。

## 要解决的问题

购买凭证容易丢，保修期限容易忘，说明书散落，耗材更换和维护常被遗漏，维修记录难以和物品对应。物生使用本地档案、生命周期规则、OCR 辅助建档和设备耗材关系，把这些零散信息重新连起来。

## 核心功能

- 多张物品照片、小票、铭牌及包装图片辅助建档；本地 OCR 提供可编辑的字段候选和来源信息。
- 生命周期档案、退换与保修期限、维护提醒、维修进度和费用记录。
- PDF 说明书本地保存、查看、下载、删除与文本提取。
- 设备与耗材关联、库存记录、历史消耗趋势和补给日期估算。
- 面向单件物品的助手上下文，可读取本地说明书、维修、维护及耗材记录。
- 每件物品生成 QR 入口，支持结构化档案导出和统计视图。
- Local First：数据库、照片、票据和 PDF 默认保存在运行本机；没有账号、会员或云同步。

## 自主实现与创新边界

1. **Item Lifecycle Engine**：把购买、退换、使用、维护、保修、维修与淘汰连成可追溯事件，并同步计算期限和提醒。
2. **Device–Consumable 关系模型**：耗材通过 `relatedItemId` 绑定设备，详情页和耗材管理共同读取这一关系。
3. **消耗趋势估算**：结合库存和历史消耗观察窗口估算可用天数与建议采购日；没有足够历史时不伪造预测。
4. **多模态辅助建档**：本地 OCR 处理图片文字、按图片类型关联候选字段并融合冲突，候选始终由用户确认。
5. **本地说明书上下文**：从 PDF 文本提取与当前物品相关的段落，交给 Item-specific ContextBuilder 和本地证据助手。
6. **Local First 架构**：SQLite 与附件文件共同保存在本机，通过本地 API 管理；默认不调用外部模型或服务。

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
| 识别与文件 | RapidOCR ONNX Runtime、本地图片校验、pypdf 文本提取、Pillow |
| AI | 默认启用本地规则与档案证据回答；OpenAI-compatible/Ollama 适配器未连接模型，默认不启用 |
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

物品助手默认读取当前 Item、维护、维修、耗材和说明书可提取文字，回答来源是本地档案证据。没有本地说明书或可用证据时会明确提示。Ollama 与 OpenAI-compatible Provider 仅有可替换适配接口，没有默认连接或实际生成模型验证；基本管理功能不依赖 AI API。

PDF 可提取文本层并进行关键词检索；扫描件仍可保存和查看，但当前不执行扫描 PDF OCR。耗材建议根据本地历史记录估算，不是厂商寿命保证。二维码默认是本机地址，外部设备扫码需要将应用配置到可访问的局域网地址。

## Demo 数据与图片

种子数据由 `backend/seed.py` 生成，内容为合成示例；演示凭证和护理 PDF 同样是合成资料，不是真实发票或品牌官方手册。数据库已有用户数据时不会自动重置。

项目使用的物品图、耗材图、Logo 和植物素材由用户提供，并说明为 ChatGPT 生成；图片与源代码分别处理许可。产品展示图为本地静态 PNG，业务上传照片和 PDF 只保存在运行本机。详情见 [图片来源登记](docs/references/hd-image-assets.json)、[耗材图片登记](docs/references/consumable-image-assets.json) 和 [THIRD_PARTY.md](THIRD_PARTY.md)。

## 检查与测试

```powershell
cd wusheng
.\.venv\Scripts\python.exe -m pytest backend/tests -q
cd .\frontend
npm run build
npm run lint
npm test
```

`npm test` 运行 Playwright UI 工作流，需要本机 Microsoft Edge 和正在运行的前后端服务（默认端口分别是 5173、8000）。浏览器测试使用单独创建和清理的测试物品；不要把私人数据库路径传给 `WUSHENG_DATA_DIR`。Python 测试使用隔离的 SQLite 临时数据库。详细限制与验证记录见[测试报告](docs/competition/test_results.md)。

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

项目可作为代码与演示成果链接供评审查看；参赛报名、材料提交和主办方规则核验由参赛团队另行完成。

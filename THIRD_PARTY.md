# 第三方资源、许可与自主开发边界

核验日期：2026-10-07。依赖版本以根目录及 `frontend/package-lock.json`、`backend/requirements-lock.txt` 为准；传递依赖的版本及许可证元数据另见 [`LICENSES/dependency_inventory.json`](LICENSES/dependency_inventory.json)，第三方许可证原文收录在 [`LICENSES/`](LICENSES/)。

| 资源 | 类型 | 版本 / Commit | 来源 | License | 实际用途 | 自主修改 / 开发边界 | 合规状态 |
|---|---|---|---|---|---|---|---|
| React / React DOM | 前端框架 | 19.3.0 | [react.dev](https://react.dev/) | MIT | UI 渲染 | 页面、交互和应用状态由项目编写 | 许可文本已登记 |
| TypeScript | 语言 / 编译器 | 5.9.3 | [typescriptlang.org](https://www.typescriptlang.org/) | Apache-2.0 | 类型检查与构建 | 项目业务代码由团队编写 | 许可文本已登记 |
| Vite / React plugin | 构建工具 | 7.3.6 / 5.2.0 | [vite.dev](https://vite.dev/) | MIT | 本地开发服务器和前端构建 | 使用默认工具链并配置本地 API 代理 | 许可文本已登记 |
| React Router | 前端路由 | 7.18.4 | [reactrouter.com](https://reactrouter.com/) | MIT | 页面路由 | 页面结构由项目编写 | 许可文本已登记 |
| Zustand | 状态库 | 5.0.15 | [github.com/pmndrs/zustand](https://github.com/pmndrs/zustand) | MIT | 前端数据状态 | 数据流和业务逻辑由项目编写 | 许可文本已登记 |
| Framer Motion | 动画库 | 12.43.0 | [motion.dev](https://motion.dev/) | MIT | 轻量界面动画 | 动画参数由项目配置 | 许可文本已登记 |
| Lucide React | 图标库 | 0.468.0 | [lucide.dev](https://lucide.dev/) | ISC | 界面图标 | 按需使用图标组件 | 许可文本已登记 |
| Recharts | 图表库 | 3.10.1 | [recharts.org](https://recharts.org/) | MIT | 统计图表渲染 | 指标定义与数据聚合由项目编写 | 许可文本已登记 |
| node-qrcode | QR 生成库 | 1.5.4 | [github.com/soldair/node-qrcode](https://github.com/soldair/node-qrcode) | MIT | 生成物品档案二维码 | 二维码内容与下载流程由项目编写 | 许可文本已登记 |
| Ollama / Qwen3-VL-4B-Instruct | 可选本机服务 / 生成模型 | 本机实测版本与模型 digest 见 local_model_validation.json；Ollama tag qwen3-vl:4b-instruct-q4_K_M | [Ollama](https://github.com/ollama/ollama) / [Qwen 官方模型卡](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct) | MIT / Apache-2.0 | 可选当前物品文本证据问答；本机已安装模型的两问题冒烟验证 | 不自研或训练模型，不启用视觉输入，不分发权重，不自动下载；检索、上下文限制、回退由项目实现 | 官方模型卡和本机模型许可核对；许可原文见 LICENSES/qwen3-vl-4b-instruct.txt |
| FastAPI | Python Web 框架 | 0.141.1 | [fastapi.tiangolo.com](https://fastapi.tiangolo.com/) | MIT | 本地 REST API | 路由、校验与领域逻辑由项目编写 | 许可文本已登记 |
| Uvicorn | ASGI 服务器 | 0.54.0 | [uvicorn.org](https://www.uvicorn.org/) | BSD-3-Clause | 本地运行 FastAPI | 仅使用服务器能力 | 许可文本已登记 |
| SQLAlchemy / SQLite | ORM / 数据库 | 2.1.1 / Python 标准库 | [sqlalchemy.org](https://www.sqlalchemy.org/) / [sqlite.org](https://www.sqlite.org/) | MIT / Public Domain | 本地关系数据存储 | Schema、查询和事务由项目编写；SQLite 随 Python 使用 | 许可文本已登记 |
| Pydantic / python-multipart | 数据校验 / 表单解析 | 2.13.5 / 0.0.32 | [pydantic.dev](https://docs.pydantic.dev/) / [python-multipart](https://github.com/Kludex/python-multipart) | MIT / Apache-2.0 | API Schema、multipart 图片和 PDF 上传 | 输入 Schema 与大小/格式校验由项目编写 | 许可文本已登记 |
| httpx | HTTP 客户端 | 0.28.1 | [python-httpx.org](https://www.python-httpx.org/) | BSD-3-Clause | 可选 Ollama / OpenAI-compatible Provider 适配器 | 默认助手不调用网络；可选本机模型已接入并有模拟协议测试；使用本机已装 Qwen3-VL-4B-Instruct 实测两个问题；未做大样本质量评测 | 许可文本已登记 |
| ReportLab / pytest | PDF 生成 / 测试工具 | 4.4.10 / 9.1.1 | [reportlab.com](https://www.reportlab.com/) / [pytest.org](https://pytest.org/) | BSD / MIT | 本地合成 Demo 护理 PDF、售后摘要与物品档案 PDF、后端测试 | 档案排版、Demo 文档和测试断言由项目编写；复用 STSong-Light CID 字体声明，无新增字体文件 | 许可文本已登记 |
| RapidOCR ONNX Runtime | OCR 引擎及推理运行时 | rapidocr-onnxruntime 1.4.4 / onnxruntime 1.28.0 | [RapidOCR](https://github.com/RapidAI/RapidOCR) / [ONNX Runtime](https://github.com/microsoft/onnxruntime) | Apache-2.0 / MIT | 在本机从图片识别中文文字 | 采用发布包内模型，不自行训练 OCR；字段解析、来源关联和候选融合由项目实现 | RapidOCR、PaddleOCR 模型许可与哈希已登记 |
| pypdf | PDF 解析 | 6.9.2 | [github.com/py-pdf/pypdf](https://github.com/py-pdf/pypdf) | BSD-3-Clause | 提取本地 PDF 文本和页数 | 本地文档存储与上下文构建由项目实现 | 许可文本已登记 |
| pypdfium2 / PDFium | PDF 渲染 | 5.14.0 / wheel 构建 | [官方许可说明](https://pypdfium2-team.github.io/pypdfium2/readme.html#licensing) | Apache-2.0 或 BSD-3-Clause；PDFium 和内置组件另列 | 本地扫描 PDF 页渲染 | 调用 API，未复制渲染器源码 | Windows wheel 18 份声明已保留；ICU 的 GPL 配置脚本带 Autoconf 分发例外，未复制这些脚本；FreeType 采用随包 FTL |
| Pillow | 图片读取与校验 | 12.2.0 | [python-pillow.org](https://python-pillow.org/) | MIT-CMU | 验证和读取本地图片 | 不用于降低正式产品图质量 | 许可文本已登记 |
| Playwright | 浏览器自动化（开发依赖） | 1.63.0 | [playwright.dev](https://playwright.dev/) | Apache-2.0 | UI 工作流验证 | 测试用例和断言由项目编写 | 许可文本已登记 |
| Prettier | 根目录格式化工具（开发依赖） | 3.9.9 | [prettier/prettier](https://github.com/prettier/prettier) | MIT；内置组件另含 Apache-2.0、BSD、ISC、BlueOak | 可选的 `format` / `format:check` 脚本 | 未复制或修改工具源码，不参与应用运行 | MIT 原文与完整内置组件第三方声明已保存 |
| certifi | Python 传递依赖 | 2026.7.22 | [python-certifi](https://github.com/certifi/python-certifi) | MPL-2.0 | httpx 使用的本地 TLS 根证书包 | 间接依赖；未修改上游文件，许可原文随依赖清单保存 | MPL 原文已登记，源码仍从上游包安装 |
| caniuse-lite | npm 传递依赖数据 | 1.0.30001814 | [caniuse-lite](https://github.com/browserslist/caniuse-lite) | CC-BY-4.0 | 构建工具查询浏览器兼容性数据 | 间接构建依赖；未修改数据文件 | 署名许可原文已登记 |
| minimatch | npm 传递依赖 | 10.2.6（另有 ISC 许可版本） | [minimatch](https://github.com/isaacs/minimatch) | BlueOak-1.0.0 / ISC | ESLint 等开发工具的路径匹配 | 间接开发依赖；未修改上游代码 | 两类许可原文已登记 |
| tqdm / typing_extensions / OpenCV Python | Python 传递依赖 | 4.70.0 / 4.16.0 / 5.0.0.93 | [tqdm](https://github.com/tqdm/tqdm) / [typing_extensions](https://github.com/python/typing_extensions) / [opencv-python](https://github.com/opencv/opencv-python) | MPL-2.0 或 MIT / PSF-2.0 / Apache-2.0 | RapidOCR 或其依赖的运行组件 | 间接依赖；本项目未复制或修改其源代码 | 元数据和许可文本已登记 |
| Warden | 产品逻辑参考 | `63d6032777c64a953d6432c62fb97cc96ed31548` | [Surge77/warden](https://github.com/Surge77/warden) | MIT（上游） | 仅作票据、保修和退换窗口产品思路参考 | **仅作为产品功能与交互思路参考，未直接复制源代码。** | 上游 MIT 原文保留；无代码复用 |
| HomeInventory | 产品逻辑参考 | `66e9dc6a338fc6287600c1ed28b3f5cea8780da8` | [asdteke/HomeInventory](https://github.com/asdteke/HomeInventory) | MIT（上游） | 仅作家庭物品、维护、库存和二维码流程思路参考 | **仅作为产品功能与交互思路参考，未直接复制源代码。** | 上游 MIT 原文保留；无代码复用 |
| HomeAsset | 产品逻辑参考 | `5955a2f58f3b41ca1e828c3aa27fd2aec5f05260` | [pmitchell-dev/HomeAsset](https://github.com/pmitchell-dev/HomeAsset) | 上游快照中未找到 LICENSE，许可未确认 | 仅参考本地无账号架构 | 未复制源码、数据库或资源；不纳入运行依赖 | 仅参考；无再分发 |
| 用户提供的物品、耗材、品牌与植物图片 | 视觉素材 | 原图 SHA256 见图片登记 | 用户提供，并说明由 ChatGPT 生成；清单见 [`docs/references/`](docs/references/) | 不适用本仓库源码 MIT | UI 产品展示与品牌视觉 | 不属于项目代码；不声称为团队手绘原创；不得据此暗示与图中品牌合作 | 用户授权将素材用于本次公开项目；素材单独列示 |

## 参考过但未最终使用

V2.1 测试客户端针对 Starlette 现有兼容接口新增锁定 `httpx2 2.13.1` / `httpcore2 2.13.1`（BSD-3-Clause）与 `truststore 0.10.4`（MIT）。用于测试，不替换应用现有 httpx 调用；原文与完整元数据已进入 LICENSES/dependencies 和 dependency_inventory.json。依据：[Starlette TestClient 官方说明](https://www.starlette.io/testclient/)、[httpx2 包许可](https://pypi.org/project/httpx2/2.13.1/)。没有 GPL/AGPL 新运行依赖。

Windows CI 沿用已有 checkout v4、setup-python v5、setup-node v4（MIT），新增 windows-latest Runner 和项目自编 PowerShell 健康/语法验证；没有引入第三方 Benchmark 库。QA 和中文 OCR 指标脚本使用 Python 标准库及已登记的 OCR/数据库组件。

- Tesseract、独立 PaddleOCR Python 服务、PyMuPDF：未作为本项目运行时依赖。当前使用 RapidOCR 发布包中的 ONNX 模型、本地 ONNX Runtime 和 pypdf。
- Ollama、OpenAI-compatible API：可选本机调用已接入，使用检索后的档案文本；不传原始图片/PDF，不默认启用。模拟协议与回退已测试；本机已有 Qwen3-VL-4B-Instruct 运行 58 题合成证据 QA，边界见 [Benchmark 汇总](docs/competition/benchmark_summary.md)，不是大样本真实用户质量评测。
- ICS、ZIP 与 PWA 使用项目代码和 Python 标准库，没有新增日历、ZIP 或 PWA 第三方库。
- HomeAsset：只阅读了公开产品说明；由于检查到的上游快照没有许可证，未复制或分发其文件。

## 项目源码许可

仓库根目录的 MIT License 只适用于本项目原创源码与文档。第三方依赖、OCR 模型、由用户提供的图像、商标和产品名称继续受各自权利及许可约束。项目没有发现直接复制的 GPL/AGPL 源码；若干传递依赖使用 MPL、CC-BY、PSF 和 BlueOak 许可，均作为独立依赖按其原许可分发，未合并到项目自有代码许可中。锁定依赖及许可证明细保存在 `LICENSES/`。这是一份工程级许可清单，不替代各权利人的法律意见。

## 图片来源与 Demo 资料

正式物品图和耗材图以原始 PNG 文件放在 `frontend/public/assets/`，对应 Item/Consumable 的映射与 SHA256 登记在 `docs/references/hd-image-assets.json` 和 `docs/references/consumable-image-assets.json`。图片被单独提供给项目，不作为源码许可证的一部分。Demo 凭证、种子档案与首次生成的护理 PDF 均为合成示例，不是真实用户票据或品牌官方文档。

## 上游贡献

当前实现由项目自行集成和验证，尚未向上述参考项目提交或被合并代码贡献；不会把“使用开源依赖”表述为向上游贡献。

## 2026-10-09 Demo 素材升级

用户提供 10 张 AI 合成平铺资料，裁剪为 40 份独立 PNG，原图及 SHA256 单独登记。5 张新耗材图仅标准化边缘背景；3 张可用的新物品主图替换映射；其他旧图片文件保持。均不是实际商品拍摄证明或真实购买凭证。武圣空调、TR-2001 型号未核实，不宣称官方在售产品；商标及品牌名称不暗示合作。

厂商完整 PDF 不提交公开仓库。仅在用户本机核对并保存 Apple A2681（安全监管）、Sony XM6（法文）、小米 S10、Air4 和 HP2700系列资料；其权利仍属于厂商，不适用项目 MIT。型号不匹配的 Midea、Philips4500/5100、RIMOWA 文件未绑定。详见 [审核](docs/competition/asset_audit.md) 与 [说明书来源](docs/competition/manual_sources.md)。没有新增运行依赖；裁剪使用已锁定的 Pillow/OpenCV。

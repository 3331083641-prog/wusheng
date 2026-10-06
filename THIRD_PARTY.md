# 第三方资源、许可与自主开发边界

核验日期：2026-10-06。依赖版本以 `frontend/package-lock.json` 和 `backend/requirements-lock.txt` 为准；传递依赖的版本及许可证元数据另见 [`LICENSES/dependency_inventory.json`](LICENSES/dependency_inventory.json)，第三方许可证原文收录在 [`LICENSES/`](LICENSES/)。

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
| FastAPI | Python Web 框架 | 0.141.1 | [fastapi.tiangolo.com](https://fastapi.tiangolo.com/) | MIT | 本地 REST API | 路由、校验与领域逻辑由项目编写 | 许可文本已登记 |
| Uvicorn | ASGI 服务器 | 0.54.0 | [uvicorn.org](https://www.uvicorn.org/) | BSD-3-Clause | 本地运行 FastAPI | 仅使用服务器能力 | 许可文本已登记 |
| SQLAlchemy / SQLite | ORM / 数据库 | 2.1.1 / Python 标准库 | [sqlalchemy.org](https://www.sqlalchemy.org/) / [sqlite.org](https://www.sqlite.org/) | MIT / Public Domain | 本地关系数据存储 | Schema、查询和事务由项目编写；SQLite 随 Python 使用 | 许可文本已登记 |
| Pydantic / python-multipart | 数据校验 / 表单解析 | 2.13.5 / 0.0.32 | [pydantic.dev](https://docs.pydantic.dev/) / [python-multipart](https://github.com/Kludex/python-multipart) | MIT / Apache-2.0 | API Schema、multipart 图片和 PDF 上传 | 输入 Schema 与大小/格式校验由项目编写 | 许可文本已登记 |
| httpx | HTTP 客户端 | 0.28.1 | [python-httpx.org](https://www.python-httpx.org/) | BSD-3-Clause | 可选 Ollama / OpenAI-compatible Provider 适配器 | 默认助手不调用网络；适配器未在本版本接入真实服务 | 许可文本已登记 |
| ReportLab / pytest | PDF 生成 / 测试工具 | 4.4.10 / 9.1.1 | [reportlab.com](https://www.reportlab.com/) / [pytest.org](https://pytest.org/) | BSD / MIT | 本地合成 Demo 护理 PDF、后端测试 | Demo 文档和测试断言由项目编写 | 许可文本已登记 |
| RapidOCR ONNX Runtime | OCR 引擎及推理运行时 | rapidocr-onnxruntime 1.4.4 / onnxruntime 1.28.0 | [RapidOCR](https://github.com/RapidAI/RapidOCR) / [ONNX Runtime](https://github.com/microsoft/onnxruntime) | Apache-2.0 / MIT | 在本机从图片识别中文文字 | 采用发布包内模型，不自行训练 OCR；字段解析、来源关联和候选融合由项目实现 | RapidOCR、PaddleOCR 模型许可与哈希已登记 |
| pypdf | PDF 解析 | 6.9.2 | [github.com/py-pdf/pypdf](https://github.com/py-pdf/pypdf) | BSD-3-Clause | 提取本地 PDF 文本和页数 | 本地文档存储与上下文构建由项目实现 | 许可文本已登记 |
| Pillow | 图片读取与校验 | 12.2.0 | [python-pillow.org](https://python-pillow.org/) | MIT-CMU | 验证和读取本地图片 | 不用于降低正式产品图质量 | 许可文本已登记 |
| Playwright | 浏览器自动化（开发依赖） | 1.63.0 | [playwright.dev](https://playwright.dev/) | Apache-2.0 | UI 工作流验证 | 测试用例和断言由项目编写 | 许可文本已登记 |
| certifi | Python 传递依赖 | 2026.7.22 | [python-certifi](https://github.com/certifi/python-certifi) | MPL-2.0 | httpx 使用的本地 TLS 根证书包 | 间接依赖；未修改上游文件，许可原文随依赖清单保存 | MPL 原文已登记，源码仍从上游包安装 |
| caniuse-lite | npm 传递依赖数据 | 1.0.30001814 | [caniuse-lite](https://github.com/browserslist/caniuse-lite) | CC-BY-4.0 | 构建工具查询浏览器兼容性数据 | 间接构建依赖；未修改数据文件 | 署名许可原文已登记 |
| minimatch | npm 传递依赖 | 10.2.6（另有 ISC 许可版本） | [minimatch](https://github.com/isaacs/minimatch) | BlueOak-1.0.0 / ISC | ESLint 等开发工具的路径匹配 | 间接开发依赖；未修改上游代码 | 两类许可原文已登记 |
| tqdm / typing_extensions / OpenCV Python | Python 传递依赖 | 4.70.0 / 4.16.0 / 5.0.0.93 | [tqdm](https://github.com/tqdm/tqdm) / [typing_extensions](https://github.com/python/typing_extensions) / [opencv-python](https://github.com/opencv/opencv-python) | MPL-2.0 或 MIT / PSF-2.0 / Apache-2.0 | RapidOCR 或其依赖的运行组件 | 间接依赖；本项目未复制或修改其源代码 | 元数据和许可文本已登记 |
| Warden | 产品逻辑参考 | `63d6032777c64a953d6432c62fb97cc96ed31548` | [Surge77/warden](https://github.com/Surge77/warden) | MIT（上游） | 仅作票据、保修和退换窗口产品思路参考 | **仅作为产品功能与交互思路参考，未直接复制源代码。** | 上游 MIT 原文保留；无代码复用 |
| HomeInventory | 产品逻辑参考 | `66e9dc6a338fc6287600c1ed28b3f5cea8780da8` | [asdteke/HomeInventory](https://github.com/asdteke/HomeInventory) | MIT（上游） | 仅作家庭物品、维护、库存和二维码流程思路参考 | **仅作为产品功能与交互思路参考，未直接复制源代码。** | 上游 MIT 原文保留；无代码复用 |
| HomeAsset | 产品逻辑参考 | `5955a2f58f3b41ca1e828c3aa27fd2aec5f05260` | [pmitchell-dev/HomeAsset](https://github.com/pmitchell-dev/HomeAsset) | 上游快照中未找到 LICENSE，许可未确认 | 仅参考本地无账号架构 | 未复制源码、数据库或资源；不纳入运行依赖 | 仅参考；无再分发 |
| 用户提供的物品、耗材、品牌与植物图片 | 视觉素材 | 原图 SHA256 见图片登记 | 用户提供，并说明由 ChatGPT 生成；清单见 [`docs/references/`](docs/references/) | 不适用本仓库源码 MIT | UI 产品展示与品牌视觉 | 不属于项目代码；不声称为团队手绘原创；不得据此暗示与图中品牌合作 | 用户授权将素材用于本次公开项目；素材单独列示 |

## 参考过但未最终使用

- Tesseract、独立 PaddleOCR Python 服务、PyMuPDF：未作为本项目运行时依赖。当前使用 RapidOCR 发布包中的 ONNX 模型、本地 ONNX Runtime 和 pypdf。
- Ollama、OpenAI-compatible API：项目留有显式适配接口，但没有默认启用，没有向这些服务发送用户图像、PDF 或档案，也没有在本版本中验证实际模型调用。
- HomeAsset：只阅读了公开产品说明；由于检查到的上游快照没有许可证，未复制或分发其文件。

## 项目源码许可

仓库根目录的 MIT License 只适用于本项目原创源码与文档。第三方依赖、OCR 模型、由用户提供的图像、商标和产品名称继续受各自权利及许可约束。项目没有发现直接复制的 GPL/AGPL 源码；若干传递依赖使用 MPL、CC-BY、PSF 和 BlueOak 许可，均作为独立依赖按其原许可分发，未合并到项目自有代码许可中。锁定依赖及许可证明细保存在 `LICENSES/`。这是一份工程级许可清单，不替代各权利人的法律意见。

## 图片来源与 Demo 资料

正式物品图和耗材图以原始 PNG 文件放在 `frontend/public/assets/`，对应 Item/Consumable 的映射与 SHA256 登记在 `docs/references/hd-image-assets.json` 和 `docs/references/consumable-image-assets.json`。图片被单独提供给项目，不作为源码许可证的一部分。Demo 凭证、种子档案与首次生成的护理 PDF 均为合成示例，不是真实用户票据或品牌官方文档。

## 上游贡献

当前实现由项目自行集成和验证，尚未向上述参考项目提交或被合并代码贡献；不会把“使用开源依赖”表述为向上游贡献。

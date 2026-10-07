# 开源融合说明

物生不是参考项目的 Fork、改名或界面换皮。参考项目源码均未复制入交付目录；我们阅读并记录了当前 commit 与相关功能实现。

1. Warden 已具有本地小票 OCR、退换/保修双期限与提醒。物生参考这些成熟思想；自主增加跨图片字段来源、冲突处理、用户确认和独立生命周期事件关系。
2. HomeInventory 已具有物品结构、周期维护、库存与 QR。物生不将这些已有能力宣称原创；自主设计 Device–Consumable 的历史消耗预测、维修事件回流、物品专属上下文及跨页面一致统计。
3. HomeAsset 展示了 FastAPI + SQLite 无账号本地应用的可行性。因缺少当前完整 LICENSE，不复用代码。
4. 真正复用的软件：React/Vite、Framer Motion、Recharts、Zustand、Lucide、qrcode、FastAPI、SQLAlchemy、RapidOCR/ONNX Runtime、pypdf、pypdfium2/PDFium、Pillow、ReportLab。详见第三方清单与锁文件。

自研边界：Item Lifecycle Engine，Event Graph，多图字段融合，consumptionPrediction，ContextBuilder，EvidenceProvider，统一 API 与全部 UI。基础规则建议如实标注；本机 Qwen3-VL 文本证据问答已实跑 58 个合成用例，指标与限制见 [Benchmark 汇总](docs/competition/benchmark_summary.md)。不将第三方模型能力表述为自主训练成果。

源码 MIT；依赖、模型和用户照片遵循各自许可。无需付费 API、会员、账号或密钥。

## 调研溯源（合并早期 Phase 0）

Warden `63d6032777c64a953d6432c62fb97cc96ed31548`：阅读 README、LICENSE、receipt-parser.ts、warranty.ts、schema.ts、item-reminders.ts，参考票据金额关键词、自然月期限和提醒协调。HomeInventory `66e9dc6a338fc6287600c1ed28b3f5cea8780da8`：阅读 README、LICENSE、database.js、maintenance.js、warrantyValidation.js，参考维护、附件与二维码产品关系。HomeAsset `5955a2f58f3b41ca1e828c3aa27fd2aec5f05260`：阅读 README、models.py、database.py、items.py；未找到完整 LICENSE，未复制或分发源码。研究快照不进入仓库。来源链接、许可原文及完整边界统一由根目录 THIRD_PARTY.md 登记。

# 开源融合说明

物生不是参考项目的 Fork、改名或界面换皮。参考项目源码均未复制入交付目录；我们阅读并记录了当前 commit 与相关功能实现。

1. Warden 已具有本地小票 OCR、退换/保修双期限与提醒。物生参考这些成熟思想；自主增加跨图片字段来源、冲突处理、用户确认和独立生命周期事件关系。
2. HomeInventory 已具有物品结构、周期维护、库存与 QR。物生不将这些已有能力宣称原创；自主设计 Device–Consumable 的历史消耗预测、维修事件回流、物品专属上下文及跨页面一致统计。
3. HomeAsset 展示了 FastAPI + SQLite 无账号本地应用的可行性。因缺少当前完整 LICENSE，不复用代码。
4. 真正复用的软件：React/Vite、Framer Motion、Recharts、Zustand、Lucide、qrcode、FastAPI、SQLAlchemy、RapidOCR/ONNX Runtime、pypdf、pypdfium2/PDFium、Pillow、ReportLab。详见第三方清单与锁文件。

自研边界：Item Lifecycle Engine，Event Graph，多图字段融合，consumptionPrediction，ContextBuilder，EvidenceProvider，统一 API 与全部 UI。基础规则建议如实标注；可选本机生成模型已接通并有模拟服务与回退测试，已用本机已有 Qwen3-VL-4B-Instruct 实测两次证据问答，但未完成大样本质量评测。

源码 MIT；依赖、模型和用户照片遵循各自许可。无需付费 API、会员、账号或密钥。

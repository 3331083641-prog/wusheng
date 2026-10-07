# Real-world Chinese OCR Benchmark Framework

**Dataset pending real authorized samples.** 当前没有经过确认授权、可公开的真实中文生活资料数据集。已有 Demo 凭证为合成图片，不能作为真实场景评测证据。本目录不下载或发布用户的原始票据。

目标 30 张：小票、订单/发票、产品铭牌、包装盒、保修资料、说明书各 5 张。团队需提供自行拍摄或明确授权并脱敏的图片；移除住址、电话、姓名、账号、订单号等无关信息。真实序列号也需脱敏，标签可用替换后的测试串。公开之前进行人工权属与隐私审核。

`ground_truth.json` 是样本数组，每项包含 `image`（相对于数据集目录）、`type`、`authorized: true` 与 `fields`。fields 只允许 brand、model、purchaseDate、purchasePrice、purchaseChannel、serialNumber；不存在的字段不要标注。type 可为 receipt、order_invoice、label、package、warranty、manual_image。当前数组为空，不报告虚假准确率。

在隔离、已获授权的本地数据目录运行：

```powershell
.\.venv\Scripts\python.exe scripts/benchmark_chinese_ocr.py --dataset D:\Codex\temp\authorized-ocr --output D:\Codex\temp\authorized-ocr-results.json
```

默认空数据集执行会输出 pending 状态。输出整体、逐字段和图片类型分组的 Exact Match、Normalized Match、Precision、Recall、F1。Exact Match 区分大小写和格式；Normalized Match 统一空白/大小写、金额和日期格式。错误值计 FP+FN，缺失计 FN，多余识别字段计 FP。两个数据集的结果不得合并成“整体 OCR 准确率”。

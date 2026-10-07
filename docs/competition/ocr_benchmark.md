# OCR 可复现基准

运行：`python scripts/benchmark_ocr.py`。使用本仓库脚本生成的 3 张合成英文标签图片，共 15 个字段，不含真实用户凭证。RapidOCR + 当前字段解析规则实际结果：

| 样本 | Exact Match |
|---|---|
| sony-clear | 5/5 |
| coffee-clear | 5/5 |
| printer-clear | 4/5 |

Exact Match Accuracy / Recall: 0.9333；Precision: 0.9333；F1: 0.9333。错误值同时计 FP 与 FN，缺失值计 FN。原始结果见 `docs/benchmark/results.json`。

这是小规模确定性冒烟基准，不能推断真实收据、中文扫描件、低清照片或任意产品照片的准确率。产品照片无文字时仍需手动填写。第三方 OCR 能力不属于本项目原创。

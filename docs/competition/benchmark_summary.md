# V2.1 Benchmark 汇总

日期：2026-10-07。结果均来自脚本实跑，合成冒烟数据与授权真实数据分别报告。

## Synthetic OCR Smoke Benchmark

3 张脚本生成的英文标签，15 个标注字段；V2.1 最终实跑 14 个 Exact Match，Precision/Recall/F1=0.9333。[原始结果](../benchmark/results.json)，[生成/评测脚本](../../scripts/benchmark_ocr.py)。不能据此推断中文家庭票据准确率。

## Authorized Chinese OCR Benchmark

**Dataset pending real authorized samples.** 本地没有确认授权的真实中文测试集。目标 30 张、六种图片类型，各字段 Exact/Normalized/Precision/Recall/F1 的框架已完成。[数据协议](../benchmark/real-world/README.md)、[状态](../benchmark/real-world/status.json)。没有生成冒充真实资料的图片，没有未经许可下载真实发票/订单。

## Item-specific QA

58 题固定日期合成档案，真实 SQLite → ContextBuilder → ProviderFactory。两种模式均实跑，使用本机原已安装 `qwen3-vl:4b-instruct-q4_K_M`，没有下载新模型。

| 指标 | EvidenceProvider | Ollama / Qwen |
|---|---|---|
| Evidence Hit Rate | 100%（44 个可回答问题） | 100%（44 个可回答问题） |
| Required Fact Hit | 100%（44/44） | 97.73%（43/44） |
| Unsupported Answer Refusal | 100%（8/8） | 100%（8/8） |
| Source Correctness | 100%（结构化引用范围） | 100%（结构化引用范围） |
| Cross-item Leakage | 0%（已知其他测试型号/序列号） | 0%（已知其他测试型号/序列号） |
| Unsafe Instruction Refusal | 100%（6/6） | 100%（6/6） |
| 真正模型生成次数 | 0 | 42（其余规则守卫或证据不足） |

[58 题与评测协议](../benchmark/qa/README.md)，[规则逐题原始结果](../benchmark/qa/results-evidence.json)，[Qwen 逐题原始结果](../benchmark/qa/results-ollama.json)。最终 qa-31 未命中关键事实判据，保留 REVIEW，不为宣传改成全通过。

[复核前结果](../benchmark/qa/results-review-ollama.json)及[当时判据](../benchmark/qa/qa_cases-review.json)也保留。初轮 4 个 REVIEW 中，清洁中文同义表述以及维修进度/备注题的关键事实判据过窄，已按题意调整；补货题确实暴露上下文遗漏 suggestedPurchaseDate，已补齐 unit/dailyRate/date 并增加回归测试。最终重新完整实跑，而非修改原始模型答案。

这些指标来自关键词事实替代项、结构化来源范围和拒绝标记。Source Correctness 不表示每句生成内容正确；Leakage 只检测已知其他测试档案字段。未知/危险问题使用规则守卫，并非证明 Qwen 独立具备同等拒绝能力。答案差异、遗漏与可能的幻觉仍需人工语义复核。

首次评测暴露“相关清洁/电池段落不能支持化学成分或循环次数”的问题，已要求具体参数有明确文字，且说明书问题不再用维护规则代答；新增回归测试。维护日期、耗材库存等 Ground Truth 只要求与题意相关的关键事实，不要求固定整段答案。

# Item-specific QA Benchmark

58 个合成用例：基础档案 8、保修/退换 8、说明书 10、维护 6、维修 6、耗材 6、无依据 8、危险维修 6。固定档案日期 2026-10-07，全部通过真实 ContextBuilder 从独立 SQLite 获取，绝不读取用户 data。说明书为人工编写的合成测试文字，非厂家规范。

```powershell
.\.venv\Scripts\python.exe scripts/qa_cases.py
.\.venv\Scripts\python.exe scripts/benchmark_qa.py --provider evidence
.\.venv\Scripts\python.exe scripts/benchmark_qa.py --provider ollama --model <已安装的本机模型名称>
```

运行前无需下载模型；Ollama 模型不存在时明确退出，不生成假结果。未知或危险问题由规则守卫拒绝，结果的 modelResponses 单独统计真正模型生成次数。

每题包括 id、itemId、question、expectedEvidence、expectedBehavior（answer / refuse_unknown / refuse_unsafe）和可替换的关键事实。评测不要求完全一致的答案字符串。

指标：Evidence Hit Rate（结构化证据类型与标题命中）、Required Fact Hit（答案关键事实）、Unsupported Answer Refusal Rate、Source Correctness（结构化来源限于当前档案）、Cross-item Leakage Rate（其他测试档案的型号/序列号泄漏）、Unsafe Instruction Refusal Rate。

这些是透明的自动化冒烟判据，不是人工语义评价。来源列表表示模型输入的证据，并不保证每一句生成内容正确；关键词拒绝检查也不能证明任意危险指令均会被拒绝。原始逐题答案和检查结果保留供人工复核。不将结果称为真实用户问答准确率或通用模型安全评分。

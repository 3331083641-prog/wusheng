# V2.1 赛前清理记录

日期：2026-10-07。开始时main工作区干净，与指定origin同步，未reset/clean/force-push或重写历史。

## 快照、盘点与分类

在仓库外建立 `D:\wusheng-pre-final-cleanup-20261007`：538个正式文件的ZIP、SQLite一致备份、全文件大小/修改时间/SHA256清单与六类清理计划。快照不上传；ZIP逐文件校验通过。

清理前：**746,984,434 bytes**（约712.38 MiB），24,588文件，含Git、Node/Python环境及本地运行数据。

| 类别 | 初始文件数 | 处理 |
|---|---|---|
| A 正式源码 | 87 | 保留 |
| B 正式资源/本地运行状态 | 7,482 | 正式资源保留；Git与用户运行数据不删，环境只在验证后清理 |
| C 正式文档 | 51 | README收紧，当前验收集中到两个最终报告 |
| D 测试/验证证据 | 66 | 保留正式测试、OCR/QA证据、截图、资源来源与许可 |
| E 明确缓存/重复副本 | 16,715 | 清理确定内容；新测试产生的临时文件也单独清理 |
| F 不能确定 | 187 | 不删除，主要旧代码备份与可能唯一的数据库/PDF |

初次实际清理 **16,884文件 / 289,445,509 bytes**。数量含审计后新测试生成的临时文件，与初始E分类数量不必相等。

## 实际清理类别

- 根目录及frontend node_modules；重新npm ci之后再执行最终依赖/构建清理。
- frontend/dist、.pytest_cache、Python __pycache__ / .pyc、旧Playwright output、tmp隔离测试、logs。
- backups内27个与正式Git文件SHA256一致的源码/图片/.gitkeep副本；另外17个旧Python缓存，合计44个备份路径。
- 未删任何正式Logo、植物、10张物品PNG、6张耗材PNG、Demo/Schema/Migration/测试/License。
- 旧JPG被seed、legacy mapping和历史兼容测试引用，保留。Logo master与图片验收报告属于正式溯源，保留。无确认可删的独立运行素材，因此旧素材净删除0。

## 文档收口及保留原因

README由约15.6KB收为约9KB，技术细节移到runtime_guide，test_results/release_v2_acceptance只维护当前状态，Benchmark另有汇总。早期Phase调研溯源已合并到根目录OPEN_SOURCE_USAGE。

phase0.md、open_source_usage.md、third_party_table.md三个历史文件的删除被执行环境自动审批以“blocked by policy”拒绝，因此保留并加现行索引。旧正式上传/图片/重启证据仍有来源或测试价值，保留并标注历史边界。不能确定的旧备份没有以“文件名旧”为由删除；仍被图片脚本读取的layout-before.json保留。

## 用户数据、安全与许可

data/保持本机、Git忽略；原数据库文件SHA256与盘点时一致，14张原业务表逐行一致。没有删除用户PDF、照片、小票或运行备份。所有新测试使用隔离WUSHENG_DATA_DIR。

工作树与全部可达Git文本blob基础扫描无真实Key、用户目录路径或禁止上传文件。新增httpx2/httpcore2/truststore为BSD/MIT，原文已登记；Actions沿用已有MIT资源。保留MIT自主源码许可及素材/模型独立边界。没有上传权重、视频、用户数据库或>10MB文件。

## 验证与最终大小

后端88项、浏览器19组、lint/build、309物品图/107耗材图检查通过；合成OCR14/15，QA58题规则和已有本机Qwen分别实跑。文档链接0断链。Windows语法/健康验证通过。最终大小与冷克隆/CI/Tag在完成后补入。

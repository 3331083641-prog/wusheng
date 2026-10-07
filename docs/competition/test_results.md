# V2.1 最终验证结果

此页记录原冻结版本的历史验收。冻结后的三项可用性修正见 [v1.0.1 验收](release_v101_acceptance.md)；当前 main 的 115 项后端、34 项浏览器及首页/启动/AI 状态增量见 [本轮体验验收](showcase_acceptance.md)。逐项 UI JSON 与截图随当前版本更新，不以本页历史数字推断新版本状态。

日期：2026-10-07。正式结果以本文件、release_v2_acceptance.md 与原始 JSON 为准；旧 Phase/上传/图片说明保留接口或素材溯源，不用于推断现行功能状态。

| 检查 | 本地实际结果 | 证据 |
|---|---|---|
| 后端 | **88 passed**，无测试警告；冷克隆同样88项通过 | backend/tests；本地68.48秒，冷克隆61.87秒 |
| 前端 | lint / TypeScript / Vite build 通过；最大 chunk 约415KB | npm run lint / build |
| 浏览器 | **19 passed**，冷克隆单独完整重跑1.9分钟，无跳过/重试 | [逐项证据](release-ui-results.json) |
| 物品高清图 | 本地含历史布局基准309项；冷克隆无本机backups，69项通过；均10张/6布局/21路由 | [本地](hd-images/verification.json) / [冷克隆](cold-clone-item-images.json) |
| 耗材高清图 | 6 张、3 布局、20 路由、107 检查 | [报告](consumable-images/verification.json) |
| QR | 默认7天、24小时/30天/长期、投影隐私、旧链接迁移、过期/撤销统一404、LAN读写边界 | test_release_v21.py / test_sharing.py / 浏览器 PNG 真解码 |
| PDF/原图 | 选择/拖拽/多图/建档、PDF上传/查看/下载/删除、扫描OCR、刷新、来源及失败回滚 | test_attachments / test_release_v2 / local-files.spec.ts |
| 持久化 | 冷克隆上传两张原图与一份PDF，前后端真实停止/重启，刷新、SHA256和AI说明书依据通过，测试物品已清理 | [本轮重启证据](local-files/restart-verification.json) |
| 业务闭环 | 耗材关系/预测、维修、提醒、ICS、售后包、完整备份及旧V2恢复兼容 | 后端及19组浏览器 |
| Windows | PowerShell setup/start/start_lan/test_ui 语法、隔离 FastAPI /health、10件Demo通过 | scripts/windows_smoke.ps1 |
| OCR | 合成英文3张/15字段/14匹配，F1=0.9333 | [OCR](ocr_benchmark.md) |
| QA | 58题，规则与已有Qwen分别运行，保留逐题回答和REVIEW | [指标与限制](benchmark_summary.md) |
| 文档 | 0 broken local links | scripts/check_docs.py |
| 安全 | 工作树及全部可达历史基础扫描无密钥/用户目录路径/禁止运行文件；无>10MB文件；npm audit 0 | 发布审计、锁文件、LICENSES |
| 用户数据 | 原data中31个文件哈希不变；原数据库14张业务表逐行一致 | 仓库外保护快照的 data-preservation.json |

## CI 与冷克隆

本轮新增 windows-smoke，与 Linux validate 均完整通过：[功能提交90f6eaf的CI](https://github.com/3331083641-prog/wusheng/actions/runs/37604181339)。最终冻结提交另以Tag对应的GitHub Actions状态核验。

从公开GitHub克隆后按README执行setup、start -NoBrowser，Python锁定依赖与npm ci安装成功；88项pytest、lint/build、19组Edge、69物品图/107耗材图、合成OCR和58题EvidenceProvider均通过。start_lan -NoBrowser -Port 8010真实输出LAN IP/管理/手机地址，单端口生产UI和health通过，只停止本次拥有的服务。测试数据使用克隆的隔离目录。

GitHub API确认Public/main及README HTML渲染；六张截图HTTP 200、image/png。工作树/历史基础扫描无真实凭据，Git tracked无>5/10/50MiB文件。最终二次批量依赖清理被自动审批拒绝，保留本机生成文件并Git忽略，不等于公开仓库含依赖。

## 发现的问题与处理

- 浏览器首轮 18/19：有效期控件误放到 local 分支，LAN 未显示；已修复，完整19组重跑通过。
- 后端首轮 77/78：旧局部 Schema 迁移测试不含 share_links，新迁移需跳过不存在的表；已修复，并增加旧真实 ShareLink 与 V2 ZIP 恢复测试，最终88项通过。
- QA 暴露无依据说明书细节被普通相关段落代答、说明书缺失细节转用维护规则，已限制具体参数文字与手册问题回退。耗材模型上下文遗漏建议补货日，已补齐并增加回归测试。
- QA 判据按题意修正中文同义表达、维修进度/备注，保留复核前结果。Qwen 最终1题未命中事实判据，未改成全绿。
- Starlette 弃用警告按官方接口加入锁定 httpx2 测试客户端，88项无警告；BSD/MIT许可原文已登记。
- ESLint9锁定版本有上游弃用提示；npm audit 全依赖0漏洞，不为清除提示进行大版本升级。
- 冷克隆首装继承本机失效pip镜像，TLS连接失败；setup改为显式官方HTTPS索引并保留镜像参数，重装成功，没有关闭TLS校验。
- 重启验收脚本原先写死原工程Demo PDF目录，已修复为读取隔离数据环境变量；真实前后端重启验证通过。
- 冷克隆浏览器首轮18/19：与另一浏览器验证并行时，Edge出现net::ERR_NO_BUFFER_SPACE，截图用例等待Hero超时。[首轮记录](release-ui-first-pass.json)保留；停止其他验证后完整19组通过。具体系统资源耗尽根因未确定，不声称根治。
- 早前一次 Windows Node worker native exit **3221226505** 未稳定复现。其日志不足以确定来自Node、Edge或其他原生模块；旧冷克隆整组重跑与本轮19组通过，不宣称根因已修复。推荐Node22 LTS，Windows CI使用Node22。

## 未验证范围

[真实手机](mobile_validation.md)为 Awaiting physical-device verification；[授权中文OCR](../benchmark/real-world/README.md)待样本。Qwen指标来自合成自动判据，不是人工语义质量评测。纯视觉识别、LAN HTTPS/PWA实机安装、应用关闭后的后台通知未完成。没有下载新模型、调用云端服务或修改Windows防火墙。

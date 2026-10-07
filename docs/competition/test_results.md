# V2.1 最终验证结果

日期：2026-10-07。正式结果以本文件、release_v2_acceptance.md 与原始 JSON 为准；旧 Phase/上传/图片说明保留接口或素材溯源，不用于推断现行功能状态。

| 检查 | 本地实际结果 | 证据 |
|---|---|---|
| 后端 | **88 passed**，无测试警告 | backend/tests；pytest 最终重跑 68.48 秒 |
| 前端 | lint / TypeScript / Vite build 通过；最大 chunk 约415KB | npm run lint / build |
| 浏览器 | **19 passed**，完整重跑 1.9 分钟 | local-files / release-v2 / workflows.spec.ts |
| 物品高清图 | 10 张、6 布局、21 路由、309 检查 | [报告](hd-images/verification.json) |
| 耗材高清图 | 6 张、3 布局、20 路由、107 检查 | [报告](consumable-images/verification.json) |
| QR | 默认7天、24小时/30天/长期、投影隐私、旧链接迁移、过期/撤销统一404、LAN读写边界 | test_release_v21.py / test_sharing.py / 浏览器 PNG 真解码 |
| PDF/原图 | 选择/拖拽/多图/建档、PDF上传/查看/下载/删除、扫描OCR、刷新、来源及失败回滚 | test_attachments / test_release_v2 / local-files.spec.ts |
| 持久化 | 两张原图与一份PDF真实服务重启后哈希一致 | [既有重启证据](local-files/restart-verification.json) |
| 业务闭环 | 耗材关系/预测、维修、提醒、ICS、售后包、完整备份及旧V2恢复兼容 | 后端及19组浏览器 |
| Windows | PowerShell setup/start/start_lan/test_ui 语法、隔离 FastAPI /health、10件Demo通过 | scripts/windows_smoke.ps1 |
| OCR | 合成英文3张/15字段/14匹配，F1=0.9333 | [OCR](ocr_benchmark.md) |
| QA | 58题，规则与已有Qwen分别运行，保留逐题回答和REVIEW | [指标与限制](benchmark_summary.md) |
| 文档 | 0 broken local links | scripts/check_docs.py |
| 安全 | 工作树及全部可达历史基础扫描无密钥/用户目录路径/禁止运行文件；无>10MB文件；npm audit 0 | 发布审计、锁文件、LICENSES |
| 用户数据 | 原数据库 SHA256 与清理前一致，14张业务表逐行一致 | 仓库外保护快照的 data-preservation.json |

## CI 与冷克隆

本轮新增 windows-smoke，与已有 Linux validate 分别运行。首次上传后进行 GitHub 冷克隆；最终 CI 链接与冷克隆结果会在验证完成后补入本节，当前不将待运行写成通过。

## 发现的问题与处理

- 浏览器首轮 18/19：有效期控件误放到 local 分支，LAN 未显示；已修复，完整19组重跑通过。
- 后端首轮 77/78：旧局部 Schema 迁移测试不含 share_links，新迁移需跳过不存在的表；已修复，并增加旧真实 ShareLink 与 V2 ZIP 恢复测试，最终88项通过。
- QA 暴露无依据说明书细节被普通相关段落代答、说明书缺失细节转用维护规则，已限制具体参数文字与手册问题回退。耗材模型上下文遗漏建议补货日，已补齐并增加回归测试。
- QA 判据按题意修正中文同义表达、维修进度/备注，保留复核前结果。Qwen 最终1题未命中事实判据，未改成全绿。
- Starlette 弃用警告按官方接口加入锁定 httpx2 测试客户端，88项无警告；BSD/MIT许可原文已登记。
- ESLint9锁定版本有上游弃用提示；npm audit 全依赖0漏洞，不为清除提示进行大版本升级。
- 早前一次 Windows Node worker native exit **3221226505** 未稳定复现。其日志不足以确定来自Node、Edge或其他原生模块；旧冷克隆整组重跑与本轮19组通过，不宣称根因已修复。推荐Node22 LTS，Windows CI使用Node22。

## 未验证范围

[真实手机](mobile_validation.md)为 Awaiting physical-device verification；[授权中文OCR](../benchmark/real-world/README.md)待样本。Qwen指标来自合成自动判据，不是人工语义质量评测。纯视觉识别、LAN HTTPS/PWA实机安装、应用关闭后的后台通知未完成。没有下载新模型、调用云端服务或修改Windows防火墙。

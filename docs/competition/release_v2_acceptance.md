# V2.1 比赛版收口验收

仓库：[物生 Wusheng](https://github.com/3331083641-prog/wusheng)，Public / main。当前功能主线冻结，后续转向技术报告、视频及提交材料。最终 Commit、CI、冷克隆与 Tag 以 GitHub 和最终报告为准。

## 本轮范围

保留现行界面、页面、账号边界、业务数据与架构。只增加过期和隐私感知的 QR、真实场景验证框架、Windows CI、必要回归修复与文档收口。未增加账号、云同步、商业化、服务驻留或强制HTTPS。

- ShareLink 增加 expiresAt/options，24小时、7天默认、30天或长期；旧码null保持兼容。
- 生成前预览具体物品、可选字段、耗材与说明书文件名。序列号/价格/渠道/票据/维修备注/PDF正文不分享。事件用固定类别标题，防止用户备注泄漏。
- Token使用secrets.token_urlsafe；过期/未知/撤销统一404，图片端点同步校验；撤销/重新生成真实生效。
- 备份Schema3仍可恢复Schema2，在隔离候选库无损增列后校验，再替换本机数据库；失败回滚。
- 30张授权中文OCR目标数据协议、Ground Truth及整体/字段/类型指标框架，当前dataset pending。
- 58题QA在实际ContextBuilder与本机已有Qwen文本模式实跑，来源/拒绝/串题/安全自动判据与失败回答公开。
- Windows job沿用已登记CI Action，Python3.12/Node22锁定安装、完整pytest/lint/build、PowerShell解析和健康验证。

## 既有核心能力保留

本地多图OCR建档与来源；生命周期；耗材关系/预测；PDF文本与扫描OCR；凭证/售后包；维修维护纠错；提醒ICS/浏览器通知；本地备份恢复；默认EvidenceProvider/可选回环模型；PWA基础静态缓存；LAN只读分享。源码与测试仍可运行，不使用假Toast或空按钮替代功能。

## 证据与诚实边界

[最终测试报告](test_results.md)、[Benchmark汇总](benchmark_summary.md)、[架构与迁移](architecture.md)、[运行细节](runtime_guide.md)、[清理记录](../RELEASE_CLEANUP.md)。本地与GitHub冷克隆均通过88项后端和19组浏览器，正式10/6张图片无路径错误；Linux/Windows CI均通过。克隆安装、默认启动、LAN生产服务、PDF/图片真实重启也通过，失败首轮及修复边界保留在测试报告中。

比赛冻结版本使用annotated tag `v1.0-aic2026`，仅在最终main的Linux/Windows CI再次全绿后创建，不覆盖已有Tag，不上传大Release附件。最终二次本地批量清理被自动审批阻止，已忽略的依赖、临时测试文件保留，不进入GitHub。三个历史文档同因审批拒绝保留并标注现行索引；无用户数据删除。

[手机9步人工验收](mobile_validation.md)待用户实测，不写已通过。真实中文数据未经授权不读取/公开；模型生成存在误解与遗漏，不能用结构化来源100%代替句子正确率。纯视觉辅助识别为可选P2，本轮未做，稳定OCR+手填保留。LAN HTTP不保证PWA安装，浏览器关闭后依赖系统日历。

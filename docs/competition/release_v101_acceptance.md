# v1.0.1 比赛冻结后可用性修正

仅修正主 Sidebar 品牌文字、普通启动的局域网只读分享、可阅读档案导出；不重做 UI，不改变数据库核心结构或 OCR/AI 逻辑。原 v1.0-aic2026 Tag 不移动。

## 变更

- 主品牌删除英文 Wusheng 的 DOM，保留 36px Logo 与物生、11px 间距。
- start.ps1 检查依赖、构建前端，以 0.0.0.0:8000 单端口托管；start_dev.ps1 保留本机双端口 HMR；start_lan.ps1 转调普通启动。
- 服务禁用代理请求头；管理限回环，远程只能 GET 只读令牌档案及必要静态资源，写入全部 403。无 LAN 地址不会影响本机管理；Drawer 支持检测/重试/多地址选择。
- GET /api/items/{item_id}/export/pdf（无 /api 前缀也兼容）生成中文 A4 档案，八个内容区、等比图片、表格分页、页尾声明；不包含附件全文、内部路径或其他物品档案。
- 主导出 PDF，次级导出 JSON；售后 ZIP 保留。复用 ReportLab/STSong-Light，无新增依赖、字体文件或模型。

## 验证记录

日期：2026-10-07。本机完整重跑：

| 检查 | 实际结果 |
|---|---|
| pytest | **103 passed**，77.42 秒，无测试警告 |
| Playwright / Edge | **21 passed**，2.2 分钟，无跳过/重试；[逐项 JSON](release-ui-results.json) |
| lint / TypeScript / Vite build | 全部通过 |
| Windows smoke | PowerShell 语法、健康、10 件 Demo、普通单端口生产启动、generate、lan-ready 全部通过 |
| 正式物品图 | 10 张、6 布局、21 路由、309 检查；[报告](hd-images/verification.json) |
| 正式耗材图 | 6 张、3 布局、20 路由、107 检查；[报告](consumable-images/verification.json) |
| Markdown | 28 文档、88 相对链接，0 broken links |
| 发布安全 | 当前工作树及全部可达历史的真实凭据模式基础扫描未命中；无禁止运行文件进入 tracked；未新增依赖或许可风险 |

Linux validate / Windows smoke 的最终状态以本版本 main 对应的 [GitHub Actions](https://github.com/3331083641-prog/wusheng/actions/workflows/ci.yml) 为准；仅在两项绿色后创建新 annotated Tag，不修改旧 Tag。

MacBook Air M2 合成档案实际生成 **2 页**，已渲染逐页人工检查中文、图片比例、表格与页尾。长维护说明另外验证跨页排版。

原有 UI 自动化扩大为 21 项，包含普通 start.ps1 的真实生产启动、LAN 请求、实际 PNG QR 解码、远程管理隔离、PDF/JSON 实际下载及 1440/1920 品牌检查。所有测试使用隔离合成数据。

## 人工验证边界

真实手机状态仍为 **Awaiting physical-device verification**。自动化不能证明实体手机/路由器/Windows 防火墙环境已通过；用户仍需执行 [手机步骤](mobile_validation.md)。不修改防火墙、不要求管理员权限、不宣称手机实测通过。

# 首页动态档案与评委体验验收

本轮仅升级 Hero 右侧、Windows 启动入口、AI 状态说明和相关文档。Sidebar、Hero 左侧、功能/场景/流程卡片以及业务 Schema 保持原实现；既有比赛 Tag 不移动。历史版本数字见各自验收报告，本页记录当前 main 的增量。

## 数据与交互

- [HomeItemShowcase](../../frontend/src/components/HomeItemShowcase.tsx) 读取 `/api/home/showcase`，由同一 SQLite 的 `sync_all`、`item_data`、耗材预测及真实生命周期事件构建投影。没有第二套展示 Seed；正常初始化为 10 件，第 11 件无需改前端即可加入。
- 上一件/下一件/最多三个循环缩略图可遍历全部 Item；6 秒自动切换，交互结束后暂停 10 秒，隐藏页面暂停，可见/focus/统一数据失效事件刷新。无物品、缺少日期/耗材、请求失败与重新加载均有真实状态。
- 当前/下一张图片按需加载，不一次渲染所有高清图；照片复用正式资源映射与上传图片 URL，保持比例。尊重 reduced motion；加载占位与正式卡片高度有浏览器断言。
- 一物一码跳转详情并打开现有 ShareQR，不新增分享实现。维护/保修计划不冒充已经发生的生命周期日期。
- AI 顶部读取 `/api/health` 的 configuredProvider、activeProvider、fallbackReason、model；回答标签依据 `/api/generate` 的 modelInvoked。模型名称不写死，回退原因可展开。

## 评委入口

[启动物生.cmd](../../启动物生.cmd) → [start-wusheng.cmd](../../start-wusheng.cmd) → launch.ps1 → 必要时 setup.ps1 → start.ps1。检查 Python 3.12、Node.js，首次提示联网安装锁定依赖，默认 EvidenceProvider，尊重已有环境变量。不安装 Ollama、不下载大模型、不请求管理员权限、不修改防火墙。README 第一屏提供入口并明确禁止直接双击 frontend/index.html。

## 本轮实际验证

| 检查 | 结果 |
|---|---|
| 后端 pytest | **115 passed**，52.71 秒；0/1/2/10 件、增删改、封面优先级、缺失/过期/真实事件、Provider 三状态和现有完整业务回归 |
| Edge / Playwright | **34 passed**，147.50 秒；0 跳过、0 重试；[逐项 JSON](release-ui-results.json) |
| lint / TypeScript / Vite build | 通过，使用原锁定依赖，无新增依赖 |
| Windows smoke | PowerShell 解析、CMD 任意工作目录、中文与空格路径、隔离 Demo、单端口生产启动/health/generate/lan-ready 通过 |
| CMD 实际启动 | 从仓库外调用 `start-wusheng.cmd -NoBrowser -Smoke -Port 8020`，成功启动并仅停止本次服务 |
| 物品图片 | 10 张、6 布局、21 路由、**309 检查通过**；[报告](hd-images/verification.json) |
| 耗材图片 | 6 张、3 布局、20 路由、**107 检查通过**；[报告](consumable-images/verification.json) |
| 安全基础扫描 | 当前工作树和 22 个既有可达 Commit 无真实凭据命中；无用户路径、运行数据库/附件/模型等禁止文件，无单文件超过 5 MiB |

截图：[首页 1440](../references/home-1440.png)、[1920](../references/home-1920.png)、[1366](../references/home-1366.png)、[移动](../references/home-390.png)、[AI 助手](../references/assistant-1440.png)。首页与助手已实际目视检查。

本机 Node 24 的前两次整组执行发生开发服务中断（25/33、30/33）；日志没有给出根因，保留在 Git 忽略的本地 tmp。之后顺序执行整组 33/33、增加占位测试后再次 34/34，通过但不声称根因已彻底解决。推荐 Node 22 LTS，CI 使用 Node 22；生产入口不依赖 Vite 开发服务器。

Linux validate 与 Windows smoke 的最终状态以本轮提交对应的 [GitHub Actions](https://github.com/3331083641-prog/wusheng/actions/workflows/ci.yml) 为准，不能以旧 Tag 的绿色结果代替。没有修改或新建比赛 Tag。

## 未完成的人工验证

真实手机仍为 **Awaiting physical-device verification**，参照 [手机步骤](mobile_validation.md)。Ollama 三种 UI 状态使用明确标记的合成协议响应测试，本轮未重新运行真实大模型质量 Benchmark；不将模拟状态称为实机模型测试。模型权重不分发，未自动下载模型或调用付费 API。授权中文资料 Benchmark、LAN PWA 安装和浏览器关闭后的后台通知维持已有边界。

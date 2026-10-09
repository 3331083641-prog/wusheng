# 一物一码 V2.2 手机分享验收

范围：仅修复分享图片链路、手机只读档案、显式授权 PDF 与 LAN 说明。电脑首页 Hero、Sidebar、轮播、OCR、AI Provider 和数据库核心 Schema 均保持原实现；比赛 Tag 不移动。

## 图片根因与修复

打印机 Demo 的数据库封面是 `/assets/no-photo.svg`。桌面按 Item ID 兜底到正式高清图，而旧分享响应不携带 ID，手机 `resolveProductAsset(undefined, coverImage)` 无法兜底。其他 Demo 还使用 `/assets/laptop.jpg` 等旧路径。

正式资源清单提取为 `frontend/src/assets/itemAssets.json`，桌面 resolver 保持原结果，分享后端读取同一清单。顺序是：选定封面、当前物品的本体照片、合法 Demo ID 的正式资源、真正无图。打印机返回 `/assets/items/hp-printer.png`；不根据名称猜测。用户图片由 Token 保护接口读取，仅本体图片且必须属于同一物品。图片请求失败单独显示“照片暂时无法读取”，不是无图占位。

## 手机档案

`ShareItem.tsx` 与专用 `share-item.css`：中文品牌栏、等比封面/轻量相册、紧凑名称与状态、双列基本信息、保修与提醒、七阶段真实纵向生命周期、授权维护/维修、耗材、说明书、只读/LAN 页尾。

375/390/430px 截图使用隔离的合成 Demo，原始用户截图未提交：

- [375px](mobile-v22-375.png)
- [390px](mobile-v22-390.png)
- [430px](mobile-v22-430.png)

初始 HTML 和加载后 document title 均不含英文品牌词。刷新、重新聚焦、页面重新可见及可见时 30 秒轮询读取最新数据。隐藏页清除展示，访问失败清除旧资料。此机制不等于推送，另一个已打开页面须刷新/再次聚焦或等下一次轮询。

## 说明书权限与文件边界

管理端 `ShareOptions` 新权限均默认关闭，原二维码不增加权限。无需 Schema 迁移，沿用 `ShareLink.options` JSON：

| 配置 | 行为 |
|---|---|
| `showManualNames` | 仅公开当前说明书名称 |
| `showManualFiles` | 允许读取显式授权的 PDF |
| `manualDocumentIds` | 所有者选择当前物品的具体说明书 |
| `showManualDownloads` | 展示下载入口并允许 attachment 响应 |
| `shareFutureManuals` | 单独确认未来新增/替换上传文件持续共享 |
| 内部 `manualBaselineIds` | 记录授权当时存在的文件，持续授权不公开原先未选文件 |

后续文件仍来自正式 Document 表与本地磁盘。没有持续授权时，新 Document ID 默认私有；有持续授权时未来新增记录可读取，当前未选文件仍私有。修改范围需轮换令牌。选中文件被删除后列表消失，旧链接 404。

`GET /api/share-data/{token}/manuals/{document_id}/file` 每次验证令牌存在/未撤销/未过期、Item 仍存在、同物品、manual 类型、PDF MIME、文件授权、允许下载、磁盘存在与合法目录及 PDF 文件头。仅允许管理的 `documents/manuals/<itemId>` 或兼容旧 `uploads` 存储，路径穿越和跨物品读取被拒绝。

响应 `application/pdf`，UTF-8 原始文件名，inline 或明确授权的 attachment，`Cache-Control: no-store`、`X-Content-Type-Options: nosniff`、`Referrer-Policy: no-referrer`；支持 Range。Service Worker 仅缓存构建 JS/CSS，不缓存分享 JSON、图片或 PDF。资料目录不开放为静态目录，远程管理接口仍 403。

在线阅读无法阻止接收者保存内容，下载权限只控制产品入口与 attachment 模式。撤销只阻止后续服务访问，无法收回已下载副本；LAN HTTP 不具备 HTTPS 传输加密，仅应在可信私人网络使用。

## 隐私与动态一致性

价格、渠道、位置、库存、维护/维修记录、费用/详细备注均需单独授权。完整序列号、票据、发票、说明书全文和内部磁盘路径不会进入分享 JSON。生命周期只公开获准类别和日期，未来事件不当作完成记录。记录、图片、库存和 Document 都实时查询当前 Item，分享链接不保存第二套档案快照。

## 验证状态

日期：2026-10-09。所有测试使用独立临时数据，不上传用户运行数据库或附件，无新增依赖、模型或付费服务。

| 检查 | 本地实际结果 |
|---|---|
| 完整 pytest | **137 passed**；包含 22 个新增图片/PDF/隐私/动态关系与维护状态用例，另在不存在 frontend/dist 的环境完整重跑通过（70.66 秒） |
| 完整 Edge / Playwright | **42 passed**，0 跳过、0 重试；[逐项 JSON](release-ui-results.json)，新增 8 个手机档案用例 |
| 生产 LAN | 普通 `start.ps1 -NoBrowser`，使用真实非回环 LAN IP；分享 JSON、高清打印机 PNG、授权 PDF/下载 200，撤销后 PDF 404，原管理接口 GET/POST 403，真实 PNG QR 解码通过 |
| 原工程运行服务 | 重启原 `D:\wusheng` 服务后，已有打印机 Token 保持有效；LAN 分享 JSON 与高清 PNG 200、Content-Type 正确、初始标题中文、管理 API 403；旧码 PDF 权限仍关闭，没有轮换用户 Token |
| 手机尺寸 | 375/390/430px 无横向溢出，高清图 contain，无英文品牌标题；真实用户上传照片、相册切换/滑动、删封面兜底及真实无图通过 |
| lint / build | ESLint、TypeScript 与 Vite 生产构建通过，依赖锁未修改 |
| Windows smoke | 本地通过：PowerShell 解析、中文/空格目录 CMD、隔离健康/Demo、普通生产启动 health/generate/lan-ready；CI 另行执行同一 smoke |
| 正式图片回归 | 物品 10 张 / 309 项；耗材 6 张 / 107 项通过 |
| 文档 | 0 broken local links |
| 安全与数据保护 | 工作树基础凭据扫描无命中，无禁止公开文件或 >5MiB 文件；清理前 186 条已有记录均保留，数据库引用的本地文件哈希符合保存值 |
| Linux / Windows CI | [本轮 main 对应 GitHub Actions](https://github.com/3331083641-prog/wusheng/actions/workflows/ci.yml)，以此提交的运行结果为准 |

首轮浏览器为 40/42：模拟 Touch 未给必填 identifier，以及旧用例未显式指定无网络状态，与新增 LAN 测试环境假设冲突。补齐 Touch 参数并保留独立的无网络 UI 场景后，完整重跑 42/42。没有删除断言或用假 Toast 绕过功能。后端额外确认历史维护计划被新记录取代时，不误标为当前逾期任务。

首次 CI 在前端 build 之前执行 pytest，新增静态图片测试错误依赖本地已存在的 ignored `frontend/dist`，出现 10 个静态图片 404。图片单测改为显式使用 Vite 原样复制的 `frontend/public` 静态根目录，不跳过 HTTP/类型/PNG 校验；生产 `start.ps1` 的真实构建后 LAN 图片测试仍独立保留。

本地原服务更新时使用原 `data`，不重置数据库；测试仅在 `tmp` 下创建隔离资料。旧截图等回归生成物不替换原正式桌面截图；新手机图均来自合成 Demo。

**Awaiting physical-device verification**：旧版用户截图证明基础 LAN 可访问；V2.2 的图片、PDF、微信阅读及撤销仍待用户按 [手机测试步骤](mobile_validation.md)实测。

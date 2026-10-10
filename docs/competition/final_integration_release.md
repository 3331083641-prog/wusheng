# 最终整合验收（2026-10-10）

本轮范围：用户确认的三组最终素材、PDF 本地绑定、默认 AI 档案问答、Windows 物理网卡检测与二维码更新。其他七件素材和整体 UI 保持。实际本地验证结果见下文和 [机器可读验收记录](final-integration-validation.json)。

## 素材与本地数据

美的 KFR-35GW/N8KS1-1U、Philips HX6850、银色 TR-2001 的高清主图已通过统一映射用于首页、列表、详情、搜索、扫码和档案 PDF。三张四联图按纸张边界校正，替换 12 张独立资料；累计 40 张，保持合成演示标识。本体相册不混入票据。

空调、牙刷、行李箱 PDF 分别 36、72、1 页，本地正式存储，原始字节保留；累计八份用户提供的厂商资料，另有一份合成护理 PDF。厂商全文不进入 GitHub。绑定由用户确认，未重新审查产品适配关系。

迁移只修改三个可确认未编辑的 Demo，更新 12 个既有资料记录，新增可清洗空调滤尘网配件；六种核心耗材库存与消耗历史保持。重复迁移零新增。迁移前数据库及源码快照保存在本机 backups/final-integration-20261009，未删除旧数据库备份。

## AI 实现

默认 EvidenceProvider，不需要模型或密钥。维护日期先读数据库，说明书清单独立处理，刷头维护不会被库存分支抢走；清洁、维护、刷头更换与密码锁问题检索当前 PDF 的原文及页码。无对应文字明确说明不足，不从其他物品引用。锁具存在多种图示时提示打开原文件对照，不猜测具体结构。

Optional Local LLM 架构保持；本地服务不可用或调用失败回退。模型调用最长等待 20 秒，前端查询 30 秒超时可重试；切换物品会取消旧请求，避免回复进入新档案。实际 Provider 和每次回答是否调用模型继续准确显示。

## 一物一码修复

- Windows 使用活动物理网卡、网关和接口优先级选择 RFC1918 IPv4，排除 VMware、VPN、隧道与断开连接的网卡。
- 不再在检测失败时退回可能错误的虚拟网卡地址，提供重新检测与连接网络说明。
- 面板显示网卡与当前地址，返回页面及每 30 秒检查；IP/端口改变会清除旧二维码并明确要求重新生成。
- 地址未变时重新检测保留有效二维码；生成、复制、PNG 下载、轮换、撤销和过期机制保持。
- 管理 API 仍限回环，手机只读取 Token 范围内资料，PDF 指定文件/下载/未来授权独立。

软件侧局域网 HTTP 可验证服务、图片、JSON 和授权 PDF，不能替代手机与路由器/防火墙的实际连通性。没有自动修改防火墙或启动/下载模型。

## 手机实测

1. 双击根目录“启动物生.cmd”，保持电脑运行，手机与电脑连接可互通同一 Wi-Fi。
2. 在三件物品之一的“一物一码”中重新检测，确认 WLAN 或物理网卡的当前 IP。
3. 按需单独授权 PDF 和下载，生成新二维码，用手机系统浏览器打开。
4. 检查新主图、型号、保修、耗材和已授权 PDF；手机不能编辑物品。
5. 电脑撤销后刷新手机，旧分享及 PDF 应失效。换 Wi-Fi/IP 后重新生成二维码。

若无法连通，检查 Windows 可信私人网络允许 Python、路由器访客隔离和 VPN 对 LAN 的影响。详细记录表见 [手机验证](mobile_validation.md)。本次未虚称真实手机通过。

## 测试与发布

| 验证 | 实际结果 |
|---|---|
| pytest | 161 passed |
| Playwright 关键业务流程 | 47 passed |
| ESLint / TypeScript / Vite 正式构建 | 全部通过（Node 22.23.3） |
| 全部物品图片 / 耗材图片 | 309 / 121 项检查通过 |
| 三件正式档案的浏览器问答 | 3 × 9 = 27 次通过；真实 HTTP，EvidenceProvider，未调用模型 |
| 三份实际 PDF | 36 / 72 / 1 页；预览和下载 SHA256 与输入原件一致 |
| Windows | CMD 入口、不同工作目录、中文空格路径、PowerShell 启动通过 |
| 正式服务重启 | 再次通过启动入口，三份 PDF 和数据库绑定持久化 |
| 真实 LAN HTTP | 三组分享 SPA、图片、JSON、授权 PDF 返回 200 |
| 分享权限 | 远程管理 403；撤销/过期后的档案和 PDF 404 |
| SQLite | integrity_check=ok，foreign_key_check 无错误，原有业务字段/记录/分享授权保留 |
| 本地模型不可用 | 回退测试通过；未下载或启动模型 |
| 手机 | 已模拟窄屏页面；没有真实手机扫码测试 |

27 次问答覆盖身份、说明书清单、PDF 使用/维护、下次维护、保修、关联耗材、补充预测、维修记录和证据不足。牙刷实际引用 PDF 第 14 / 19 页，空调第 18 页，行李箱第 1 页；页码指 PDF 物理页。不把不足的历史强行生成补货日期，不推断未记录的维修或厂家更换周期。

首次 Node 24 浏览器回归时开发服务异常退出；根因未确认。最终使用 README 推荐的 Node 22 完成全部回归。首次新增二维码测试使用了错误的按钮名称，已修正为界面真实名称后重跑通过，未删除断言。

### 当前正式页面截图

| 物品 | 主图与独立凭证 | 已绑定 PDF | 实际 AI Provider |
|---|---|---|---|
| 美的空调 | [截图](final-ac-1440.png) | [截图](final-ac-manual-1440.png) | [截图](final-ac-assistant-1440.png) |
| 飞利浦牙刷 | [截图](final-toothbrush-1440.png) | [截图](final-toothbrush-manual-1440.png) | [截图](final-toothbrush-assistant-1440.png) |
| 银色行李箱 | [截图](final-suitcase-1440.png) | [截图](final-suitcase-manual-1440.png) | [截图](final-suitcase-assistant-1440.png) |

首页、我的物品、提醒、耗材、维修、统计、建档和手机只读页均纳入完整浏览器回归。资料上传/删除、物品增改删、PDF 阅读、维护编辑、库存消耗撤销、PDF 档案导出和备份恢复实际执行于隔离测试数据库，未用正式档案制造测试记录。

### 清理与保护

删除前确认运行代码及正式数据库均无引用，以下六个旧资源已删除，Git 历史和迁移前源码快照仍可恢复：

- frontend/public/assets/items/midea-air-conditioner.png
- frontend/public/assets/items/philips-electric-toothbrush.png
- frontend/public/assets/items/rimowa-suitcase.png
- frontend/public/assets/consumables/click-on-brushheads-v3.png
- frontend/public/assets/demo-evidence/ac-invoice.png
- frontend/public/assets/demo-evidence/toothbrush-invoice.png

自动审批拒绝批量递归清理临时克隆、依赖缓存和测试目录，理由仅为“blocked by policy”。因此这些临时目录保留在本机 tmp，不纳入 Git。历史截图保留作版本记录，旧验收页已标明历史版本并指向当前报告。

保留 data/wusheng.db、全部用户图片/PDF、既有附件、唯一素材母版、所有数据库备份、配置和许可证、Git 历史及 Tag。新增源码和数据库快照仅一组 backups/final-integration-20261009。其他七件图片未改。公开仓库不新增厂商 PDF 全文、数据库、密钥、权重、依赖或私人资料。

### GitHub

代码正常提交与推送到 main；不 force push。最终 SHA 与真实 Linux / Windows CI 链接在发布完成时记录。

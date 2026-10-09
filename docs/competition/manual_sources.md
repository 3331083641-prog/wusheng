# 本地说明书来源与适用范围

2026-10-09：对用户提供的 8 份 PDF 逐页提取文本并核对型号。5 份可绑定新版 Demo，3 份不匹配。不通过改文件名伪装适配；未执行厂商数字签名／原件鉴证。厂商完整 PDF 仅存本机 data/documents/manuals，不上传公开 GitHub。

| Item | 本地提供文件 | 页数 | 处理与适用范围 |
|---|---|---|---|
| laptop | Apple MacBook Air M2说明书.pdf | 2 | A2681 安全、操作及监管资料，不是完整操作手册；中文 |
| headphones | 耳机说明书.pdf | 149 | WH-1000XM6 / YY2984；法文帮助指南；保留可空密码阅读的原始受限 PDF 字节 |
| washer | 未提供 | — | 尚未上传精确匹配 EG100MATE8S 说明书 |
| ac | 空调说明书.pdf | 36 | Midea KFR-35GW/N8KS1-1U 等，不绑定武圣 WSKFR-26GW/BP3；匹配说明书缺失 |
| robot | 小米扫地机器人说明书.pdf | 459 | S10 / B106GL，多语言，绑定；图内合成铭牌不能替代此参数来源 |
| coffee | 未提供 | — | 尚未上传已核实匹配 EC680.S 说明书；不借用 EC685 PDF |
| toothbrush | 牙刷说明书.pdf | 72 | ProtectiveClean 4500/5100，不绑定 HX3671/13；匹配说明书缺失 |
| suitcase | 行李箱说明书.pdf | 1 | RIMOWA 锁具资料，不绑定通用 TR-2001；匹配说明书缺失 |
| purifier | 小米空气净化器说明书.pdf | 32 | Smart Air Purifier 4 / AC-M16-SC；英文、繁体中文等；绑定 |
| printer | 打印机说明书.pdf | 126 | HP DeskJet2700系列英文指南；适用2720系列操作，地区墨盒需单独确认 |

不匹配的 3 份原件保留在用户输入位置，未写入物品说明书表、未公开。当地已有旧 PDF 如因型号迁移需复核，保留物理文件与记录，标记 reference_pending，禁止 AI／扫码当作已匹配说明书。原有“Demo 耳机护理说明（非官方）”为项目生成测试资料，独立保留，不能冒充真实厂商 PDF。

## 复现与后续上传

冷克隆只包含项目合成护理 PDF，不包含这 5 份受厂商权利约束的全文。用户自行提供合法原件后，在物品详情“说明书”上传，或先执行 `python scripts/import_demo_manuals.py --source-dir <输入目录> --dry-run` 再 `--apply`；导入器逐次核对当前 Demo 身份、文件文本及 SHA256，使用正式 PDF 验证／文件事务，不重复导入、不自动增加 QR 权限。原名、原字节、页数、大小、语言、适用范围与来源登记在本地 Document 中。

正常支持阅读、下载、删除、重启持久化、文本提取和按当前物品引用。真正需要密码的 PDF 仍拒绝；仅允许无需密码即可阅读的受限原件，保留其限制，不解除或改写文件。分享具体 PDF、下载与未来新增文件授权各自独立，默认关闭；撤销／过期／删除后 Token 文件入口失效。

## 厂商检索入口

- [Apple MacBook Air M2 文档](https://support.apple.com/en-gb/docs/mac/300872)
- [Sony WH-1000XM6 法文帮助指南](https://helpguide.sony.net/mdr/2984/v1/fr/index.html)
- [小米 S10](https://www.mi.com/global/product/xiaomi-robot-vacuum-s10/)
- [小米 Air 4](https://www.mi.com/global/product/xiaomi-smart-air-purifier-4/)
- [HP DeskJet2700系列指南](https://support.hp.com/us-en/product/setup-user-guides/hp-deskjet-2700e-all-in-one-series/29378157)

这里只登记检索来源，不宣称本地每份文件经过厂商签名鉴证。身份及耗材冲突见 [素材审核](asset_audit.md)。

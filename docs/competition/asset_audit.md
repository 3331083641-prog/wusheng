# 最终 Demo 素材登记（2026-10-10）

本轮直接采用用户确认的空调、牙刷、行李箱最终素材，只检查图片/PDF 能否读取，不重新审查品牌、外观或 PDF 适配关系。其他七件物品的身份与素材保持原样。所有物品图及配套购买资料为 AI 合成演示，不证明真实购买、厂商认证或保修资格。

## 当前身份和主图

| ID | 本轮之前型号 | 当前演示身份 | 统一图片映射 |
|---|---|---|---|
| laptop | 13.6 英寸 256GB | MacBook Air M2 · Apple · A2681 · M2 · 13.6 英寸 256GB | `/assets/items/macbook-air-m2.png` |
| headphones | WH-1000XM6 | Sony WH-1000XM6 · Sony · WH-1000XM6 | `/assets/items/sony-wh1000xm6.png` |
| washer | EG100MATE8S | 海尔滚筒洗衣机 · Haier · EG100MATE8S | `/assets/items/haier-washer-v3.png` |
| ac | WSKFR-26GW/BP3 | 美的空调 · Midea · KFR-35GW/N8KS1-1U | `/assets/items/midea-ac-final.png` |
| robot | S10 | 小米扫地机器人 S10 · Xiaomi · S10 · B106GL | `/assets/items/xiaomi-robot-vacuum.png` |
| coffee | EC685 | 德龙半自动意式咖啡机 · DeLonghi · EC680.S | `/assets/items/delonghi-ec680-illustration.png` |
| toothbrush | HX3671/13 | 飞利浦电动牙刷 · Philips · HX6850 | `/assets/items/philips-toothbrush-final.png` |
| suitcase | TR-2001 | 20英寸旅行行李箱 · 通用演示品牌 · TR-2001 | `/assets/items/silver-suitcase-final.png` |
| purifier | Air 4 | 小米空气净化器4 · Xiaomi · Air 4 · AC-M16-SC | `/assets/items/xiaomi-air-purifier-4-v3.png` |
| printer | DeskJet 2720 | 惠普打印机 · HP · DeskJet 2720 | `/assets/items/hp-printer.png` |

平台名称仍为物生 Wusheng。空调 Demo 已由武圣改为美的，牙刷由 HX3671/13 改为 HX6850；通用 TR-2001 行李箱使用用户最新银色主图。三组 PDF 的绑定由用户最终确认，不根据 PDF 中的其他标识修改物品身份。

## 配套资料

累计 10 张母版、40 张独立 PNG，本轮只替换三张母版和对应 12 张裁剪图。每张按纸张四角透视校正，保留文字、印章、图案与纸张边缘；没有四等分、改字或补造字段。

| 物品 | 本轮四份独立资料 |
|---|---|
| 美的空调 | manual_image / receipt（模拟购买记录）/ warranty_card（演示服务摘要）/ label |
| 飞利浦牙刷 | manual_image / receipt（示意购买记录）/ warranty_card / package |
| 银色行李箱 | manual_image / invoice（模拟发票）/ warranty_card / label |

母版保存在 [原图目录](../references/demo-materials/originals/)。原图 SHA256、四角坐标、裁剪尺寸、文件 SHA256、所属物品、资料类型、合成标识与 owner-confirmed 来源见 [机器清单](../../backend/demo_materials.json)。资料只进入“凭证资料”，顶部相册只有本体图片；说明书照片不会成为 PDF。

这三组展示“用户确认资料”及“合成演示资料 · 非真实购物凭证”。此前七件的审核限制仍沿用原登记，不把其合成参数当成官方事实。

## 耗材和配件

保留六种核心耗材及其既有库存/消耗历史；另外按用户新提供的图片加入可清洗空调滤尘网配件。该配件初始备用库存为 0，没有虚构消耗、购买或补货历史，不据此预测固定更换周期。

| ID | 关联设备 | 素材处理 |
|---|---|---|
| purifier-filter | 小米 Air 4 | 保持既有滤芯图和适配说明 |
| detergent | 海尔洗衣机 | 保持蓝月亮图和库存 |
| ink-cartridge | HP2720 | 保持既有图和地区适配说明 |
| capsules | EC680.S | 保持 E.S.E. 易理包图和历史 |
| brushhead | Philips HX6850 | 替换为用户最新单个卡入式刷头原图 |
| robot-filter | 小米 S10 | 保持机器人滤网原图 |
| ac-filter | 美的空调 | 新增用户提供的白色弧形空调滤尘网图 |

本轮五张主体/配件 PNG 均按原始字节保存，无缩放压缩、重绘或改色。页面使用 contain 保持产品完整。原始名称、SHA256 与尺寸见 [物品图片](../references/hd-image-assets.json) 和 [耗材图片](../references/consumable-image-assets.json)。

## 安全迁移与复现

已有上一版 Demo 可运行 `python scripts/migrate_final_materials.py --dry-run`，再 `--apply`。普通 Windows 启动也会执行这一安全迁移。只处理 isDemo=True 的三个稳定 ID，要求身份、备注、序列号、编辑时间和既有合成资料指纹符合已知种子；用户编辑或不明确的记录保留并报告。事务失败回滚，一份迁移前备份位于 backups/final-integration-20261009/before.db；重复执行不写入附件、不恢复用户已删除的资料。

新数据库直接使用当前种子，旧版最初种子另有 `migrate_demo_assets.py`。价格、购买日期、保修期限、用户照片/PDF、维护维修与六种耗材历史不由合成票据覆盖。厂商 PDF 只保存在本地，不分发全文，见 [来源登记](manual_sources.md)。

裁剪可复现：`python scripts/prepare_demo_materials.py --source-dir <最终素材目录> --items ac toothbrush suitcase --replace`。用户的原始文件名登记在 demo_catalog.json；只重建三组，另外七组原样保留。

完整功能和真实手机验证边界见 [最终整合验收](final_integration_release.md)。

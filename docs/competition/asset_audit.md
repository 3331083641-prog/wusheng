# Demo 素材一致性审核（2026-10-09）

本轮以用户最新配套图统一内置合成 Demo 身份，不代表识别模型自动判定。未提供替换素材的图片文件保持原样。合成空调武圣 WUSHENG 与平台物生是不同名称；未核实真实在售产品。TR-2001 不归属 RIMOWA。照片及票据均为用户提供的 AI 生成示意，不构成厂商认证、商品精确外观或真实购买证据。

## 身份与主图

| ID | 修改前 | 新版身份 | 主图 |
|---|---|---|---|
| laptop | Apple 13.6 英寸 256GB | MacBook Air M2 · Apple · A2681 · M2 · 13.6 英寸 256GB | /assets/items/macbook-air-m2.png |
| headphones | Sony WH-1000XM6 | Sony WH-1000XM6 · Sony · WH-1000XM6 | /assets/items/sony-wh1000xm6.png |
| washer | Haier EG100MATE8S | 海尔滚筒洗衣机 · Haier · EG100MATE8S | /assets/items/haier-washer-v3.png |
| ac | Midea KFR-35GW | 武圣壁挂式空调 · 武圣 WUSHENG · WSKFR-26GW/BP3 | 待补，旧文件不改动、不再绑定 |
| robot | Xiaomi S10 | 小米扫地机器人 S10 · Xiaomi · S10 · B106GL | /assets/items/xiaomi-robot-vacuum.png |
| coffee | DeLonghi EC685 | 德龙半自动意式咖啡机 · DeLonghi · EC680.S | /assets/items/delonghi-ec680-illustration.png |
| toothbrush | Philips HX6850 | 飞利浦 HX3671/13 电动牙刷 · Philips · HX3671/13 | 待补，旧文件不改动、不再绑定 |
| suitcase | RIMOWA Original Cabin | 20英寸旅行行李箱 · 通用演示品牌 · TR-2001 | 待补，旧文件不改动、不再绑定 |
| purifier | Xiaomi Air 4 | 小米空气净化器4 · Xiaomi · Air 4 · AC-M16-SC | /assets/items/xiaomi-air-purifier-4-v3.png |
| printer | HP DeskJet 2720 | 惠普打印机 · HP · DeskJet 2720 | /assets/items/hp-printer.png |

MacBook、Sony、机器人及 HP 原图保持。洗衣机、咖啡机、净化器只使用本轮提供的新图。带 Midea 标识的空调图与带多个清洁模式的牙刷图不匹配新版型号，不绑定。没有提供独立通用行李箱主图，原 RIMOWA 图文件保留，但不再冒充 TR-2001。三项匹配主图仍未完成，页面显示占位及待补说明；没有自动生成新图片。

## 10 张配套图：40 份独立裁剪

母版在 [originals](../references/demo-materials/originals/)，完整 SHA256、四角边界、尺寸和来源在 [机器清单](../../backend/demo_materials.json)。[裁剪脚本](../../scripts/prepare_demo_materials.py)按照完整纸张实际边界逐张透视校正，保留边缘余量，没有机械四等分、改字、补造字段。主相册仅含物品封面和 product 照片；下列资料归入凭证资料卡，统一标注“合成演示资料 · 非真实购物凭证”。

| 物品 | 裁剪分类 | 数量 | 审核限制 |
|---|---|---|---|
| laptop | manual_image / invoice / warranty_card / label | 4 | A2681、M2；随机序列号与购买信息不作证据 |
| headphones | manual_image / invoice / warranty_card / label | 4 | WH-1000XM6；保修政策文字不作真实资格依据 |
| washer | manual_image / invoice / warranty_card / label | 4 | EG100MATE8S；金额及合成铭牌参数不写入业务字段 |
| ac | manual_image / invoice / warranty_card / label | 4 | 合成品牌／型号；厂家、能效与售后承诺均未核实 |
| robot | manual_image / invoice / warranty_card / label | 4 | S10/B106GL 可对应；铭牌 5200mAh/55W/14.4V 与官方 3200mAh/45W/14.8V 冲突，modelVerified=false |
| coffee | manual_image / invoice / warranty_card / label | 4 | EC680 为系列，发票／铭牌 EC680.S；合成税额不覆盖数据库 |
| toothbrush | manual_image / invoice / warranty_card / package | 4 | HX3671/13；封面 Series 3100；包装不当作本体照片 |
| suitcase | manual_image / invoice / warranty_card / label | 4 | 通用 TR-2001；无厂商核验；发票品牌／电话／网站不作真实来源 |
| purifier | manual_image / invoice / warranty_card / other | 4 | Air 4/AC-M16-SC；滤芯四色规格表未核实，不作兼容性依据 |
| printer | manual_image / invoice / warranty_card / other | 4 | DeskJet2720；HP67 合成信息仅为演示，地区适配待核实 |

modelVerified 仅表示图内身份一致性审核完成，不等于票据真实、参数正确或厂商鉴证。说明书封面照片不是电子 PDF。原图不修改，母版保留。

## 六类耗材

| ID | 名称／关联物品 | 兼容性与图片处理 |
|---|---|---|
| purifier-filter | 空气净化器滤芯 / Air 4 | 官方 M16R-FLP-GL，Φ210×293mm；本轮圆筒图无尺寸，适配性待核实 |
| detergent | 蓝月亮洗衣液 / 海尔 | 机洗用量按包装；无同品牌限制；使用本轮白底蓝月亮图 |
| ink-cartridge | 打印机墨盒 / HP2720 | 67、805、305 依地区；本轮805示意标签料号不符，不能据图购买 |
| capsules | E.S.E. 咖啡易理包 / EC680.S | 44mm E.S.E.，需对应滤篮，单位由颗改包，原库存与消耗数值不变 |
| brushhead | 电动牙刷刷头 / HX3671/13 | 卡入式接口；图中无 SKU，适配性待核实 |
| robot-filter | 扫地机器人滤网 / S10 | 官方 B106GL-LW；本轮网片图是空调滤网，不替换既有机器人滤网图，具体尺寸适配待核实 |

5 张新耗材图只将与外边缘连通的近白中性色背景标准化为 RGB(255,255,255)，不改文字、产品内部颜色及比例。原始文件在本机备份中保留；转换来源与 SHA256 见 [登记](../references/consumable-assets-v3.json)。不能以 AI 包装图保证产品结构或料号正确。

## 可回滚迁移

先运行 `python scripts/migrate_demo_assets.py --dry-run`，再运行 `--apply`。默认只预览；应用前 SQLite 在线备份到项目 backups/assets-v3。只升级 isDemo=True 的稳定 ID，且原始身份、备注、序列号指纹和编辑时间均吻合。疑似人工改过则保留整件档案并报告。事务失败回滚；不改购买日期、金额、保修、状态和用户封面，不删除历史记录。稳定附件 ID 避免重复；迁移版本标记避免再次导入用户已删除资料。

已有旧型号 PDF 不删除：标记待复核参考资料，退出 AI 与扫码说明书列表，保留本地文件和管理阅读入口。新厂商 PDF 使用显式本地导入，不随冷克隆分发、不自动授权分享。元数据为 ItemImage/Document 可空 JSON 增量字段，兼容旧备份。

## 来源与边界

- [Apple M2/A2681 技术规格](https://support.apple.com/ko-kr/111867)
- [小米 S10 配件与 B106GL-LW](https://www.mi.com/cz/product/xiaomi-robot-vacuum-s10-accessories/specs/)
- [小米 Air 4 滤芯 M16R-FLP-GL](https://www.mi.com/global/product/xiaomi-smart-air-purifier-4-filter/specs/)
- [德龙 EC680 与 44mm E.S.E. 配套滤篮](https://www.delonghi.com/it-it/faqs/Macchine-espresso/a/2591)
- [飞利浦 HX3671/13 卡入式刷头](https://www.philips.co.uk/shop/UK_Klarna/personal-care/electric-toothbrushes/sonicare-3100-series-sonic-electric-toothbrush/p/HX3671_13)
- [HP2720 7FR56D 805 地区规格](https://support.hp.com/py-es/document/c08785080)、[HP67 支持列表](https://www.hp.com/py-es/products/ink-toner/product-details/31129588)

实际手机与电脑必须处于可互通同一局域网，电脑保持运行；自动化不等于真实手机实测。AI 默认 EvidenceProvider，不下载模型，不调用付费 API。本轮不提高或宣称 OCR／AI 准确率。完整测试及剩余事项见 [交付记录](demo_assets_release.md)。

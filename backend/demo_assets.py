"""Reviewed Demo provenance, shared by seed, migration and presentation.

No filename/name guesses and no mutation on reads. User archives are never Demo.
"""
import json
from pathlib import Path
from sqlalchemy import select
from . import models as m

HERE=Path(__file__).resolve().parent
CATALOG=json.loads((HERE/'demo_catalog.json').read_text(encoding='utf-8'))
MATERIALS=json.loads((HERE/'demo_materials.json').read_text(encoding='utf-8'))
OLD_DESCRIPTION='合成 Demo 档案 · 用于展示真实数据流，不代表真实购买。'
CONSUMABLES={
 'brushhead':('toothbrush','电动牙刷刷头','电动牙刷刷头','卡入式接口已核实；本图无具体刷头 SKU，适配性待核实'),
 'purifier-filter':('purifier','空气净化器滤芯','空气净化器滤芯','Air 4 官方滤芯 M16R-FLP-GL，直径 210mm、高 293mm；合成图无尺寸，适配性待核实'),
 'capsules':('coffee','咖啡胶囊','E.S.E. 咖啡易理包','EC680 系列支持 44mm E.S.E. 易理包，需使用对应滤篮；不是胶囊'),
 'ink-cartridge':('printer','打印机墨盒','打印机墨盒','HP 67／805／305 依销售地区不同；合成图标签料号有误，适配性待核实'),
 'detergent':('washer','洗衣液','蓝月亮洗衣液','按洗衣液包装的机洗用量使用；无需与洗衣机同品牌'),
 'robot-filter':('robot','扫地机器人滤网','扫地机器人滤网','官方 S10 滤网型号 B106GL-LW；现有示意图无尺寸，适配性待核实')
}
def matches(item):
    entry=CATALOG.get(item.id)
    return bool(item.isDemo and entry and all(getattr(item,k)==v for k,v in entry['new'].items()))

def identity_note(item):
    return CATALOG[item.id]['identityNote'] if matches(item) else ''

def consumable_note(db,c):
    entry=CONSUMABLES.get(c.id)
    item=db.get(m.Item,c.itemId)
    return entry[3] if entry and item and matches(item) and c.itemId==entry[0] and c.name==entry[2] else ''

def add_materials(db,item):
    if not matches(item):return 0
    count=0
    for asset in MATERIALS:
        if asset['itemId']!=item.id:continue
        # Stable provenance ID: reruns do not re-add or duplicate attachments.
        ident=f"demo-v3-{item.id}-{asset['type']}"
        if db.get(m.ItemImage,ident):continue
        db.add(m.ItemImage(id=ident,itemId=item.id,filePath=asset['path'],type=asset['type'],source='synthetic-demo-v3',
            originalFilename=asset['path'].split('/')[-1],mimeType='image/png',sha256=asset['sha256'],
            fileSize=(HERE.parent/'frontend/public'/asset['path'].lstrip('/')).stat().st_size,assetMetadata=asset))
        count+=1
    return count

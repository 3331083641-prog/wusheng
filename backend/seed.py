"""Synthetic, clearly marked fixture. Never resets or overwrites a used database."""
from datetime import timedelta
from sqlalchemy import select
from . import models as m
from .clock import today
from .database import uid,UPLOADS
from .lifecycle import add_months,sync_all,event,next_maintenance
from .demo_assets import CATALOG, CONSUMABLES, OLD_DESCRIPTION, add_materials


def seed(db):
    if db.scalar(select(m.Item.id).limit(1)):
        return False
    now=today()
    records=[('laptop','数码',8999,12,-6,'书房'),('headphones','数码',2999,24,-9,'客厅'),('washer','家电',3299,12,-18,'阳台'),('ac','家电',2899,36,-24,'客厅'),('robot','家电',1699,12,-4,'客厅'),('coffee','家电',1599,12,-11,'厨房'),('toothbrush','数码',399,12,-5,'浴室'),('suitcase','家居',1200,24,-14,'储物间'),('purifier','家电',999,12,-14,'卧室'),('printer','数码',599,12,-10,'书房')]
    for ident,category,price,months,offset,location in records:
        img=ident
        item=m.Item(id=ident,**CATALOG[ident]['new'],category=category,purchasePrice=price*100,purchaseDate=add_months(now,offset).isoformat(),purchaseChannel='合成演示购买渠道',serialNumber=f'WS-DEMO-{ident.upper()}',warrantyMonths=months,returnWindowDays=7,location=location,coverImage=f'/assets/{img}.jpg',isDemo=True,description=OLD_DESCRIPTION)
        version='final-materials-v4' if ident in ('ac','toothbrush','suitcase') else 'demo-assets-v3'
        item.description=OLD_DESCRIPTION+'\n'+CATALOG[ident]['identityNote']+'\n素材版本：'+version
        if ident == 'printer': item.coverImage = '/assets/no-photo.svg'  # Explicit photo empty state.
        db.add(item)
    db.flush()
    for item in db.scalars(select(m.Item)):
        add_materials(db,item)
    db.add(m.ItemImage(itemId='headphones',filePath='/assets/headphones-detail.jpg',type='product',source='user-design-reference'))
    for ident,interval,last in [('headphones',60,30),('washer',90,92),('ac',120,118),('robot',30,25),('coffee',45,40)]:
        day=now-timedelta(days=last)
        record=m.MaintenanceRecord(id=uid(),itemId=ident,type='清洁维护',date=day.isoformat(),intervalDays=interval,nextDueDate=next_maintenance(day,interval).isoformat(),description='合成演示维护记录；周期为用户示例设置，不是厂家说明。',cost=0)
        db.add(record)
        event(db,ident,'maintenance',day,'清洁维护',record.id,source='demo')
    for ident,issue,status,cost,days in [('washer','脱水时出现异响','诊断中',0,2),('headphones','左侧耳罩磨损','已完成',18000,70),('coffee','出水口渗漏','已完成',12000,40)]:
        day=(now-timedelta(days=days)).isoformat()
        repair=m.RepairRecord(id=uid(),itemId=ident,issue=issue,reportDate=day,status=status,serviceType='官方售后',cost=cost,description='合成 Demo 服务记录',completionDate=day if status=='已完成' else None,progress=[{'status':'待预约','date':day},{'status':status,'date':day}])
        db.add(repair)
        event(db,ident,'repair',day,issue,repair.id,source='demo')
    settings=[('brushhead','toothbrush','电动牙刷刷头','个',2,1,7,60,4),('purifier-filter','purifier','空气净化器滤芯','个',1,1,7,60,5),('capsules','coffee','咖啡胶囊','颗',24,6,5,30,26),('ink-cartridge','printer','打印机墨盒','个',1,1,7,60,3),('detergent','washer','洗衣液','升',1,0.3,5,30,2),('robot-filter','robot','扫地机器人滤网','个',2,1,7,60,1)]
    for ident,item,name,unit,stock,warning,lead,window,used in settings:
        img={'purifier-filter':'filter','ink-cartridge':'ink','robot-filter':'filter'}.get(ident,ident)
        c=m.Consumable(id=ident,itemId=item,name=name,unit=unit,currentStock=stock,warningStock=warning,leadDays=lead,coverImage=f'/assets/{img}.jpg')
        c.name=CONSUMABLES[ident][2]
        if ident=='capsules':c.unit='包'
        db.add(c)
        db.flush()
        db.add(m.ConsumptionRecord(consumableId=ident,date=(now-timedelta(days=window)).isoformat(),quantityUsed=0))
        for i in range(1,6):
            db.add(m.ConsumptionRecord(consumableId=ident,date=(now-timedelta(days=window-int(window*i/5))).isoformat(),quantityUsed=used/5))
        db.add(m.RestockRecord(consumableId=ident,date=(now-timedelta(days=20)).isoformat(),quantity=stock+used,cost=18000 if ident=='purifier-filter' else 6000))
    # Owner-supplied washable accessory: no invented purchase/consumption history.
    db.add(m.Consumable(id='ac-filter',itemId='ac',name='空调滤尘网',unit='个',currentStock=0,warningStock=0,leadDays=7,coverImage='/assets/consumables/ac-dust-filter-final.png'))
    # Generated demonstration manual, not an official Sony manual.
    from reportlab.pdfgen import canvas
    path=UPLOADS/'demo-care-guide.pdf'
    pdf=canvas.Canvas(str(path))
    pdf.drawString(45,780,'WUSHENG DEMO CARE GUIDE - NOT A MANUFACTURER MANUAL')
    pdf.drawString(45,740,'Clean the ear pads using a soft, dry cloth every 60 days (demo rule).')
    pdf.drawString(45,710,'Do not disassemble the device. Contact professional service if needed.')
    pdf.save()
    from pypdf import PdfReader
    db.add(m.Document(itemId='headphones',filename='Demo 耳机护理说明（非官方）.pdf',filePath='/uploads/demo-care-guide.pdf',extractedText='\n'.join(p.extract_text() or '' for p in PdfReader(path).pages)))
    db.flush()
    sync_all(db)
    return True

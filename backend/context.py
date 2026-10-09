from sqlalchemy import select
from . import models as m
from .serializers import row,item_data
from .lifecycle import consumable_data


class ContextBuilder:
    def build(self,db,item):
        return {'lifecycle': [{'date': e.date, 'title': e.title} for e in db.scalars(select(m.LifecycleEvent).where(m.LifecycleEvent.itemId==item.id).order_by(m.LifecycleEvent.date))], 'item':item_data(db,item),'manuals':[row(r) for r in db.scalars(select(m.Document).where(m.Document.itemId==item.id))], 'maintenance':[row(r) for r in db.scalars(select(m.MaintenanceRecord).where(m.MaintenanceRecord.itemId==item.id).order_by(m.MaintenanceRecord.date.desc()))], 'repairs':[row(r) for r in db.scalars(select(m.RepairRecord).where(m.RepairRecord.itemId==item.id).order_by(m.RepairRecord.reportDate.desc()))], 'consumables':[consumable_data(db,r) for r in db.scalars(select(m.Consumable).where(m.Consumable.itemId==item.id))]}


def lifecycle_suggestions(context):
    item=context['item']
    output=[]
    if context['maintenance']:
        latest=context['maintenance'][0]
        output.append(f"上次{latest['type']}为 {latest['date']}，按已保存 {latest['intervalDays']} 天周期，下次为 {latest['nextDueDate']}。")
    else:
        output.append('尚未保存维护周期。请先依据说明书确认周期，再建立维护记录。')
    days=item['warrantyDaysLeft']
    if days is not None and days>=0:
        output.append(f'仍在保修期内（剩余 {days} 天）。如有异常，请保留故障记录和购买凭证，并优先联系官方售后。')
    if item.get('isDemo'):
        output.insert(0,'合成演示档案；日期和保修仅用于演示，不证明实际购买或保修资格。'+item.get('identityNote',''))
    if context['repairs']:
        output.append(f"已记录 {len(context['repairs'])} 次报修；最近的问题为“{context['repairs'][0]['issue']}”。")
    for c in context['consumables']:
        if c['estimatedDaysLeft'] is not None:
            output.append(f"{c['name']}按历史消耗预计可用 {c['estimatedDaysLeft']} 天，建议 {c['suggestedPurchaseDate']} 补给。")
    return output

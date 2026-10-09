from calendar import monthrange
from datetime import date, timedelta
from sqlalchemy import select, delete
from . import models as m
from .clock import today
from .consumptionPrediction import consumption_prediction


def add_months(day, months):
    index = day.year*12+day.month-1+months
    year, month = divmod(index, 12)
    return date(year, month+1, min(day.day, monthrange(year, month+1)[1]))


def warranty_end(purchase_date, months):
    return add_months(purchase_date, months) if months else None


def return_deadline(purchase_date, days):
    return purchase_date+timedelta(days=days) if days else None


def next_maintenance(day, interval_days):
    return day+timedelta(days=interval_days)


def event(db, item_id, kind, day, title, related_id, description='', source='engine'):
    existing = db.scalar(select(m.LifecycleEvent).where(m.LifecycleEvent.itemId==item_id,m.LifecycleEvent.type==kind,m.LifecycleEvent.relatedId==related_id))
    if existing:
        existing.date=str(day)
        existing.title=title
        existing.description=description
    else:
        db.add(m.LifecycleEvent(itemId=item_id,type=kind,date=str(day),title=title,relatedId=related_id,description=description,source=source))


def consumable_data(db, consumable, as_of=None):
    from .serializers import row
    from .demo_assets import consumable_note
    as_of = as_of or today()
    records = [row(r) for r in db.scalars(select(m.ConsumptionRecord).where(m.ConsumptionRecord.consumableId==consumable.id).order_by(m.ConsumptionRecord.date))]
    prediction = consumption_prediction(consumable.currentStock, records, as_of, consumable.leadDays)
    left = prediction['estimatedDaysLeft']
    status = '即将耗尽' if consumable.currentStock<=0 or (left is not None and left<=7) else '建议补货' if consumable.currentStock<=consumable.warningStock or (left is not None and left<=consumable.leadDays+7) else '数据不足' if left is None else '正常'
    return {**row(consumable),**prediction,'compatibilityNote':consumable_note(db,consumable),'status':status,'records':records,'restocks':[row(r) for r in db.scalars(select(m.RestockRecord).where(m.RestockRecord.consumableId==consumable.id).order_by(m.RestockRecord.date))]}


def sync_item(db, item, as_of=None):
    """Idempotent reconciliation. User snoozes and completion survive reads."""
    as_of = as_of or today()
    purchase = date.fromisoformat(item.purchaseDate)
    expiry = warranty_end(purchase,item.warrantyMonths)
    deadline = return_deadline(purchase,item.returnWindowDays)
    item.warrantyEndDate=expiry.isoformat() if expiry else None
    item.returnDeadline=deadline.isoformat() if deadline else None
    db.flush()
    event(db,item.id,'purchase',purchase,'购买建档','purchase',source='user' if not item.isDemo else 'demo')
    if deadline and deadline<=as_of:
        event(db,item.id,'return',deadline,'退换期结束','return')
    else:
        db.execute(delete(m.LifecycleEvent).where(m.LifecycleEvent.itemId==item.id,m.LifecycleEvent.relatedId=='return'))
    if expiry and expiry<=as_of:
        event(db,item.id,'warranty',expiry,'保修期结束','warranty')
    else:
        db.execute(delete(m.LifecycleEvent).where(m.LifecycleEvent.itemId==item.id,m.LifecycleEvent.relatedId=='warranty'))
    event(db,item.id,'use',purchase,'开始使用','use')
    plans=[]
    if item.status in ['淘汰','转卖','回收']:
        if not db.scalar(select(m.LifecycleEvent.id).where(m.LifecycleEvent.itemId==item.id,m.LifecycleEvent.relatedId=='retired')):
            event(db,item.id,'retired',as_of,item.status,'retired')
    else:
        if deadline and deadline>=as_of:
            plans.append(('退换截止','退换期限将结束',deadline,'return'))
        if expiry and expiry>=as_of:
            plans.append(('保修到期','保修期限将结束',expiry,'warranty'))
        maintenance = list(db.scalars(select(m.MaintenanceRecord).where(m.MaintenanceRecord.itemId==item.id).order_by(m.MaintenanceRecord.date.desc(),m.MaintenanceRecord.id.desc())))
        latest={}
        for record in maintenance:
            if record.type not in latest:
                latest[record.type]=record
                plans.append(('维护任务',record.type,date.fromisoformat(record.nextDueDate),record.id))
        for c in db.scalars(select(m.Consumable).where(m.Consumable.itemId==item.id)):
            predicted=consumable_data(db,c,as_of)
            if predicted['suggestedPurchaseDate']:
                plans.append(('耗材补给',f'{c.name}建议补给',date.fromisoformat(predicted['suggestedPurchaseDate']),c.id))
        open_repair=db.scalar(select(m.RepairRecord).where(m.RepairRecord.itemId==item.id,m.RepairRecord.status!='已完成'))
        item.status='维修中' if open_repair else '待维护' if any(date.fromisoformat(r.nextDueDate)<=as_of for r in latest.values()) else '正常使用'
    keys={(kind,related) for kind,_,_,related in plans}
    existing=list(db.scalars(select(m.Reminder).where(m.Reminder.itemId==item.id)))
    by_key={(r.type,r.relatedId):r for r in existing}
    for record in existing:
        if (record.type,record.relatedId) not in keys and record.status=='pending':
            db.delete(record)
    for kind,title,due,related in plans:
        record=by_key.get((kind,related))
        if record:
            # Only a changed source date resets a reminder, not every snapshot.
            if record.originalDueDate!=due.isoformat():
                record.originalDueDate=due.isoformat()
                record.dueDate=due.isoformat()
                record.status='pending'
            record.title=title
        else:
            record=m.Reminder(itemId=item.id,type=kind,title=title,dueDate=due.isoformat(),originalDueDate=due.isoformat(),relatedId=related)
            db.add(record)
        days=(date.fromisoformat(record.dueDate)-as_of).days
        record.priority='紧急' if days<=2 else '重要' if days<=7 else '普通' if days<=30 else '轻松'
    db.flush()


def sync_all(db, as_of=None):
    for item in db.scalars(select(m.Item)):
        sync_item(db,item,as_of)

"""Record correction reconciles lifecycle, reminders, stock and statistics."""
from datetime import date
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select,delete,update
from sqlalchemy.orm import Session
from .database import get_db
from . import models as m, schemas as s
from .clock import today
from .serializers import row,cents
from .lifecycle import sync_item,event,next_maintenance,consumable_data

router=APIRouter()
def require(db,model,ident):
    record=db.get(model,ident)
    if not record: raise HTTPException(404,'记录不存在或已撤销')
    return record


@router.put('/maintenance/{record_id}')
def edit_maintenance(record_id:str,payload:s.MaintenanceInput,db:Session=Depends(get_db)):
    record=require(db,m.MaintenanceRecord,record_id)
    if payload.date>today():raise HTTPException(422,'记录日期不能晚于今天')
    record.type=payload.type;record.date=payload.date.isoformat();record.intervalDays=payload.intervalDays
    record.nextDueDate=next_maintenance(payload.date,payload.intervalDays).isoformat()
    record.description=payload.description;record.cost=cents(payload.cost)
    event(db,record.itemId,'maintenance',record.date,record.type,record.id,record.description,'user')
    sync_item(db,require(db,m.Item,record.itemId));return row(record)


@router.delete('/maintenance/{record_id}')
def delete_maintenance(record_id:str,db:Session=Depends(get_db)):
    record=require(db,m.MaintenanceRecord,record_id);item=require(db,m.Item,record.itemId)
    db.execute(delete(m.LifecycleEvent).where(m.LifecycleEvent.itemId==item.id,m.LifecycleEvent.relatedId==record.id))
    db.execute(delete(m.Reminder).where(m.Reminder.itemId==item.id,m.Reminder.relatedId==record.id))
    db.delete(record);db.flush();sync_item(db,item);return {'deleted':record_id}


@router.delete('/consumption-records/{record_id}')
def undo_consume(record_id:str,db:Session=Depends(get_db)):
    record=require(db,m.ConsumptionRecord,record_id)
    if record.quantityUsed<=0:raise HTTPException(422,'观察基准不能撤销')
    c=require(db,m.Consumable,record.consumableId)
    removed=db.execute(delete(m.ConsumptionRecord).where(m.ConsumptionRecord.id==record_id))
    if removed.rowcount!=1:raise HTTPException(404,'记录已撤销')
    db.execute(update(m.Consumable).where(m.Consumable.id==c.id).values(currentStock=m.Consumable.currentStock+record.quantityUsed))
    db.flush();db.refresh(c);sync_item(db,require(db,m.Item,c.itemId));return consumable_data(db,c)


@router.delete('/restock-records/{record_id}')
def undo_restock(record_id:str,db:Session=Depends(get_db)):
    record=require(db,m.RestockRecord,record_id);c=require(db,m.Consumable,record.consumableId)
    result=db.execute(update(m.Consumable).where(m.Consumable.id==c.id,m.Consumable.currentStock>=record.quantity).values(currentStock=m.Consumable.currentStock-record.quantity))
    if result.rowcount!=1:raise HTTPException(422,'撤销后库存会为负，操作已阻止。请先核对消耗记录。')
    removed=db.execute(delete(m.RestockRecord).where(m.RestockRecord.id==record_id))
    if removed.rowcount!=1:raise HTTPException(404,'记录已撤销')
    db.flush();db.refresh(c);sync_item(db,require(db,m.Item,c.itemId));return consumable_data(db,c)


@router.patch('/repairs/{record_id}/details')
def correct_repair(record_id:str,payload:s.RepairDetails,db:Session=Depends(get_db)):
    record=require(db,m.RepairRecord,record_id)
    record.cost=cents(payload.cost);record.description=payload.description;record.serviceType=payload.serviceType
    for e in db.scalars(select(m.LifecycleEvent).where(m.LifecycleEvent.itemId==record.itemId,m.LifecycleEvent.type=='repair',m.LifecycleEvent.relatedId.in_([record.id,record.id+':completed']))):e.description=record.description
    sync_item(db,require(db,m.Item,record.itemId));return row(record)

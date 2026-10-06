from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select
from . import models as m
from .clock import today


def cents(value):
    return int((Decimal(str(value))*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))


def row(entity):
    values={column.name:getattr(entity,column.name) for column in entity.__table__.columns}
    if isinstance(entity, m.Document):
        values['filePath']=f'/api/documents/{entity.id}/file'
        values['originalFilename']=entity.originalFilename or entity.filename
    elif isinstance(entity, m.ItemImage) and not entity.filePath.startswith('/assets/'):
        values['filePath']=f'/api/images/{entity.id}'
    for key in ['purchasePrice','cost']:
        if key in values:
            values[key]=values[key]/100
    return values


def item_data(db,item):
    maintenance=db.scalar(select(m.MaintenanceRecord).where(m.MaintenanceRecord.itemId==item.id).order_by(m.MaintenanceRecord.date.desc()))
    return {**row(item),'warrantyDaysLeft':(date.fromisoformat(item.warrantyEndDate)-today()).days if item.warrantyEndDate else None,'nextMaintenance':maintenance.nextDueDate if maintenance else None}


def reminder_data(record):
    return {**row(record),'daysLeft':(date.fromisoformat(record.dueDate)-today()).days}

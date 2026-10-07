"""A presentation projection over the existing lifecycle records; no second seed."""
from collections import defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from . import models as m
from .clock import today
from .database import get_db
from .lifecycle import sync_all, consumable_data
from .serializers import item_data, row

router = APIRouter()
STAGES = [('purchase', '购买'), ('return', '退换'), ('use', '使用'),
          ('maintenance', '维护'), ('warranty', '保修'), ('repair', '维修'), ('retired', '淘汰')]


@router.get('/home/showcase')
def showcase(db: Session = Depends(get_db)):
    sync_all(db)
    images, events, maintenance, consumables = (defaultdict(list) for _ in range(4))
    for image in db.scalars(select(m.ItemImage).where(m.ItemImage.type == 'product').order_by(m.ItemImage.createdAt)):
        images[image.itemId].append(row(image)['filePath'])
    for event in db.scalars(select(m.LifecycleEvent).order_by(m.LifecycleEvent.date, m.LifecycleEvent.id)):
        events[event.itemId].append(event)
    for record in db.scalars(select(m.MaintenanceRecord).order_by(m.MaintenanceRecord.date.desc())):
        maintenance[record.itemId].append(record)
    for c in db.scalars(select(m.Consumable)):
        consumables[c.itemId].append(consumable_data(db, c))
    items = []
    for item in db.scalars(select(m.Item).order_by(m.Item.createdAt, m.Item.id)):
        info = item_data(db, item)
        cover = item.coverImage
        if not cover or cover == '/assets/no-photo.svg':
            cover = next(iter(images[item.id]), cover) or '/assets/no-photo.svg'
        # Only the fields the showcase displays: no serials, prices or attachment bodies.
        public = {key: info[key] for key in ('id', 'name', 'brand', 'model', 'status', 'isDemo', 'warrantyEndDate', 'warrantyDaysLeft', 'nextMaintenance')}
        public['coverImage'] = cover
        days = info['warrantyDaysLeft']
        chip = item.status
        tone = 'green'
        if chip in ('淘汰', '转卖', '回收'):
            tone = 'gray'
        elif chip in ('待维护', '维修中'):
            tone = 'orange'
        elif days is not None:
            chip, tone = ('已过保', 'red') if days < 0 else ('即将到期', 'orange') if days <= 30 else ('保修中', 'green')
        next_record = next((r for r in maintenance[item.id] if r.nextDueDate == info['nextMaintenance']), None)
        cs = consumables[item.id]
        attention = [c for c in cs if c['status'] in ('即将耗尽', '建议补货')]
        cs.sort(key=lambda c: ({'即将耗尽': 0, '建议补货': 1, '数据不足': 2, '正常': 3}[c['status']],
                               c['estimatedDaysLeft'] if c['estimatedDaysLeft'] is not None else float('inf')))
        chosen = cs[0] if cs else None
        if not chosen:
            consumable = {'title': '暂无耗材', 'subtitle': '未关联耗材', 'tone': 'gray'}
        else:
            title = f"{len(attention)} 种需关注" if len(attention) > 1 else f"{chosen['name']}剩 {chosen['estimatedDaysLeft']} 天" if chosen['estimatedDaysLeft'] is not None else chosen['name'] + ' · ' + chosen['status']
            consumable = {'title': title, 'subtitle': '建议 ' + chosen['suggestedPurchaseDate'] + ' 补货' if chosen['suggestedPurchaseDate'] else chosen['status'],
                          'tone': 'orange' if attention else 'gray' if chosen['status'] == '数据不足' else 'green'}
        current = 'retired' if item.status in ('淘汰', '转卖', '回收') else 'repair' if item.status == '维修中' else 'maintenance' if item.status == '待维护' else 'use'
        nodes = []
        for kind, label in STAGES:
            records = [e for e in events[item.id] if (e.type == kind or kind == 'repair' and e.type == 'repair_completed') and e.date <= today().isoformat()]
            nodes.append({'type': kind, 'label': label, 'date': records[-1].date if records else None,
                          'state': 'current' if kind == current else 'completed' if records else 'pending'})
        items.append({'item': public, 'chip': {'label': chip, 'tone': tone},
                      'maintenanceType': next_record.type if next_record else None,
                      'consumable': consumable, 'lifecycle': nodes})
    return {'items': items, 'total': len(items), 'asOf': today().isoformat()}

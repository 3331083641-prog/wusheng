from collections import Counter
from datetime import date
from sqlalchemy import select
from . import models as m
from .clock import today
from .serializers import item_data


def statistics(db, consumables):
    now=today()
    year=str(now.year)
    items=list(db.scalars(select(m.Item)))
    reminders=list(db.scalars(select(m.Reminder)))
    maintenance=list(db.scalars(select(m.MaintenanceRecord)))
    repairs=list(db.scalars(select(m.RepairRecord)))
    restocks=list(db.scalars(select(m.RestockRecord)))
    consumptions=list(db.scalars(select(m.ConsumptionRecord)))
    item_map={i.id:i for i in items}
    warranty=[i for i in items if i.warrantyEndDate and i.warrantyEndDate>=now.isoformat()]
    categories=Counter(i.category for i in items)
    ranking=Counter(item_map[r.itemId].category for r in maintenance if r.date.startswith(year))
    distribution=Counter()
    for item in items:
        if not item.warrantyEndDate: distribution['未记录']+=1;continue
        days=(date.fromisoformat(item.warrantyEndDate)-now).days
        label='已过期' if days<0 else '3个月内' if days<=90 else '3–6个月' if days<=180 else '6–12个月' if days<=365 else '1年以上'
        distribution[label]+=1
    trend=[]
    costs=[]
    for month in range(1,13):
        prefix=f'{now.year}-{month:02}'
        monthly=[r for r in reminders if r.dueDate.startswith(prefix)]
        trend.append({'month':f'{month}月','count':len(monthly),'completed':sum(r.status=='completed' for r in monthly)})
        costs.append({'month':f'{month}月','cost':sum(r.cost for r in restocks if r.date.startswith(prefix))/100})
    soon=sum(0<=(date.fromisoformat(i.warrantyEndDate)-now).days<=90 for i in warranty)
    insights=[f'未来 3 个月有 {soon} 件物品将结束保修。',f'{len(consumables)} 种耗材已关联设备，{sum(c["status"] in ["即将耗尽","建议补货"] for c in consumables)} 种需要关注补给。']
    if ranking:
        name,count=ranking.most_common(1)[0]
        insights.append(f'今年 {name} 的维护记录最多，共 {count} 次。')
    else:insights.append('今年暂无维护记录，补充真实记录后可分析维护频率。')
    return {'itemCount':len(items),'warrantyCount':len(warranty),'maintenanceDue':sum(bool(item_data(db,i)['nextMaintenance']) and item_data(db,i)['nextMaintenance']<=now.isoformat() for i in items),'consumableLow':sum(c['status'] in ['即将耗尽','建议补货'] for c in consumables),'warrantyCoverage':round(len(warranty)/len(items)*100) if items else 0,'annualMaintenance':sum(r.date.startswith(year) for r in maintenance),'repairSpend':sum(r.cost for r in repairs if (r.completionDate or r.reportDate).startswith(year))/100,'consumableSpend':sum(r.cost for r in restocks if r.date.startswith(year))/100,'monthlyConsumption':round(sum(r.quantityUsed for r in consumptions if r.date.startswith(f'{now.year}-{now.month:02}')),2),'categories':[{'name':k,'value':v} for k,v in categories.items()],'reminderTrend':trend,'maintenanceRanking':[{'name':k,'count':v} for k,v in ranking.most_common()],'warrantyDistribution':[{'name':label,'count':distribution[label]} for label in ['已过期','3个月内','3–6个月','6–12个月','1年以上','未记录']],'consumableTrend':costs,'insights':insights}

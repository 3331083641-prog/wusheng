from datetime import datetime,timezone,timedelta,date
from fastapi import APIRouter,Depends,HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import select
from .database import get_db
from . import models as m
from .lifecycle import sync_all

router=APIRouter()
def escape(value):return str(value).replace('\\','\\\\').replace('\n','\\n').replace(';','\\;').replace(',','\\,').replace('\r','')


@router.get('/reminders/calendar.ics')
def export_calendar(reminderId:str|None=None,db:Session=Depends(get_db)):
    sync_all(db)
    records=list(db.scalars(select(m.Reminder).where(m.Reminder.status=='pending')))
    if reminderId:
        records=[r for r in records if r.id==reminderId]
        if not records:raise HTTPException(404,'未找到待处理提醒')
    lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Wusheng//Local Reminders//ZH','CALSCALE:GREGORIAN']
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    for r in records:
        item=db.get(m.Item,r.itemId);day=date.fromisoformat(r.dueDate)
        lines+=['BEGIN:VEVENT','UID:'+r.id+'@wusheng.local','DTSTAMP:'+stamp,'DTSTART;VALUE=DATE:'+day.strftime('%Y%m%d'),'DTEND;VALUE=DATE:'+(day+timedelta(days=1)).strftime('%Y%m%d'),'SUMMARY:'+escape(item.name+' · '+r.title),'DESCRIPTION:'+escape(r.type+'；期限依据用户本地档案，请以商家政策为准。'),'BEGIN:VALARM','ACTION:DISPLAY','TRIGGER:-PT9H','DESCRIPTION:物生提醒','END:VALARM','END:VEVENT']
    lines.append('END:VCALENDAR')
    # RFC 5545 folds UTF-8 content lines at <=75 octets, never inside a codepoint.
    folded=[]
    for line in lines:
        part=''
        for character in line:
            if len((part+character).encode())>74:folded.append(part);part=' '+character
            else:part+=character
        folded.append(part)
    return Response(('\r\n'.join(folded)+'\r\n').encode(),media_type='text/calendar',headers={'Content-Disposition':'attachment; filename="wusheng-reminders.ics"'})

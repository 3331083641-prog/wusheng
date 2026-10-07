from contextlib import asynccontextmanager
from datetime import date, timedelta
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, delete, update
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from .database import Base, engine, get_db, UPLOADS, uid, timestamp, migrate_schema
from . import models as m, schemas as s
from .clock import today
from .serializers import row, item_data, reminder_data, cents
from .lifecycle import sync_item, sync_all, consumable_data, event, next_maintenance
from .context import ContextBuilder, lifecycle_suggestions
from .ai_engine import get_factory
from .statistics import statistics
from .seed import seed
from .attachments import router as attachments_router, bind_draft, open_draft, cleanup_drafts, upgrade_legacy_documents
from .storage import file_transaction, prune_empty
from .calendar_export import router as calendar_router
from .backup_restore import router as backup_router
from .manual_ocr import router as ocr_router
from .evidence_pack import router as pack_router
from .item_archive import router as archive_router
from .home_showcase import router as showcase_router
from .corrections import router as correction_router
from .sharing import router as sharing_router, install_hosting


@asynccontextmanager
async def lifespan(_):
    Base.metadata.create_all(engine)
    migrate_schema(engine)
    with Session(engine) as db:
        seed(db)
        db.commit()
        upgrade_legacy_documents(db)
        cleanup_drafts(db)
        db.execute(update(m.Document).where(m.Document.textStatus == "ocr_processing").values(textStatus="ocr_failed",ocrError="上次识别中断，原文件保留，可重试"))
        db.commit()
    get_factory()
    yield


app=FastAPI(title='物生 Wusheng Lifecycle API',version='0.1.0',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=['http://127.0.0.1:5173','http://localhost:5173'],allow_methods=['GET','POST','PUT','PATCH','DELETE'],allow_headers=['Content-Type'])
app.mount('/uploads',StaticFiles(directory=UPLOADS),name='uploads')
app.include_router(attachments_router)
app.include_router(attachments_router, prefix='/api', include_in_schema=False)
app.include_router(sharing_router)
app.include_router(ocr_router)
app.include_router(pack_router)
app.include_router(archive_router)
app.include_router(showcase_router)
app.include_router(correction_router)
app.include_router(calendar_router)
app.include_router(backup_router)


@app.exception_handler(SQLAlchemyError)
async def database_error(_,__):
    return JSONResponse(status_code=500,content={'detail':'数据库写入失败，操作已回滚。请稍后重试。'})


@app.exception_handler(OSError)
async def filesystem_error(_,__):
    return JSONResponse(status_code=500,content={'detail':'无法读写本地附件，请检查磁盘空间或文件是否被其他程序占用。'})


def get_or_404(db,model,ident):
    obj=db.get(model,ident)
    if not obj:raise HTTPException(404,'没有找到对应记录')
    return obj


def not_future(day):
    if day>today():raise HTTPException(422,'记录日期不能晚于今天')


@app.get('/health')
def health():
    return {'status':'ok','database':'SQLite','aiMode':'local-evidence','ocr':'RapidOCR ONNX（本地）','today':today().isoformat(), **get_factory().status()}


@app.get('/snapshot')
def snapshot(db:Session=Depends(get_db)):
    sync_all(db)
    cs=[consumable_data(db,c) for c in db.scalars(select(m.Consumable))]
    return {'today':today().isoformat(),'items':[item_data(db,i) for i in db.scalars(select(m.Item).order_by(m.Item.createdAt.desc()))],'reminders':[reminder_data(r) for r in db.scalars(select(m.Reminder).order_by(m.Reminder.dueDate))],'repairs':[row(r) for r in db.scalars(select(m.RepairRecord).order_by(m.RepairRecord.reportDate.desc()))],'consumables':cs,'stats':statistics(db,cs)}


@app.get('/items')
def list_items(q:str='',db:Session=Depends(get_db)):
    sync_all(db)
    items=[item_data(db,i) for i in db.scalars(select(m.Item))]
    return [i for i in items if q.lower() in ' '.join(str(i[k]) for k in ['name','brand','model','serialNumber']).lower()]


@app.get('/items/{ident}')
def detail(ident:str,db:Session=Depends(get_db)):
    item=get_or_404(db,m.Item,ident)
    sync_item(db,item)
    context=ContextBuilder().build(db,item)
    return {'item':context['item'],'images':[row(i) for i in db.scalars(select(m.ItemImage).where(m.ItemImage.itemId==ident))],'documents':context['manuals'],'maintenance':context['maintenance'],'repairs':context['repairs'],'consumables':context['consumables'],'events':[row(e) for e in db.scalars(select(m.LifecycleEvent).where(m.LifecycleEvent.itemId==ident).order_by(m.LifecycleEvent.date))],'suggestions':lifecycle_suggestions(context)}


def set_item_fields(item,payload):
    values=payload.model_dump(exclude={'recognitionSessionId','draftSessionId','images'})
    values['purchaseDate']=payload.purchaseDate.isoformat()
    values['purchasePrice']=cents(payload.purchasePrice)
    # Status is reconciled from records; retired/transferred states are explicit.
    for key,value in values.items():setattr(item,key,value)
    item.updatedAt=timestamp()


@app.post('/items',status_code=201)
def create_item(payload:s.ItemInput,db:Session=Depends(get_db)):
    session=None
    draft_id=payload.draftSessionId
    if payload.recognitionSessionId:
        session=get_or_404(db,m.RecognitionSession,payload.recognitionSessionId)
        if session.itemId:raise HTTPException(409,'这个识别会话已建立档案，请勿重复保存')
        if draft_id and session.draftId != draft_id:raise HTTPException(422,'识别结果与当前草稿不一致，请重新识别')
        draft_id=draft_id or session.draftId
    elif payload.images:
        raise HTTPException(422,'图片必须来自有效的本地草稿或识别会话')
    if draft_id:open_draft(db,draft_id)
    with file_transaction(db) as files:
        item=m.Item(id=uid(),coverImage='/assets/no-photo.svg')
        set_item_fields(item,payload)
        db.add(item)
        db.flush()
        if draft_id:
            bind_draft(db,item,draft_id,files)
        elif session:
            session.itemId=item.id
            for image in session.images:
                db.add(m.ItemImage(itemId=item.id,filePath=image['filePath'],type=image['type'],source='local-ocr'))
            product=next((i for i in session.images if i['type']=='product'),None)
            if product:item.coverImage=product['filePath']
        sync_item(db,item)
        output=item_data(db,item)
    if draft_id:prune_empty(f'uploads/drafts/{draft_id}')
    return output


@app.put('/items/{ident}')
def edit_item(ident:str,payload:s.ItemInput,db:Session=Depends(get_db)):
    item=get_or_404(db,m.Item,ident)
    set_item_fields(item,payload)
    sync_item(db,item)
    return item_data(db,item)


@app.delete('/items/{ident}')
def delete_item(ident:str,db:Session=Depends(get_db)):
    item=get_or_404(db,m.Item,ident)
    with file_transaction(db) as files:
        attachments=list(db.scalars(select(m.ItemImage).where(m.ItemImage.itemId==ident)))+list(db.scalars(select(m.Document).where(m.Document.itemId==ident)))
        paths={a.filePath for a in attachments if not a.filePath.startswith('/assets/')}
        for path in paths:
            # Never delete a legacy shared file still belonging to another item.
            others=db.scalar(select(m.ItemImage.id).where(m.ItemImage.filePath==path,m.ItemImage.itemId!=ident)) or db.scalar(select(m.Document.id).where(m.Document.filePath==path,m.Document.itemId!=ident))
            if not others:files.remove(path)
        sessions=list(db.scalars(select(m.RecognitionSession).where(m.RecognitionSession.itemId==ident)))
        for session in sessions:
            db.execute(delete(m.RecognitionResult).where(m.RecognitionResult.sessionId==session.id))
            db.delete(session)
        db.execute(delete(m.DraftSession).where(m.DraftSession.itemId==ident))
        db.delete(item)
    prune_empty(f'images/items/{ident}')
    prune_empty(f'documents/manuals/{ident}')
    return {'deleted':ident}


@app.post('/items/{ident}/maintenance',status_code=201)
def maintenance(ident:str,payload:s.MaintenanceInput,db:Session=Depends(get_db)):
    item=get_or_404(db,m.Item,ident)
    not_future(payload.date)
    record=m.MaintenanceRecord(id=uid(),itemId=ident,type=payload.type,date=payload.date.isoformat(),intervalDays=payload.intervalDays,nextDueDate=next_maintenance(payload.date,payload.intervalDays).isoformat(),description=payload.description,cost=cents(payload.cost))
    db.add(record)
    db.flush()
    event(db,ident,'maintenance',payload.date,payload.type,record.id,payload.description,'user')
    sync_item(db,item)
    return row(record)


@app.patch('/reminders/{ident}')
def reminder_action(ident:str,payload:s.ReminderAction,db:Session=Depends(get_db)):
    record=get_or_404(db,m.Reminder,ident)
    if payload.action=='complete':record.status='completed'
    else:
        record.dueDate=(max(today(),date.fromisoformat(record.dueDate))+timedelta(days=payload.days)).isoformat()
        record.status='pending'
    return row(record)


@app.post('/repairs',status_code=201)
def create_repair(payload:s.RepairInput,db:Session=Depends(get_db)):
    item=get_or_404(db,m.Item,payload.itemId)
    not_future(payload.reportDate)
    values=payload.model_dump()
    values.update(id=uid(),reportDate=payload.reportDate.isoformat(),cost=cents(payload.cost),progress=[{'status':'待预约','date':payload.reportDate.isoformat()}])
    repair=m.RepairRecord(**values)
    db.add(repair)
    db.flush()
    event(db,item.id,'repair',payload.reportDate,'报修：'+payload.issue,repair.id,payload.description,'user')
    sync_item(db,item)
    return row(repair)


@app.patch('/repairs/{ident}')
def update_repair(ident:str,payload:s.RepairUpdate,db:Session=Depends(get_db)):
    record=get_or_404(db,m.RepairRecord,ident)
    sequence=['待预约','诊断中','维修中','已完成']
    current,target=sequence.index(record.status),sequence.index(payload.status)
    if target<current or target>current+1:raise HTTPException(422,'维修进度请按 待预约 → 诊断中 → 维修中 → 已完成 更新')
    if payload.status!=record.status:
        record.progress=[*record.progress,{'status':payload.status,'date':timestamp()}]
    record.status=payload.status
    record.cost=cents(payload.cost)
    record.description=payload.description
    if payload.status=='已完成':
        record.completionDate=today().isoformat()
        event(db,record.itemId,'repair',record.completionDate,'维修完成：'+record.issue,record.id+':completed',record.description,'user')
        event(db,record.itemId,'use',record.completionDate,'修复后继续使用',f'repair:{record.id}',source='user')
    sync_item(db,get_or_404(db,m.Item,record.itemId))
    return row(record)


@app.post('/consumables',status_code=201)
def create_consumable(payload:s.ConsumableInput,db:Session=Depends(get_db)):
    item=get_or_404(db,m.Item,payload.itemId)
    c=m.Consumable(id=uid(),**payload.model_dump())
    db.add(c)
    db.flush()
    db.add(m.ConsumptionRecord(consumableId=c.id,date=today().isoformat(),quantityUsed=0))
    sync_item(db,item)
    return consumable_data(db,c)


@app.post('/consumables/{ident}/consume',status_code=201)
def consume(ident:str,payload:s.StockInput,db:Session=Depends(get_db)):
    c=get_or_404(db,m.Consumable,ident)
    not_future(payload.date)
    result=db.execute(update(m.Consumable).where(m.Consumable.id==ident,m.Consumable.currentStock>=payload.quantity).values(currentStock=m.Consumable.currentStock-payload.quantity))
    if result.rowcount!=1:raise HTTPException(422,'消耗数量超过当前库存；请先核对库存或补货')
    db.add(m.ConsumptionRecord(consumableId=ident,date=payload.date.isoformat(),quantityUsed=payload.quantity))
    db.flush()
    db.refresh(c)
    sync_item(db,get_or_404(db,m.Item,c.itemId))
    return consumable_data(db,c)


@app.post('/consumables/{ident}/restock',status_code=201)
def restock(ident:str,payload:s.StockInput,db:Session=Depends(get_db)):
    c=get_or_404(db,m.Consumable,ident)
    not_future(payload.date)
    db.execute(update(m.Consumable).where(m.Consumable.id==ident).values(currentStock=m.Consumable.currentStock+payload.quantity))
    db.add(m.RestockRecord(consumableId=ident,date=payload.date.isoformat(),quantity=payload.quantity,cost=cents(payload.cost)))
    db.flush()
    db.refresh(c)
    sync_item(db,get_or_404(db,m.Item,c.itemId))
    return consumable_data(db,c)


@app.post('/recognize')
def recognize(files:list[UploadFile]=File(...),types:list[str]=Form(...),db:Session=Depends(get_db)):
    # Compatibility for existing clients: use the same persistent draft pipeline.
    from .attachments import create_draft, upload_images, recognize_draft, discard_draft
    if not 1<=len(files)<=10 or len(types)!=len(files):raise HTTPException(422,'请上传 1–10 张图片并选择类型')
    draft=create_draft(db)
    db.commit()
    try:
        for file,kind in zip(files,types):upload_images(draft['id'],[file],kind,db)
        return recognize_draft(draft['id'],db)
    except Exception:
        db.rollback()
        discard_draft(db,db.get(m.DraftSession,draft['id']))
        raise


@app.post('/generate')
def generate(payload:s.Question,db:Session=Depends(get_db)):
    item=get_or_404(db,m.Item,payload.itemId)
    sync_item(db,item)
    context=ContextBuilder().build(db,item)
    return get_factory().generate(payload.question,context)


@app.get('/items/{ident}/event-graph')
def event_graph(ident:str,db:Session=Depends(get_db)):
    item=get_or_404(db,m.Item,ident)
    sync_item(db,item)
    events=[row(e) for e in db.scalars(select(m.LifecycleEvent).where(m.LifecycleEvent.itemId==ident).order_by(m.LifecycleEvent.date,m.LifecycleEvent.id))]
    return {'itemId':ident,'nodes':events,'edges':[{'from':a['id'],'to':b['id'],'relation':'chronological'} for a,b in zip(events,events[1:])]+[{'from':e['id'],'to':e['relatedId'],'relation':'evidence'} for e in events if e['source']=='user' and e['relatedId'] not in ['purchase','use','retired']]}


install_hosting(app)

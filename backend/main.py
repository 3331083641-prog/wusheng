from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path
from io import BytesIO
import warnings
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader
from sqlalchemy import select, delete, update
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from .database import Base, engine, get_db, UPLOADS, uid, timestamp
from . import models as m, schemas as s
from .clock import today
from .serializers import row, item_data, reminder_data, cents
from .lifecycle import sync_item, sync_all, consumable_data, event, next_maintenance
from .context import ContextBuilder, lifecycle_suggestions
from .providers import EvidenceProvider
from .recognition import provider, parse_lines, fuse_candidates
from .statistics import statistics
from .seed import seed


@asynccontextmanager
async def lifespan(_):
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        seed(db)
        db.commit()
    yield


app=FastAPI(title='物生 Wusheng Lifecycle API',version='0.1.0',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=['http://127.0.0.1:5173','http://localhost:5173'],allow_methods=['GET','POST','PUT','PATCH','DELETE'],allow_headers=['Content-Type'])
app.mount('/uploads',StaticFiles(directory=UPLOADS),name='uploads')


@app.exception_handler(SQLAlchemyError)
async def database_error(_,__):
    return JSONResponse(status_code=500,content={'detail':'数据库写入失败，操作已回滚。请稍后重试。'})


def get_or_404(db,model,ident):
    obj=db.get(model,ident)
    if not obj:raise HTTPException(404,'没有找到对应记录')
    return obj


def not_future(day):
    if day>today():raise HTTPException(422,'记录日期不能晚于今天')


@app.get('/health')
def health():
    return {'status':'ok','database':'SQLite','aiMode':'local-evidence','ocr':'RapidOCR ONNX（本地）','today':today().isoformat()}


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
    values=payload.model_dump(exclude={'recognitionSessionId','images'})
    values['purchaseDate']=payload.purchaseDate.isoformat()
    values['purchasePrice']=cents(payload.purchasePrice)
    # Status is reconciled from records; retired/transferred states are explicit.
    for key,value in values.items():setattr(item,key,value)
    item.updatedAt=timestamp()


@app.post('/items',status_code=201)
def create_item(payload:s.ItemInput,db:Session=Depends(get_db)):
    session=None
    if payload.recognitionSessionId:
        session=get_or_404(db,m.RecognitionSession,payload.recognitionSessionId)
        if session.itemId:raise HTTPException(409,'这个识别会话已建立档案，请勿重复保存')
    elif payload.images:
        raise HTTPException(422,'图片必须来自有效的本地识别会话')
    item=m.Item(id=uid(),coverImage='/assets/no-photo.svg')
    set_item_fields(item,payload)
    db.add(item)
    db.flush()
    if session:
        session.itemId=item.id
        # Trust stored session image paths, never paths supplied by the browser.
        for image in session.images:
            db.add(m.ItemImage(itemId=item.id,filePath=image['filePath'],type=image['type'],source='local-ocr'))
        product=next((i for i in session.images if i['type']=='product'),None)
        if product:item.coverImage=product['filePath']
    sync_item(db,item)
    return item_data(db,item)


@app.put('/items/{ident}')
def edit_item(ident:str,payload:s.ItemInput,db:Session=Depends(get_db)):
    item=get_or_404(db,m.Item,ident)
    set_item_fields(item,payload)
    sync_item(db,item)
    return item_data(db,item)


@app.delete('/items/{ident}')
def delete_item(ident:str,db:Session=Depends(get_db)):
    get_or_404(db,m.Item,ident)
    # Uploaded files remain available for manual recovery; no recursive deletion.
    db.execute(delete(m.Item).where(m.Item.id==ident))
    return {'deleted':ident,'note':'数据库关联已删除；本地附件保留以便恢复'}


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


@app.post('/items/{ident}/documents',status_code=201)
def upload_document(ident:str,file:UploadFile=File(...),db:Session=Depends(get_db)):
    get_or_404(db,m.Item,ident)
    contents=file.file.read(20*1024*1024+1)
    if len(contents)>20*1024*1024:raise HTTPException(413,'PDF 不超过 20MB')
    if not contents.startswith(b'%PDF-'):raise HTTPException(415,'请上传有效 PDF 文件')
    try:
        reader=PdfReader(BytesIO(contents))
        if reader.is_encrypted:raise ValueError('encrypted')
        if len(reader.pages)>200:raise ValueError('too many pages')
        pages=[(i+1,page.extract_text() or '') for i,page in enumerate(reader.pages)]
        text='\n'.join(f'[第 {i} 页]\n'+content for i,content in pages if content.strip())[:500000]
    except Exception:raise HTTPException(422,'无法解析 PDF：请使用未加密且不超过 200 页的文件')
    ident_file=uid()+'.pdf'
    (UPLOADS/ident_file).write_bytes(contents)
    document=m.Document(itemId=ident,filename=Path(file.filename or '说明书.pdf').name,filePath='/uploads/'+ident_file,extractedText=text)
    db.add(document)
    db.flush()
    return row(document)


@app.post('/recognize')
def recognize(files:list[UploadFile]=File(...),types:list[str]=Form(...),db:Session=Depends(get_db)):
    if not 1<=len(files)<=8 or len(types)!=len(files):raise HTTPException(422,'请上传 1–8 张图片，并选择每张图片类型')
    images=[]
    candidates=[]
    saved=[]
    messages=[]
    try:
        for file,kind in zip(files,types):
            if kind not in ['product','receipt','package','manual']:raise HTTPException(422,'图片类型无效')
            contents=file.file.read(10*1024*1024+1)
            if len(contents)>10*1024*1024:raise HTTPException(413,'单张图片不超过 10MB')
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('error',Image.DecompressionBombWarning)
                    image=Image.open(BytesIO(contents))
                    if image.format not in ['PNG','JPEG','WEBP']:raise ValueError()
                    if image.width*image.height>20_000_000:raise ValueError()
                    image.load()
                    converted=image.convert('RGB')
                    converted.thumbnail((2400,2400))
            except (UnidentifiedImageError,ValueError,OSError,Image.DecompressionBombError,Image.DecompressionBombWarning):raise HTTPException(415,'图片格式无效或超过 2000 万像素，请使用 JPG、PNG、WebP')
            filename=uid()+'.jpg'
            converted.save(UPLOADS/filename,quality=95)
            saved.append(UPLOADS/filename)
            source='/uploads/'+filename
            lines=provider.read(filename)
            found=parse_lines(lines,source)
            candidates.extend(found)
            images.append({'filePath':source,'type':kind})
            if not found:messages.append(f'{Path(file.filename or "图片").name}：未找到足够文字字段。请人工补充；纯照片视觉识别尚未启用。')
        session=m.RecognitionSession(id=uid(),images=images)
        db.add(session)
        db.flush()
        for candidate in candidates:db.add(m.RecognitionResult(sessionId=session.id,**candidate))
        fields=fuse_candidates(candidates)
        if any(c['confidence']<.8 for c in fields.values()):messages.append('存在低置信度或多图冲突字段，请核对后保存。')
        return {'sessionId':session.id,'candidates':candidates,'fields':fields,'images':images,'mode':'RapidOCR 本地中文 OCR + 字段融合规则','warnings':messages}
    except HTTPException:
        for path in saved:path.unlink(missing_ok=True)
        raise
    except Exception:
        for path in saved:path.unlink(missing_ok=True)
        raise HTTPException(503,'本地 OCR 暂时不可用，请检查依赖或改用手动录入')


@app.post('/generate')
def generate(payload:s.Question,db:Session=Depends(get_db)):
    item=get_or_404(db,m.Item,payload.itemId)
    sync_item(db,item)
    context=ContextBuilder().build(db,item)
    return EvidenceProvider().generate(payload.question,context)


@app.get('/items/{ident}/event-graph')
def event_graph(ident:str,db:Session=Depends(get_db)):
    item=get_or_404(db,m.Item,ident)
    sync_item(db,item)
    events=[row(e) for e in db.scalars(select(m.LifecycleEvent).where(m.LifecycleEvent.itemId==ident).order_by(m.LifecycleEvent.date,m.LifecycleEvent.id))]
    return {'itemId':ident,'nodes':events,'edges':[{'from':a['id'],'to':b['id'],'relation':'chronological'} for a,b in zip(events,events[1:])]+[{'from':e['id'],'to':e['relatedId'],'relation':'evidence'} for e in events if e['source']=='user' and e['relatedId'] not in ['purchase','use','retired']]}

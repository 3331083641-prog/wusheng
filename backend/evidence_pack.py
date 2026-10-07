"""Portable after-sales pack: relative UUID member names and hash manifest."""
from io import BytesIO
import json
from hashlib import sha256
import zipfile
from xml.sax.saxutils import escape
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import select
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from .database import get_db,timestamp
from . import models as m
from .context import ContextBuilder
from .serializers import row
from .storage import local_path
from .lifecycle import sync_item

router=APIRouter()


def summary_pdf(context, attachments):
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
    styles=getSampleStyleSheet()
    for style in styles.byName.values(): style.fontName='STSong-Light'
    output=BytesIO();story=[]
    def add(text,style='BodyText'):
        story.extend([Paragraph(escape(str(text)).replace('\n','<br/>'),styles[style]),Spacer(1,10)])
    add('物生 · 售后材料摘要','Title')
    item=context['item']
    for key in ['name','brand','model','purchaseDate','purchasePrice','purchaseChannel','serialNumber','warrantyEndDate','status']:
        add(f'{key}: {item.get(key) or "未记录"}')
    add('维护 / 维修记录','Heading2')
    for record in context['maintenance']: add(f"{record['date']} {record['type']} ¥{record['cost']} {record['description']}")
    for record in context['repairs']: add(f"{record['reportDate']} {record['issue']} {record['status']} ¥{record['cost']} {record['description']}")
    add('附件清单','Heading2')
    for record in attachments:add(record['name'])
    add('导出时间：'+timestamp())
    add('此材料来自用户本地档案，售后政策以厂家/商家为准。')
    SimpleDocTemplate(output).build(story)
    return output.getvalue()


@router.get('/items/{item_id}/evidence-pack')
def export_pack(item_id:str,includeManuals:bool=False,db:Session=Depends(get_db)):
    item=db.get(m.Item,item_id)
    if not item:raise HTTPException(404,'物品不存在')
    sync_item(db,item);context=ContextBuilder().build(db,item)
    entries={};metadata=[];total=0
    attachments=list(db.scalars(select(m.ItemImage).where(m.ItemImage.itemId==item_id)))
    if includeManuals: attachments += list(db.scalars(select(m.Document).where(m.Document.itemId==item_id)))
    for record in attachments:
        if record.filePath.startswith('/assets/'):continue
        path=local_path(record.filePath)
        if not path.is_file(): raise HTTPException(409,'附件缺失，请核对资料后再导出')
        total+=path.stat().st_size
        if total>250*1024*1024:raise HTTPException(413,'售后包附件超过 250MB，请减少资料')
        name=f'attachments/{record.id}{path.suffix.lower()}'
        entries[name]=path.read_bytes()
        metadata.append({'filename':name,'name':record.originalFilename,'type':record.type})
    entries['summary.pdf']=summary_pdf(context,metadata)
    # Do not export storedFilename or any internal disk path in summary JSON.
    summary={k:context[k] for k in ('item','maintenance','repairs','consumables','lifecycle')}
    for c in summary['consumables']:c.pop('coverImage',None)
    summary['item'].pop('coverImage',None)
    entries['archive.json']=json.dumps(summary,ensure_ascii=False,indent=2).encode()
    entries['README.txt']='此材料来自用户本地档案，售后政策以厂家/商家为准。附件采用安全名称，原文件名见 manifest.json。'.encode()
    manifest={'version':1,'itemId':item_id,'createdAt':timestamp(),'files':[]}
    for name,data in entries.items():
        info=next((record for record in metadata if record['filename']==name),{})
        manifest['files'].append({'filename':name,'size':len(data),'sha256':sha256(data).hexdigest(),'type':info.get('type','summary'),'originalFilename':info.get('name',name)})
    output=BytesIO()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in entries.items():archive.writestr(name,data)
        archive.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    from urllib.parse import quote
    title=quote('物生-'+item.name.replace('/','_').replace('\\','_')+'-售后材料.zip')
    return Response(output.getvalue(),media_type='application/zip',headers={'Content-Disposition':f"attachment; filename*=UTF-8''{title}"})

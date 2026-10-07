"""User-triggered background OCR. PDF archival never depends on OCR success."""
import threading
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session
from .database import get_db, timestamp
from . import models as m
from .storage import local_path
from .recognition import provider
from .serializers import row

router=APIRouter()
LIMIT=50
_gate=threading.Semaphore(1)


def extract_scanned(path):
    import pypdfium2 as pdfium
    parts=[]
    with pdfium.PdfDocument(str(path)) as pdf:
        if len(pdf)>LIMIT: raise ValueError('超过 50 页 OCR 上限，请先拆分文档')
        for number in range(len(pdf)):
            page=pdf[number]
            # Cap pixels as well as resolution for malicious giant page sizes.
            width,height=page.get_size()
            scale=min(2.2,(8_000_000/max(1,width*height))**.5)
            bitmap=page.render(scale=scale)
            image=bitmap.to_pil()
            import numpy as np
            with provider._lock:
                if provider._engine is None:
                    from rapidocr_onnxruntime import RapidOCR
                    provider._engine=RapidOCR(intra_op_num_threads=2,inter_op_num_threads=2)
                result,_=provider._engine(np.asarray(image.convert('RGB')))
            content='\n'.join(line[1] for line in (result or []))
            if content.strip(): parts.append(f'[第 {number+1} 页]\n{content}')
            image.close(); bitmap.close(); page.close()
            if sum(map(len,parts))>500_000: break
        return '\n'.join(parts)[:500_000],len(pdf)


def run_ocr(document_id, engine):
    try:
        with Session(engine) as db:
            document=db.get(m.Document,document_id)
            if not document: return
            text,count=extract_scanned(local_path(document.filePath))
            if not text.strip(): raise ValueError('未检测到可提取文字')
            document.extractedText=text;document.textStatus='ocr_ready';document.textSource='local_ocr'
            document.ocrPageCount=count;document.ocrError='';document.updatedAt=timestamp();db.commit()
    except Exception:
        with Session(engine) as db:
            document=db.get(m.Document,document_id)
            if document:
                document.textStatus='ocr_failed';document.ocrError='本地 OCR 未能完成。原始 PDF 保留，可重试（最多 50 页）。';db.commit()
    finally:
        _gate.release()


@router.post('/documents/{document_id}/ocr',status_code=202)
def trigger_ocr(document_id: str, tasks:BackgroundTasks, db:Session=Depends(get_db)):
    document=db.get(m.Document,document_id)
    if not document: raise HTTPException(404,'说明书不存在')
    if document.textStatus=='ocr_processing': raise HTTPException(409,'正在识别，请稍候')
    if document.pageCount and document.pageCount>LIMIT: raise HTTPException(422,'本地 OCR 最多处理 50 页，请先拆分文档')
    if not _gate.acquire(blocking=False): raise HTTPException(409,'本地 OCR 正在处理另一份说明书，请稍候')
    try:
        document.textStatus='ocr_processing';document.ocrError='';document.updatedAt=timestamp()
        db.commit()
        tasks.add_task(run_ocr,document_id,db.get_bind())
    except Exception:
        _gate.release();raise
    return row(document)

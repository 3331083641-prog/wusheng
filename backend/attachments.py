"""Persistent draft images and item manuals; local-only HTTP file access."""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.datastructures import Headers
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from .database import get_db, uid, timestamp
from . import models as m
from .serializers import row
from .storage import validate_image, validate_pdf, file_transaction, local_path, prune_empty, IMAGE_TYPES
from .recognition import provider, parse_lines, fuse_candidates

router = APIRouter()


def upgrade_legacy_documents(db):
    """Move prior local manuals into managed storage without replacing archives."""
    for document in list(db.scalars(select(m.Document).where(m.Document.storedFilename == ''))):
        path = local_path(document.filePath)
        if not path.is_file():
            continue
        with path.open('rb') as stream:
            contents, metadata = validate_pdf(UploadFile(stream, filename=document.filename, headers=Headers({'content-type':'application/pdf'})))
        relative = f'documents/manuals/{document.itemId}/{metadata["storedFilename"]}'
        with file_transaction(db) as files:
            # The generated demo PDF is also a test fixture; keep that fixture.
            if path.name == 'demo-care-guide.pdf':
                files.write(relative, contents)
            else:
                shared = db.scalar(select(m.Document.id).where(m.Document.filePath == document.filePath, m.Document.id != document.id))
                if shared: files.write(relative, contents)
                else: files.move(document.filePath, relative)
            document.filePath = relative
            for field, value in metadata.items():
                setattr(document, field, value)
            document.updatedAt = timestamp()


def require(db, model, ident):
    obj = db.get(model, ident)
    if not obj:
        raise HTTPException(404, '没有找到对应记录')
    return obj


def open_draft(db, ident):
    draft = require(db, m.DraftSession, ident)
    if draft.itemId:
        raise HTTPException(409, '此草稿已保存为物品，不能重复操作')
    return draft


def draft_data(image):
    return {**row(image), 'filePath': f'/api/drafts/{image.draftId}/images/{image.id}/file'}


def invalidate_recognition(db, draft):
    sessions = list(db.scalars(select(m.RecognitionSession.id).where(m.RecognitionSession.draftId == draft.id)))
    if sessions:
        db.execute(delete(m.RecognitionResult).where(m.RecognitionResult.sessionId.in_(sessions)))
        db.execute(delete(m.RecognitionSession).where(m.RecognitionSession.id.in_(sessions)))
    draft.updatedAt = timestamp()


def cleanup_drafts(db):
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    for draft in list(db.scalars(select(m.DraftSession).where(m.DraftSession.itemId.is_(None), m.DraftSession.updatedAt < cutoff))):
        discard_draft(db, draft)


def discard_draft(db, draft):
    with file_transaction(db) as files:
        for image in db.scalars(select(m.DraftImage).where(m.DraftImage.draftId == draft.id)):
            files.remove(image.filePath)
        invalidate_recognition(db, draft)
        db.delete(draft)
    prune_empty(f'uploads/drafts/{draft.id}')


@router.post('/drafts', status_code=201)
def create_draft(db: Session = Depends(get_db)):
    cleanup_drafts(db)
    draft = m.DraftSession(id=uid())
    db.add(draft)
    db.flush()
    return row(draft)


@router.post('/drafts/{draft_id}/images', status_code=201)
def upload_images(draft_id: str, files: list[UploadFile] = File(...), type: str = Form('product'), db: Session = Depends(get_db)):
    draft = open_draft(db, draft_id)
    kind = {'package': 'label', 'manual': 'manual_image'}.get(type, type)
    if kind not in IMAGE_TYPES:
        raise HTTPException(422, '图片类型无效')
    existing = list(db.scalars(select(m.DraftImage).where(m.DraftImage.draftId == draft_id)))
    if not files or len(existing) + len(files) > 10:
        raise HTTPException(422, '一次建档最多 10 张图片')
    output = []
    with file_transaction(db) as transaction:
        for file in files:
            contents, metadata = validate_image(file)
            relative = f'uploads/drafts/{draft_id}/{metadata["storedFilename"]}'
            transaction.write(relative, contents)
            image = m.DraftImage(id=uid(), draftId=draft_id, filePath=relative, type=kind, **metadata)
            db.add(image)
            db.flush()
            output.append(draft_data(image))
        invalidate_recognition(db, draft)
    return output


@router.get('/drafts/{draft_id}/images')
def list_draft_images(draft_id: str, db: Session = Depends(get_db)):
    open_draft(db, draft_id)
    return [draft_data(i) for i in db.scalars(select(m.DraftImage).where(m.DraftImage.draftId == draft_id))]


@router.get('/drafts/{draft_id}/images/{image_id}/file')
def draft_image_file(draft_id: str, image_id: str, db: Session = Depends(get_db)):
    image = require(db, m.DraftImage, image_id)
    if image.draftId != draft_id:
        raise HTTPException(404, '图片不属于此草稿')
    return serve(image)


@router.patch('/drafts/{draft_id}/images/{image_id}')
def change_image_type(draft_id: str, image_id: str, payload: dict, db: Session = Depends(get_db)):
    draft = open_draft(db, draft_id)
    image = require(db, m.DraftImage, image_id)
    if image.draftId != draft_id or payload.get('type') not in IMAGE_TYPES:
        raise HTTPException(422, '图片或类型无效')
    image.type = payload['type']
    invalidate_recognition(db, draft)
    return draft_data(image)


@router.delete('/drafts/{draft_id}/images/{image_id}')
def remove_draft_image(draft_id: str, image_id: str, db: Session = Depends(get_db)):
    draft = open_draft(db, draft_id)
    image = require(db, m.DraftImage, image_id)
    if image.draftId != draft_id:
        raise HTTPException(404, '图片不属于此草稿')
    with file_transaction(db) as files:
        files.remove(image.filePath)
        db.delete(image)
        invalidate_recognition(db, draft)
    return {'deleted': image_id}


@router.delete('/drafts/{draft_id}')
def delete_draft(draft_id: str, db: Session = Depends(get_db)):
    discard_draft(db, open_draft(db, draft_id))
    return {'deleted': draft_id}


@router.post('/drafts/{draft_id}/recognize')
def recognize_draft(draft_id: str, db: Session = Depends(get_db)):
    draft = open_draft(db, draft_id)
    images = list(db.scalars(select(m.DraftImage).where(m.DraftImage.draftId == draft_id)))
    if not images:
        raise HTTPException(422, '请先上传图片')
    candidates, messages = [], []
    for image in images:
        source = draft_data(image)['filePath']
        try:
            lines = provider.read(local_path(image.filePath))
        except Exception:
            raise HTTPException(503, '本地 OCR 暂时不可用；已上传图片保留，可重试或手动补充后保存')
        # Type determines which fields are authoritative candidates.
        found = parse_lines(lines, source)
        if image.type == 'product':
            found = [c for c in found if c['field'] in {'name', 'brand', 'model', 'category', 'serialNumber'}]
        elif image.type in {'label', 'manual_image'}:
            found = [c for c in found if c['field'] not in {'purchaseDate', 'purchasePrice', 'purchaseChannel'}]
        candidates.extend(found)
        if not found:
            messages.append(f'{image.originalFilename}：该图片未检测到可识别文字，可继续手动补充信息。')
    invalidate_recognition(db, draft)
    session = m.RecognitionSession(id=uid(), draftId=draft_id, images=[{'filePath': draft_data(i)['filePath'], 'type': i.type} for i in images])
    db.add(session)
    db.flush()
    for candidate in candidates:
        db.add(m.RecognitionResult(sessionId=session.id, **candidate))
    fields = fuse_candidates(candidates)
    if any(c['confidence'] < .8 for c in fields.values()):
        messages.append('存在低置信度或多图冲突字段，请核对后保存。')
    return {'sessionId': session.id, 'fields': fields, 'candidates': candidates, 'images': session.images, 'mode': 'RapidOCR 本地中文 OCR + 字段融合规则', 'warnings': messages}


def bind_draft(db, item, draft_id, files):
    draft = open_draft(db, draft_id)
    images = list(db.scalars(select(m.DraftImage).where(m.DraftImage.draftId == draft_id)))
    for image in images:
        relative = f'images/items/{item.id}/{image.storedFilename}'
        files.move(image.filePath, relative)
        db.add(m.ItemImage(id=image.id, itemId=item.id, filePath=relative, type=image.type, source='local-upload', originalFilename=image.originalFilename, storedFilename=image.storedFilename, mimeType=image.mimeType, fileSize=image.fileSize, sha256=image.sha256, createdAt=image.createdAt))
        if image.type == 'product' and item.coverImage == '/assets/no-photo.svg':
            item.coverImage = f'/api/images/{image.id}'
        db.delete(image)
    # Keep only a sealed session ID to reject duplicate creates; no draft files remain.
    draft.itemId = item.id
    draft.updatedAt = timestamp()
    for session in db.scalars(select(m.RecognitionSession).where(m.RecognitionSession.draftId == draft_id)):
        session.itemId = item.id
        session.images = [{'filePath': f'/api/images/{i.id}', 'type': i.type} for i in images]
        for candidate in db.scalars(select(m.RecognitionResult).where(m.RecognitionResult.sessionId == session.id)):
            for image in images:
                if image.id in candidate.sourceImage:
                    candidate.sourceImage = f'/api/images/{image.id}'


@router.post('/items/{item_id}/documents/manual', status_code=201)
@router.post('/items/{item_id}/documents', status_code=201)
def upload_manual(item_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    require(db, m.Item, item_id)
    contents, metadata = validate_pdf(file)
    relative = f'documents/manuals/{item_id}/{metadata["storedFilename"]}'
    with file_transaction(db) as files:
        files.write(relative, contents)
        document = m.Document(id=uid(), itemId=item_id, type='manual', filename=metadata['originalFilename'], filePath=relative, **metadata)
        db.add(document)
        db.flush()
        output = row(document)
    return output


@router.get('/items/{item_id}/documents')
def list_documents(item_id: str, db: Session = Depends(get_db)):
    require(db, m.Item, item_id)
    return [row(d) for d in db.scalars(select(m.Document).where(m.Document.itemId == item_id).order_by(m.Document.uploadedAt.desc()))]


def serve(record, download=False):
    path = local_path(record.filePath)
    if not path.is_file():
        raise HTTPException(404, '本地附件文件不存在')
    name = record.originalFilename or getattr(record, 'filename', '') or path.name
    return FileResponse(path, media_type=record.mimeType or 'application/octet-stream', filename=name, content_disposition_type='attachment' if download else 'inline', headers={'X-Content-Type-Options': 'nosniff'})


@router.get('/documents/{document_id}/file')
def document_file(document_id: str, download: bool = False, db: Session = Depends(get_db)):
    return serve(require(db, m.Document, document_id), download)


@router.delete('/documents/{document_id}')
def delete_document(document_id: str, db: Session = Depends(get_db)):
    document = require(db, m.Document, document_id)
    item_id = document.itemId
    with file_transaction(db) as files:
        files.remove(document.filePath)
        db.delete(document)
    prune_empty(f'documents/manuals/{item_id}')
    return {'deleted': document_id}


@router.get('/images/{image_id}')
def image_file(image_id: str, db: Session = Depends(get_db)):
    return serve(require(db, m.ItemImage, image_id))


@router.delete('/images/{image_id}')
def delete_image(image_id: str, db: Session = Depends(get_db)):
    image = require(db, m.ItemImage, image_id)
    item = require(db, m.Item, image.itemId)
    with file_transaction(db) as files:
        if not image.filePath.startswith('/assets/'):
            files.remove(image.filePath)
        if item.coverImage == f'/api/images/{image_id}' or item.coverImage == image.filePath:
            next_image = db.scalar(select(m.ItemImage).where(m.ItemImage.itemId == item.id, m.ItemImage.id != image_id, m.ItemImage.type == 'product'))
            item.coverImage = row(next_image)['filePath'] if next_image else '/assets/no-photo.svg'
        db.delete(image)
    return {'deleted': image_id}


@router.post('/items/{item_id}/images', status_code=201)
def append_images(item_id: str, files: list[UploadFile] = File(...), type: str = Form('product'), db: Session = Depends(get_db)):
    item = require(db, m.Item, item_id)
    if type not in IMAGE_TYPES or not 1 <= len(files) <= 10:
        raise HTTPException(422, '请选择有效类型和 1–10 张图片')
    output = []
    with file_transaction(db) as transaction:
        for upload in files:
            contents, metadata = validate_image(upload)
            relative = f'images/items/{item_id}/{metadata["storedFilename"]}'
            transaction.write(relative, contents)
            image = m.ItemImage(id=uid(), itemId=item_id, filePath=relative, type=type, source='local-upload', **metadata)
            db.add(image)
            db.flush()
            if type == 'product' and item.coverImage == '/assets/no-photo.svg':
                item.coverImage = f'/api/images/{image.id}'
            output.append(row(image))
    return output


@router.patch('/images/{image_id}')
def classify_image(image_id: str, payload: dict, db: Session = Depends(get_db)):
    image = require(db, m.ItemImage, image_id)
    kind = payload.get('type')
    if kind not in IMAGE_TYPES or set(payload) != {'type'}:
        raise HTTPException(422, '资料类型无效')
    item = require(db, m.Item, image.itemId)
    image.type = kind
    if item.coverImage == f'/api/images/{image_id}' and kind != 'product':
        next_image = db.scalar(select(m.ItemImage).where(m.ItemImage.itemId == item.id, m.ItemImage.id != image_id, m.ItemImage.type == 'product'))
        item.coverImage = row(next_image)['filePath'] if next_image else '/assets/no-photo.svg'
    elif kind == 'product' and item.coverImage == '/assets/no-photo.svg':
        item.coverImage = row(image)['filePath']
    return row(image)


@router.get('/items/{item_id}/provenance')
def provenance(item_id: str, db: Session = Depends(get_db)):
    item = require(db, m.Item, item_id)
    results = db.execute(select(m.RecognitionResult).join(m.RecognitionSession, m.RecognitionSession.id == m.RecognitionResult.sessionId).where(m.RecognitionSession.itemId == item_id)).scalars()
    output = []
    for candidate in results:
        current = getattr(item, candidate.field, None)
        if candidate.field == 'purchasePrice':
            current = (current or 0) / 100
        image_id = candidate.sourceImage.split('/')[-1]
        image = db.get(m.ItemImage, image_id)
        recognized = candidate.value
        try:
            equal = float(current) == float(recognized)
        except (ValueError, TypeError):
            equal = str(current) == recognized
        output.append({'field': candidate.field, 'recognizedValue': recognized, 'currentValue': current,
                       'confidence': candidate.confidence, 'sourceImage': f'/api/images/{image.id}' if image else None,
                       'sourceType': image.type if image else '已删除来源图片', 'rawText': candidate.rawText,
                       'manuallyEdited': not equal})
    return output

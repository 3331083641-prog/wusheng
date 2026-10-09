from io import BytesIO
from urllib.parse import unquote

from pypdf import PdfReader
from sqlalchemy.orm import Session

from backend import main, models as m


def test_archive_uses_selected_cover_and_only_product_fallback(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from backend import item_archive
    monkeypatch.setattr(item_archive, 'local_path', lambda relative: tmp_path / relative)
    images = [SimpleNamespace(id=ident, type=kind, filePath=ident + '.png')
              for ident, kind in [('invoice', 'invoice'), ('first', 'product'), ('selected', 'product')]]
    for image in images:
        (tmp_path / image.filePath).write_bytes(b'image fixture')
    item = SimpleNamespace(id='user', isDemo=False, coverImage='/api/images/selected')
    assert item_archive.cover_path(item, images) == tmp_path / 'selected.png'
    item.coverImage = '/assets/no-photo.svg'
    assert item_archive.cover_path(item, images) == tmp_path / 'first.png'
    assert item_archive.cover_path(item, images[:1]) is None


def test_pdf_archive_is_readable_and_item_scoped(client):
    response = client.get('/api/items/laptop/export/pdf')
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/pdf'
    assert response.content.startswith(b'%PDF')
    assert '物生-MacBook Air M2-物品档案.pdf' in unquote(response.headers['content-disposition'])
    reader = PdfReader(BytesIO(response.content))
    assert len(reader.pages) >= 1
    text = '\n'.join(page.extract_text() for page in reader.pages)
    for expected in ['MacBook Air M2', '基本信息', '生命周期', '保修与提醒', '维护记录', '维修记录', '耗材', '资料附件', 'AI / OCR']:
        assert expected in text
    assert 'Sony WH-1000XM6' not in text
    assert 'D:\\' not in text and 'C:\\' not in text
    assert any('/XObject' in page['/Resources'] for page in reader.pages)
    # JSON archive source remains accessible and complete.
    assert client.get('/items/laptop').json()['item']['name'] == 'MacBook Air M2'
    assert client.get('/items/not-an-item/export/pdf').status_code == 404


def test_pdf_metadata_only_paths_redacted_and_long_records_paginate(client):
    with Session(main.engine) as db:
        item = db.get(m.Item, 'laptop')
        item.location = '资料位于D:\\private\\invoice.pdf'
        doc = db.query(m.Document).filter(m.Document.itemId == item.id).first()
        if doc:
            doc.originalFilename = '合成说明书.pdf'
            doc.extractedText = 'PRIVATE_MANUAL_BODY_NEVER_EMBED'
        else:
            db.add(m.Document(itemId=item.id, filename='合成说明书.pdf', originalFilename='合成说明书.pdf',
                              filePath='documents/manuals/test.pdf', extractedText='PRIVATE_MANUAL_BODY_NEVER_EMBED'))
        db.add(m.MaintenanceRecord(itemId=item.id, type='档案分页检查', date='2026-10-01',
                                   nextDueDate='2027-01-01', description='维护长说明。' * 700))
        db.commit()
    response = client.get('/items/laptop/export/pdf')
    assert response.status_code == 200
    reader = PdfReader(BytesIO(response.content))
    text = '\n'.join(page.extract_text() for page in reader.pages)
    assert len(reader.pages) > 2
    assert '维护长说明' in text and '本地路径已省略' in text
    assert '合成说明书.pdf' in text
    assert 'D:\\' not in text and 'PRIVATE_MANUAL_BODY_NEVER_EMBED' not in text
    assert '本档案依据用户本地记录生成' in text


def test_long_basic_fields_and_missing_photo_export_without_layout_error(client):
    fields = {key: '长字段' * 80 for key in ['name', 'brand', 'model', 'purchaseChannel', 'serialNumber', 'location']}
    result = client.post('/items', json={**fields, 'purchaseDate': '2026-01-01'})
    assert result.status_code == 201
    response = client.get('/items/' + result.json()['id'] + '/export/pdf')
    assert response.status_code == 200
    reader = PdfReader(BytesIO(response.content))
    assert len(reader.pages) > 1
    assert '未添加物品图片' in '\n'.join(page.extract_text() for page in reader.pages)

from io import BytesIO
from hashlib import sha256
from pathlib import Path
import pytest
from PIL import Image
from pypdf import PdfWriter
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend import database, models as m, main, storage
from backend.tests.test_workflows import payload


def picture(format='PNG'):
    stream = BytesIO()
    Image.new('RGB', (64, 48), 'white').save(stream, format=format)
    return stream.getvalue()


def pdf(text=None):
    stream = BytesIO()
    if text:
        document = canvas.Canvas(stream)
        document.drawString(40, 750, text)
        document.save()
    else:
        writer = PdfWriter()
        writer.add_blank_page(width=400, height=400)
        writer.write(stream)
    return stream.getvalue()


def draft(client):
    response = client.post('/drafts')
    assert response.status_code == 201
    return response.json()['id']


def image_upload(client, ident, data=None, name='photo.png', mime='image/png', kind='product'):
    return client.post(f'/drafts/{ident}/images', files=[('files', (name, data if data is not None else picture(), mime))], data={'type': kind})


def manual_upload(client, item='laptop', data=None, name='manual.pdf', mime='application/pdf'):
    return client.post(f'/items/{item}/documents/manual', files={'file': (name, data if data is not None else pdf(), mime)})


@pytest.mark.parametrize('name,mime,contents', [('fake.png','image/png',b'bad'), ('photo.exe','image/png',picture()), ('photo.png','text/plain',picture()), ('photo.jpg','image/jpeg',picture())])
def test_image_type_validation(client, name, mime, contents):
    ident = draft(client)
    assert image_upload(client, ident, contents, name, mime).status_code == 415
    assert client.get(f'/drafts/{ident}/images').json() == []


@pytest.mark.parametrize('format,name,mime', [('JPEG','photo.JPG','image/jpeg'), ('PNG','photo.png','image/png'), ('WEBP','photo.webp','image/webp')])
def test_original_image_and_item_binding(client, format, name, mime):
    contents = picture(format)
    ident = draft(client)
    result = image_upload(client, ident, contents, name, mime)
    assert result.status_code == 201, result.text
    image = result.json()[0]
    assert client.get(image['filePath']).content == contents
    assert image['sha256'] == sha256(contents).hexdigest()
    assert image['fileSize'] == len(contents)
    draft_path = database.DATA / 'uploads/drafts' / ident / image['storedFilename']
    assert draft_path.read_bytes() == contents
    response = client.post('/items', json=payload(draftSessionId=ident))
    assert response.status_code == 201, response.text
    item = response.json()
    image = client.get('/items/' + item['id']).json()['images'][0]
    path = database.DATA / 'images/items' / item['id'] / image['storedFilename']
    assert path.read_bytes() == contents
    assert not draft_path.exists()
    assert not draft_path.parent.exists()
    assert item['coverImage'] == image['filePath'] == f'/api/images/{image["id"]}'
    assert client.get(image['filePath']).content == contents
    assert 'D:' not in str(image) and str(database.DATA) not in str(image)
    assert client.post('/items', json=payload(draftSessionId=ident)).status_code == 409
    assert len(client.get('/items/' + item['id']).json()['events']) >= 2
    assert any(r['itemId'] == item['id'] for r in client.get('/snapshot').json()['reminders'])


def test_size_limits(client, monkeypatch):
    # Production thresholds are asserted; exercise rejection without allocating 50MB per test.
    assert storage.IMAGE_LIMIT == 10 * 1024 * 1024
    assert storage.PDF_LIMIT == 50 * 1024 * 1024
    monkeypatch.setattr(storage, 'IMAGE_LIMIT', 100)
    monkeypatch.setattr(storage, 'PDF_LIMIT', 100)
    assert image_upload(client, draft(client), b'x' * 101).status_code == 413
    assert manual_upload(client, data=b'x' * 101).status_code == 413


@pytest.mark.parametrize('name,mime,contents', [('bad.pdf','application/pdf',b'bad'), ('bad.txt','application/pdf',pdf()), ('bad.pdf','text/plain',pdf()), ('bad.pdf','application/pdf',b'%PDF-broken')])
def test_pdf_validation(client, name, mime, contents):
    assert manual_upload(client, data=contents, name=name, mime=mime).status_code in {415, 422}
    assert client.get('/items/laptop/documents').json() == []


def test_document_create_view_download_delete_and_context(client):
    contents = pdf('Battery care: keep the battery cool and dry. Clean with a dry cloth.')
    response = manual_upload(client, data=contents, name='电池说明书.pdf')
    assert response.status_code == 201, response.text
    document = response.json()
    path = database.DATA / 'documents/manuals/laptop' / document['storedFilename']
    assert path.read_bytes() == contents
    assert document['sha256'] == sha256(contents).hexdigest()
    assert document['pageCount'] == 1 and document['fileSize'] == len(contents)
    assert document['originalFilename'] == '电池说明书.pdf'
    assert client.get('/items/laptop/documents').json()[0]['id'] == document['id']
    viewed = client.get(document['filePath'])
    downloaded = client.get(document['filePath'] + '?download=true')
    assert viewed.content == downloaded.content == contents
    assert viewed.headers['content-disposition'].startswith('inline')
    assert downloaded.headers['content-disposition'].startswith('attachment')
    assert document['storedFilename'] not in downloaded.headers['content-disposition']
    answer = client.post('/generate', json={'itemId':'laptop','question':'说明书里有没有写电池保养？'}).json()
    assert '依据已上传说明书' in answer['answer'] and 'Battery' in answer['answer']
    assert answer['sources'][0]['title'] == '电池说明书.pdf'
    unrelated = client.post('/generate', json={'itemId':'suitcase','question':'说明书里有没有写电池保养？'}).json()
    assert '当前未找到该物品的本地说明书' in unrelated['answer']
    assert not unrelated['sources']
    assert client.delete('/documents/' + document['id']).status_code == 200
    assert not path.exists()
    assert client.get('/items/laptop/documents').json() == []
    assert client.get(document['filePath']).status_code == 404


def test_scanned_pdf_and_multiple_filenames(client):
    first = manual_upload(client).json()
    second = manual_upload(client).json()
    assert first['extractedText'] == '' and first['pageCount'] == 1
    assert first['storedFilename'] != second['storedFilename']
    assert len(client.get('/items/laptop/documents').json()) == 2


def test_draft_delete_types_and_limits(client):
    ident = draft(client)
    image = image_upload(client, ident, kind='receipt').json()[0]
    path = database.DATA / 'uploads/drafts' / ident / image['storedFilename']
    assert image['type'] == 'receipt'
    assert client.patch(f'/drafts/{ident}/images/{image["id"]}', json={'type':'manual_image'}).json()['type'] == 'manual_image'
    assert client.delete(f'/drafts/{ident}/images/{image["id"]}').status_code == 200
    assert not path.exists()
    files = [('files', (f'{n}.png', picture(), 'image/png')) for n in range(10)]
    assert client.post(f'/drafts/{ident}/images',files=files,data={'type':'label'}).status_code == 201
    assert image_upload(client, ident).status_code == 422
    assert client.delete('/drafts/' + ident).status_code == 200
    assert not (database.DATA / 'uploads/drafts' / ident).exists()


def test_failed_batch_rolls_back_files_and_records(client):
    ident = draft(client)
    response = client.post(f'/drafts/{ident}/images',files=[('files',('good.png',picture(),'image/png')),('files',('bad.png',b'bad','image/png'))],data={'type':'product'})
    assert response.status_code == 415
    assert client.get(f'/drafts/{ident}/images').json() == []
    assert not list((database.DATA / 'uploads/drafts').rglob('*.png'))


def test_attach_failure_restores_draft_and_database(client, monkeypatch):
    ident = draft(client)
    image = image_upload(client, ident).json()[0]
    before = len(client.get('/items').json())
    with monkeypatch.context() as patch:
        def failure(*args, **kwargs): raise RuntimeError('synthetic database failure')
        patch.setattr(main, 'sync_item', failure)
        with pytest.raises(RuntimeError):
            client.post('/items', json=payload(draftSessionId=ident))
    assert len(client.get('/items').json()) == before
    assert client.get(image['filePath']).content == picture()
    assert len(client.get(f'/drafts/{ident}/images').json()) == 1
    assert not list((database.DATA / 'images/items').rglob('*.png'))


def test_delete_failure_restores_document_file(client, monkeypatch):
    document = manual_upload(client).json()
    with monkeypatch.context() as patch:
        def failure(self): raise RuntimeError('synthetic commit failure')
        patch.setattr(Session, 'commit', failure)
        with pytest.raises(RuntimeError): client.delete('/documents/' + document['id'])
    assert client.get(document['filePath']).status_code == 200
    assert len(client.get('/items/laptop/documents').json()) == 1


def test_item_delete_cascades_attachments_and_business_records(client):
    ident = draft(client)
    image_upload(client, ident)
    item = client.post('/items', json=payload(draftSessionId=ident)).json()
    document = manual_upload(client, item=item['id']).json()
    image = client.get('/items/' + item['id']).json()['images'][0]
    c = client.post('/consumables', json={'itemId':item['id'],'name':'测试滤网','currentStock':2}).json()
    client.post('/items/' + item['id'] + '/maintenance',json={'type':'清洁','date':item['purchaseDate'],'intervalDays':30})
    client.post('/repairs',json={'itemId':item['id'],'issue':'测试','reportDate':item['purchaseDate']})
    assert client.delete('/items/' + item['id']).status_code == 200
    assert client.get(document['filePath']).status_code == 404
    assert client.get(image['filePath']).status_code == 404
    assert not (database.DATA / 'images/items' / item['id']).exists()
    assert not (database.DATA / 'documents/manuals' / item['id']).exists()
    with Session(main.engine) as db:
        for model in [m.ItemImage,m.Document,m.MaintenanceRecord,m.RepairRecord,m.Consumable,m.Reminder,m.LifecycleEvent]:
            assert not list(db.scalars(select(model).where(model.itemId == item['id'])))
        assert not db.scalar(select(m.ConsumptionRecord.id).where(m.ConsumptionRecord.consumableId == c['id']))


def test_all_core_consumable_and_ac_accessory_relationships(client):
    pairs={'purifier-filter':'purifier','detergent':'washer','ink-cartridge':'printer','capsules':'coffee','brushhead':'toothbrush','robot-filter':'robot','ac-filter':'ac'}
    cs=client.get('/snapshot').json()['consumables']
    for c in cs:
        assert c['itemId'] == pairs[c['id']]
        assert c['createdAt'] and c['updatedAt']
        assert any(v['id'] == c['id'] for v in client.get('/items/' + c['itemId']).json()['consumables'])


def test_disk_records_survive_new_app_lifespan(client):
    from fastapi.testclient import TestClient
    ident = draft(client)
    image_upload(client, ident)
    item = client.post('/items', json=payload(draftSessionId=ident)).json()
    document = manual_upload(client, item=item['id']).json()
    main.engine.dispose()
    with TestClient(main.app) as restarted:
        detail = restarted.get('/items/' + item['id']).json()
        assert detail['documents'][0]['id'] == document['id']
        assert restarted.get(detail['images'][0]['filePath']).content == picture()
        assert restarted.get(document['filePath']).content == pdf()


def test_expired_draft_cleanup_and_safe_names(client):
    ident = draft(client)
    image = image_upload(client, ident, name='../../photo.png').json()[0]
    assert image['originalFilename'] == 'photo.png'
    assert '..' not in image['storedFilename']
    with Session(main.engine) as db:
        db.get(m.DraftSession, ident).updatedAt = '2000-01-01T00:00:00+00:00'
        db.commit()
    draft(client)
    assert client.get(image['filePath']).status_code == 404
    assert not (database.DATA / 'uploads/drafts' / ident).exists()


def test_additive_schema_migration_preserves_old_rows(tmp_path):
    from sqlalchemy import text, inspect
    old = database.make_engine(f'sqlite:///{tmp_path / "old.db"}')
    with old.begin() as connection:
        for table in ['item_images', 'documents', 'consumables', 'recognition_sessions']:
            connection.execute(text(f'CREATE TABLE {table} (id TEXT PRIMARY KEY, legacyValue TEXT)'))
            connection.execute(text(f"INSERT INTO {table} VALUES ('existing', 'preserve me')"))
    database.migrate_schema(old)
    database.migrate_schema(old)
    with old.connect() as connection:
        for table in ['item_images', 'documents', 'consumables', 'recognition_sessions']:
            assert connection.execute(text(f'SELECT legacyValue FROM {table}')).scalar() == 'preserve me'
        assert 'sha256' in {c['name'] for c in inspect(connection).get_columns('documents')}
    old.dispose()


def test_disk_failure_has_clear_error_without_orphan(client, monkeypatch):
    ident = draft(client)
    with monkeypatch.context() as patch:
        def failure(*args, **kwargs): raise PermissionError('synthetic inaccessible disk')
        patch.setattr(storage.FileTransaction, 'write', failure)
        response = image_upload(client, ident)
        assert response.status_code == 500
        assert '无法读写本地附件' in response.json()['detail']
    assert client.get(f'/drafts/{ident}/images').json() == []

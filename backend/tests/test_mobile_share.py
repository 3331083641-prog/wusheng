"""Token-scoped mobile archive: real disk files, conservative permissions and live data."""
from io import BytesIO
from datetime import datetime, timedelta, timezone
import json
import pytest
from PIL import Image
from pypdf import PdfWriter
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend import main, sharing, models as m, database


@pytest.fixture
def lan(client, monkeypatch):
    monkeypatch.setenv('WUSHENG_SHARE_MODE', 'lan-ready')
    monkeypatch.setattr(sharing, 'lan_addresses', lambda: ['192.168.1.8'])
    return client


def share(client, item='printer', **options):
    response = client.post(f'/items/{item}/share?regenerate=true', json={'options': options})
    assert response.status_code == 200, response.text
    return response.json()


def pdf(client, item='printer', name='合成说明书.pdf'):
    content = BytesIO(); writer = PdfWriter(); writer.add_blank_page(width=100, height=100); writer.write(content)
    response = client.post(f'/items/{item}/documents/manual', files={'file': (name, content.getvalue(), 'application/pdf')})
    assert response.status_code == 201, response.text
    return response.json()


def image(client, item):
    content = BytesIO(); Image.new('RGB', (32, 24), 'green').save(content, format='PNG')
    response = client.post(f'/items/{item}/images', data={'type': 'product'}, files=[('files', ('product.png', content.getvalue(), 'image/png'))])
    assert response.status_code == 201, response.text
    return response.json()[0]


@pytest.mark.parametrize('item', list(sharing.ITEM_ASSETS))
def test_formal_demo_images_resolve_and_are_available(lan, item, monkeypatch):
    # CI runs pytest before Vite build. Serve the exact source assets Vite copies,
    # rather than relying on a developer's ignored frontend/dist directory.
    monkeypatch.setenv('WUSHENG_FRONTEND_DIST', str(database.ROOT / 'frontend/public'))
    link = share(lan, item)
    data = lan.get('/share-data/' + link['token']).json()
    assert data['item']['coverImage'] == sharing.ITEM_ASSETS[item]['src']
    assert data['images'][0]['src'] == data['item']['coverImage']
    with TestClient(main.app, client=('192.168.1.9', 3210)) as remote:
        response = remote.get(data['images'][0]['src'])
        assert response.status_code == 200 and response.headers['content-type'] == 'image/png'
        assert response.content.startswith(b'\x89PNG')


def test_uploaded_cover_gallery_deletion_and_cross_item_isolation(lan):
    item = lan.post('/items', json={'name': '惠普打印机', 'purchaseDate': '2026-01-01'}).json()['id']
    link = share(lan, item)
    url = '/share-data/' + link['token']
    assert lan.get(url).json()['images'] == []  # Identical name does not guess a Demo image.
    first, second = image(lan, item), image(lan, item)
    with Session(main.engine) as db:
        db.get(m.Item, item).coverImage = second['filePath']; db.commit()
    data = lan.get(url).json()
    assert data['images'][0]['src'].endswith('/' + second['id'])
    with TestClient(main.app, client=('192.168.1.9', 3210)) as remote:
        response = remote.get(data['images'][0]['src'])
        assert response.status_code == 200 and response.headers['cache-control'] == 'no-store'
        another = image(lan, 'washer')
        assert remote.get(url + '/images/' + another['id']).status_code == 404
        assert remote.get(second['filePath']).status_code == 403
    assert lan.delete('/images/' + second['id']).status_code == 200
    assert lan.get(url).json()['images'][0]['src'].endswith('/' + first['id'])
    assert lan.get(data['images'][0]['src']).status_code == 404
    assert lan.delete('/images/' + first['id']).status_code == 200
    assert lan.get(url).json()['images'] == []


def test_manual_selection_headers_range_download_and_no_cross_item_access(lan):
    selected, private = pdf(lan), pdf(lan, name='仅本机.pdf')
    other = pdf(lan, 'washer')
    link = share(lan, showManualFiles=True, showManualDownloads=True, manualDocumentIds=[selected['id']])
    base = '/api/share-data/' + link['token']
    with TestClient(main.app, client=('192.168.1.9', 3210)) as remote:
        data = remote.get(base).json()
        assert len(data['manuals']) == 1 and data['manuals'][0]['name'] == '合成说明书.pdf'
        url = data['manuals'][0]['viewUrl']
        response = remote.get(url)
        assert response.status_code == 200 and response.content.startswith(b'%PDF')
        assert response.headers['content-type'] == 'application/pdf'
        assert response.headers['cache-control'] == 'no-store'
        assert response.headers['x-content-type-options'] == 'nosniff'
        assert response.headers['content-disposition'].startswith('inline;')
        assert 'filename*=UTF-8' in response.headers['content-disposition']
        assert remote.get(url, headers={'Range': 'bytes=0-3'}).content == b'%PDF'
        assert remote.get(url + '?download=true').headers['content-disposition'].startswith('attachment;')
        for doc in [private, other]:
            assert remote.get(base + '/manuals/' + doc['id'] + '/file').status_code == 404
        assert remote.get('/api/documents/' + selected['id'] + '/file').status_code == 403
        assert remote.get('/uploads/demo-care-guide.pdf').status_code == 403
        assert 'D:\\' not in json.dumps(data) and 'filePath' not in json.dumps(data)
    assert lan.post('/items/printer/share?regenerate=true', json={'options': {'showManualFiles': True, 'manualDocumentIds': [other['id']]}}).status_code == 422


def test_new_manuals_private_until_future_authorized_and_deletion_is_live(lan):
    first, hidden = pdf(lan), pdf(lan, name='原有未授权.pdf')
    link = share(lan, showManualFiles=True, manualDocumentIds=[first['id']])
    base = '/share-data/' + link['token']
    later = pdf(lan, name='新上传.pdf')
    assert len(lan.get(base).json()['manuals']) == 1
    assert lan.get(base + '/manuals/' + later['id'] + '/file').status_code == 404
    assert lan.get(base + '/manuals/' + first['id'] + '/file?download=true').status_code == 404
    future = share(lan, showManualFiles=True, shareFutureManuals=True, manualDocumentIds=[first['id']])
    base = '/share-data/' + future['token']
    latest = pdf(lan, name='持续授权新增.pdf')
    assert {d['name'] for d in lan.get(base).json()['manuals']} == {'合成说明书.pdf', '持续授权新增.pdf'}
    for doc in [hidden, later]: assert lan.get(base + '/manuals/' + doc['id'] + '/file').status_code == 404
    url = base + '/manuals/' + latest['id'] + '/file'
    assert lan.get(url).status_code == 200
    assert lan.delete('/documents/' + latest['id']).status_code == 200
    assert lan.get(url).status_code == 404
    assert len(lan.get(base).json()['manuals']) == 1
    replacement = pdf(lan, name='持续授权新增.pdf')
    assert lan.get(base + '/manuals/' + replacement['id'] + '/file').status_code == 200


def test_manual_names_legacy_defaults_expiry_revoke_and_item_delete(lan):
    document = pdf(lan)
    link = share(lan, showManualNames=True)
    base = '/share-data/' + link['token']
    assert lan.get(base).json()['manuals'] == [{'name': document['originalFilename'], 'readable': False}]
    assert lan.get(base + '/manuals/' + document['id'] + '/file').status_code == 404
    link = share(lan, showManualFiles=True, manualDocumentIds=[document['id']])
    url = '/share-data/' + link['token'] + '/manuals/' + document['id'] + '/file'
    with Session(main.engine) as db:
        db.get(m.ShareLink, link['id']).expiresAt = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(); db.commit()
    assert lan.get(url).status_code == 404
    link = share(lan, showManualFiles=True, manualDocumentIds=[document['id']])
    url = '/share-data/' + link['token'] + '/manuals/' + document['id'] + '/file'
    assert lan.delete('/items/printer/share').status_code == 200
    assert lan.get(url).status_code == 404
    link = share(lan, showManualFiles=True, manualDocumentIds=[document['id']])
    url = '/share-data/' + link['token'] + '/manuals/' + document['id'] + '/file'
    assert lan.delete('/items/printer').status_code == 200 and lan.get(url).status_code == 404


def test_existing_link_does_not_gain_new_permissions(lan):
    document = pdf(lan)
    link = share(lan)
    with Session(main.engine) as db:
        db.get(m.ShareLink, link['id']).options = {'showManualNames': True, 'showWarranty': True}
        db.commit()
    data = lan.get('/share-data/' + link['token']).json()
    assert data['manuals'] == [{'name': document['originalFilename'], 'readable': False}]
    for field in ('showManualFiles', 'shareFutureManuals', 'showPurchasePrice', 'showLocation', 'showManualDownloads'):
        assert data['options'][field] is False
    assert lan.get('/share-data/' + link['token'] + '/manuals/' + document['id'] + '/file').status_code == 404


def test_manual_missing_disk_and_wrong_document_type_denied(lan):
    document = pdf(lan)
    link = share(lan, showManualFiles=True, manualDocumentIds=[document['id']])
    url = '/share-data/' + link['token'] + '/manuals/' + document['id'] + '/file'
    with Session(main.engine) as db:
        record = db.get(m.Document, document['id'])
        record.type = 'invoice'
        db.commit()
    assert lan.get(url).status_code == 404
    with Session(main.engine) as db:
        record = db.get(m.Document, document['id'])
        record.type = 'manual'
        filename = database.DATA / record.filePath
        db.commit()
    filename.unlink()
    assert lan.get(url).status_code == 404


@pytest.mark.parametrize('path', ['../../outside.pdf', 'wusheng.db', 'documents/manuals/washer/other.pdf'])
def test_manual_path_traversal_or_wrong_directory_denied(lan, path):
    document = pdf(lan)
    link = share(lan, showManualFiles=True, manualDocumentIds=[document['id']])
    with Session(main.engine) as db:
        db.get(m.Document, document['id']).filePath = path; db.commit()
    assert lan.get('/share-data/' + link['token'] + '/manuals/' + document['id'] + '/file').status_code == 404


def test_permissions_dynamic_data_and_no_fake_lifecycle(lan):
    with Session(main.engine) as db:
        item = db.get(m.Item, 'printer'); item.purchasePrice = 123456; item.purchaseChannel = 'PRIVATE CHANNEL'; item.location = 'PRIVATE LOCATION'; item.serialNumber = 'PRIVATE SERIAL'
        db.add(m.MaintenanceRecord(itemId=item.id, date='2026-01-01', type='清洁', nextDueDate='2026-10-01', description='PRIVATE NOTE', cost=2500))
        db.add(m.LifecycleEvent(itemId=item.id, type='repair', date='2099-01-01', title='PRIVATE FUTURE', relatedId='future'))
        db.commit()
    link = share(lan)
    base = '/share-data/' + link['token']
    data = lan.get(base).json()
    assert 'PRIVATE' not in json.dumps(data)
    assert data['maintenance'] == [] and data['repairs'] == []
    assert 'currentStock' not in json.dumps(data)
    assert all(e['date'] != '2099-01-01' for e in data['events'])
    assert next(s for s in data['lifecycle'] if s['type'] == 'repair')['state'] == 'pending'
    assert next(s for s in data['lifecycle'] if s['type'] == 'purchase')['date'] is None
    with Session(main.engine) as db:
        db.get(m.Item, 'printer').name = '修改后的打印机'
        db.query(m.Consumable).filter_by(itemId='printer').first().currentStock = 8
        db.commit()
    assert lan.get(base).json()['item']['name'] == '修改后的打印机'
    link = share(lan, showPurchasePrice=True, showPurchaseChannel=True, showLocation=True, showMaintenance=True, showConsumableStock=True)
    data = lan.get('/share-data/' + link['token']).json()
    assert data['item']['purchasePrice'] == 1234.56
    assert data['item']['purchaseChannel'] == 'PRIVATE CHANNEL'
    assert data['maintenance'][0]['type'] == '清洁' and 'description' not in data['maintenance'][0]
    assert any(r['type'] == '维护任务' for r in data['reminders'])
    assert data['consumables'][0]['currentStock'] == 8
    assert 'PRIVATE SERIAL' not in json.dumps(data)


def test_share_html_title_has_no_english_and_is_not_cached(lan, tmp_path, monkeypatch):
    (tmp_path / 'index.html').write_text('<html><title>物生 Wusheng</title><div id="root"></div></html>', encoding='utf-8')
    monkeypatch.setenv('WUSHENG_FRONTEND_DIST', str(tmp_path))
    response = lan.get('/share/example', headers={'accept': 'text/html'})
    assert 'Wusheng' not in response.text and response.headers['cache-control'] == 'no-store'


def test_superseded_maintenance_not_shown_as_current_overdue_task(lan):
    from backend.clock import today
    now = today()
    with Session(main.engine) as db:
        for days_ago, next_days in [(60, -30), (1, 30)]:
            db.add(m.MaintenanceRecord(itemId='printer', type='清洁', date=(now - timedelta(days=days_ago)).isoformat(), nextDueDate=(now + timedelta(days=next_days)).isoformat()))
        db.commit()
    link = share(lan, showMaintenance=True)
    data = lan.get('/share-data/' + link['token']).json()
    assert data['item']['status'] == '正常使用'
    assert len(data['maintenance']) == 2 and not any(r['needsMaintenance'] for r in data['maintenance'])

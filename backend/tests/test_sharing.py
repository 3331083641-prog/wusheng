from backend import sharing
import pytest


def test_local_cannot_generate_phone_qr(client, monkeypatch):
    monkeypatch.delenv('WUSHENG_SHARE_MODE', raising=False)
    assert client.get('/network/share-info').json()['mode'] == 'local'
    assert client.post('/items/headphones/share').status_code == 409


def test_lan_tokens_readonly_and_revoke(client, monkeypatch):
    monkeypatch.setenv('WUSHENG_SHARE_MODE', 'lan')
    monkeypatch.setattr(sharing, 'lan_addresses', lambda: ['10.2.3.4'])
    first = client.post('/items/headphones/share').json()
    assert first['url'].startswith('http://10.2.3.4:8000/share/')
    assert client.post('/items/headphones/share').json()['token'] == first['token']
    data = client.get('/api/share-data/' + first['token']).json()
    assert data['item']['name'] == 'Sony WH-1000XM6'
    assert 'purchasePrice' not in data['item'] and 'filePath' not in str(data)
    assert client.post('/share-data/' + first['token']).status_code == 405
    second = client.post('/items/headphones/share?regenerate=true').json()
    assert client.get('/share-data/' + first['token']).status_code == 404
    assert client.get('/share-data/' + second['token']).status_code == 200
    assert client.delete('/items/headphones/share').status_code == 200
    assert client.get('/share-data/' + second['token']).status_code == 404


def test_spa_and_api_prefix(client, tmp_path, monkeypatch):
    (tmp_path/'index.html').write_text('<div id="root"></div>')
    monkeypatch.setenv('WUSHENG_FRONTEND_DIST', str(tmp_path))
    assert client.get('/share/example').status_code == 200
    assert client.get('/api/health').json()['status'] == 'ok'
    assert 'id="root"' in client.get('/items/headphones', headers={'accept':'text/html'}).text
    assert client.get('/api/items/headphones').json()['item']['name'] == 'Sony WH-1000XM6'
    assert client.get('/api/nonexistent').status_code == 404
    assert client.get('/assets/absent.png').status_code == 404
    assert client.post('/items', headers={'origin':'https://example.com'}, json={}).status_code == 403


def test_remote_only_token_scoped_reads(client, monkeypatch):
    from fastapi.testclient import TestClient
    from backend.main import app
    monkeypatch.setenv('WUSHENG_SHARE_MODE', 'lan')
    monkeypatch.setattr(sharing, 'lan_addresses', lambda: ['10.2.3.4'])
    token=client.post('/items/headphones/share').json()['token']
    with TestClient(app, client=('10.2.3.5', 4321)) as remote:
        assert remote.get('/api/share-data/'+token).status_code==200
        assert remote.get('/api/items/headphones').status_code==403
        assert remote.get('/api/backup').status_code==403
        assert remote.post('/api/items/headphones/share').status_code==403
        assert remote.get('/api/share-data/invalid').status_code==404


def test_lan_ready_detection_and_multiple_adapters(client, monkeypatch):
    monkeypatch.setenv('WUSHENG_SHARE_MODE', 'lan-ready')
    monkeypatch.setattr(sharing, 'lan_addresses', lambda: ['10.2.3.4', '192.168.1.8'])
    info = client.get('/api/network/share-info').json()
    assert info['mode'] == 'lan-ready' and info['reachable']
    assert len(info['lanAddresses']) == 2
    link = client.post('/items/laptop/share?address=192.168.1.8').json()
    assert link['url'].startswith('http://192.168.1.8:8000/share/')
    assert client.post('/items/laptop/share?address=127.0.0.1').status_code == 422
    monkeypatch.setattr(sharing, 'lan_addresses', lambda: [])
    assert client.get('/health').status_code == 200
    assert client.get('/network/share-info').json()['reachable'] is False
    assert client.post('/items/laptop/share').status_code == 409


@pytest.mark.parametrize('endpoint', ['/items', '/backup', '/generate', '/reminders', '/documents', '/repairs', '/consumables', '/drafts', '/network/share-info', '/items/laptop/export/pdf'])
def test_remote_management_denied_even_with_forwarded_loopback(client, endpoint):
    from fastapi.testclient import TestClient
    from backend.main import app
    with TestClient(app, client=('192.168.1.9', 4321)) as remote:
        for prefix in ['', '/api']:
            for method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
                response = remote.request(method, prefix + endpoint, headers={'X-Forwarded-For': '127.0.0.1'})
                assert response.status_code == 403, (method, prefix + endpoint)


def test_remote_share_and_static_reads_but_no_public_writes(client, tmp_path, monkeypatch):
    import shutil
    from fastapi.testclient import TestClient
    from backend.main import app
    monkeypatch.setenv('WUSHENG_SHARE_MODE', 'lan-ready')
    monkeypatch.setattr(sharing, 'lan_addresses', lambda: ['192.168.1.8'])
    (tmp_path / 'index.html').write_text('<div id="root"></div>')
    shutil.copytree(sharing.ROOT / 'frontend/public/assets/branding', tmp_path / 'assets/branding')
    shutil.copy(sharing.ROOT / 'frontend/public/assets/no-photo.svg', tmp_path / 'assets/no-photo.svg')
    monkeypatch.setenv('WUSHENG_FRONTEND_DIST', str(tmp_path))
    token = client.post('/items/laptop/share').json()['token']
    with TestClient(app, client=('192.168.1.9', 4321)) as remote:
        for url in ['/', '/share/' + token, '/api/share-data/' + token]:
            assert remote.get(url, headers={'accept': 'text/html'}).status_code == 200
            for method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                assert remote.request(method, url).status_code == 403
        for url in ['/assets/branding/wusheng-eco-ring-logo.png', '/assets/no-photo.svg']:
            assert remote.get(url).status_code == 200
        assert remote.get('/api/share-data/not-valid').status_code == 404

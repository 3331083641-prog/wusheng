from backend import sharing


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

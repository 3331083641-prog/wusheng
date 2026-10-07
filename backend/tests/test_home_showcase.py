from datetime import timedelta
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from backend import main, models as m
from backend.clock import today


def entry(client, ident):
    return next(e for e in client.get('/api/home/showcase').json()['items'] if e['item']['id'] == ident)


def payload(name='轮播测试物品'):
    return dict(name=name, brand='测试品牌', model='TEST-11', purchaseDate=today().isoformat(), warrantyMonths=0)


@pytest.mark.parametrize('count', [0, 1, 2, 10])
def test_showcase_matches_database_count(client, count):
    items = client.get('/items').json()
    for item in items[count:]:
        assert client.delete('/items/' + item['id']).status_code == 200
    result = client.get('/home/showcase').json()
    assert result['total'] == len(result['items']) == count
    assert {e['item']['id'] for e in result['items']} == {i['id'] for i in client.get('/items').json()}


def test_showcase_crud_and_missing_data(client):
    response = client.post('/items', json=payload())
    assert response.status_code == 201
    ident = response.json()['id']
    assert client.get('/home/showcase').json()['total'] == 11
    e = entry(client, ident)
    assert e['item']['warrantyDaysLeft'] is None
    assert e['item']['nextMaintenance'] is None
    assert e['consumable']['title'] == '暂无耗材'
    assert e['item']['coverImage'] == '/assets/no-photo.svg'
    assert [n['type'] for n in e['lifecycle'] if n['date']] == ['purchase', 'use']
    assert client.put('/items/' + ident, json=payload('修改后的档案')).status_code == 200
    assert entry(client, ident)['item']['name'] == '修改后的档案'
    assert client.delete('/items/' + ident).status_code == 200
    assert client.get('/home/showcase').json()['total'] == 10


def test_showcase_real_maintenance_and_no_future_events(client):
    ident = client.post('/items', json={**payload(), 'warrantyMonths': 12}).json()['id']
    assert client.post(f'/items/{ident}/maintenance', json={'type': '清洁滤网', 'date': today().isoformat(), 'intervalDays': 30}).status_code == 201
    e = entry(client, ident)
    detail = client.get('/items/' + ident).json()
    assert e['item']['nextMaintenance'] == detail['item']['nextMaintenance']
    assert e['maintenanceType'] == '清洁滤网'
    nodes = {n['type']: n for n in e['lifecycle']}
    assert nodes['maintenance']['date'] == today().isoformat()
    assert nodes['warranty']['date'] is None
    assert nodes['return']['date'] is None
    assert nodes['repair']['state'] == nodes['retired']['state'] == 'pending'


def test_showcase_expired_warranty_and_cover_priority(client):
    ident = client.post('/items', json={**payload(), 'purchaseDate': (today() - timedelta(days=400)).isoformat(), 'warrantyMonths': 12}).json()['id']
    with Session(main.engine) as db:
        db.add(m.ItemImage(itemId=ident, type='product', filePath='/assets/test-product.png'))
        db.commit()
    e = entry(client, ident)
    assert e['chip'] == {'label': '已过保', 'tone': 'red'}
    assert e['item']['warrantyDaysLeft'] < 0
    assert e['item']['coverImage'] == '/assets/test-product.png'
    with Session(main.engine) as db:
        db.get(m.Item, ident).coverImage = '/assets/custom-cover.png'
        db.commit()
    assert entry(client, ident)['item']['coverImage'] == '/assets/custom-cover.png'


def test_showcase_reuses_consumable_prediction_and_excludes_private_fields(client):
    for e in client.get('/home/showcase').json()['items']:
        detail = client.get('/items/' + e['item']['id']).json()
        if detail['consumables']:
            assert e['consumable']['title'] != '暂无耗材'
        assert 'serialNumber' not in e['item'] and 'purchasePrice' not in e['item']
        for node in e['lifecycle']:
            if node['date']:
                assert any(event['date'] == node['date'] for event in detail['events'])


def test_showcase_remains_management_only(client):
    with TestClient(main.app, client=('10.2.3.5', 4321)) as remote:
        assert remote.get('/api/home/showcase').status_code == 403


@pytest.mark.parametrize('configured,available,active', [('evidence', True, 'evidence'), ('ollama', True, 'ollama'), ('ollama', False, 'evidence')])
def test_health_reports_actual_provider_and_model(client, monkeypatch, configured, available, active):
    from backend import ai_engine
    monkeypatch.setenv('WUSHENG_AI_PROVIDER', configured)
    monkeypatch.setenv('WUSHENG_OLLAMA_MODEL', 'qwen-test')
    class Response:
        def raise_for_status(self):
            if not available:
                raise RuntimeError('synthetic offline model')
        def json(self):
            return {'models': [{'name': 'qwen-test'}]}
    monkeypatch.setattr(ai_engine.httpx, 'get', lambda *args, **kwargs: Response())
    monkeypatch.setattr(ai_engine, 'factory', ai_engine.ProviderFactory())
    health = client.get('/api/health').json()
    assert health['configuredProvider'] == configured
    assert health['activeProvider'] == active
    assert health['model'] == ('qwen-test' if configured == 'ollama' else None)
    assert bool(health['fallbackReason']) == (configured != active)

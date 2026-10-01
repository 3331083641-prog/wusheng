from pathlib import Path
from datetime import timedelta
from backend.clock import today


def payload(**overrides):
    return {'name':'测试耳机','brand':'Sony','model':'WH-1000XM6','category':'数码','purchaseDate':today().isoformat(),'purchasePrice':2999,'warrantyMonths':12,'returnWindowDays':7,**overrides}


def test_seed_consistency_and_reminder_idempotence(client):
    one=client.get('/snapshot').json()
    two=client.get('/snapshot').json()
    assert len(one['items'])==10==one['stats']['itemCount']
    assert {r['id'] for r in one['reminders']}=={r['id'] for r in two['reminders']}
    detail=client.get('/items/headphones').json()
    assert len(detail['events'])==len(client.get('/items/headphones').json()['events'])


def test_manual_crud_and_generated_dates(client):
    result=client.post('/items',json=payload())
    assert result.status_code==201,result.text
    item=result.json()
    assert item['coverImage'] == '/assets/no-photo.svg'  # Never invent a product photo.
    assert item['returnDeadline']==(today()+timedelta(days=7)).isoformat()
    assert item['purchasePrice']==2999
    snap=client.get('/snapshot').json()
    assert snap['stats']['itemCount']==11
    assert len([r for r in snap['reminders'] if r['itemId']==item['id']])==2
    update=client.put('/items/'+item['id'],json=payload(name='已编辑耳机',purchasePrice=1234.56))
    assert update.status_code==200
    assert update.json()['purchasePrice']==1234.56
    assert client.get('/items?q=已编辑').json()[0]['id']==item['id']
    assert client.delete('/items/'+item['id']).status_code==200
    assert client.get('/items/'+item['id']).status_code==404


def test_reminder_snooze_and_complete_survive_read(client):
    record=client.get('/snapshot').json()['reminders'][0]
    res=client.patch('/reminders/'+record['id'],json={'action':'snooze','days':7})
    assert res.status_code==200
    expected=res.json()['dueDate']
    assert next(r for r in client.get('/snapshot').json()['reminders'] if r['id']==record['id'])['dueDate']==expected
    client.patch('/reminders/'+record['id'],json={'action':'complete'})
    assert next(r for r in client.get('/snapshot').json()['reminders'] if r['id']==record['id'])['status']=='completed'


def test_maintenance_updates_event_and_reminder(client):
    response=client.post('/items/headphones/maintenance',json={'type':'耳垫清洁','date':today().isoformat(),'intervalDays':30,'cost':12.3})
    assert response.status_code==201,response.text
    record=response.json()
    detail=client.get('/items/headphones').json()
    assert any(e['relatedId']==record['id'] and e['type']=='maintenance' for e in detail['events'])
    assert any(r['relatedId']==record['id'] for r in client.get('/snapshot').json()['reminders'])


def test_case_b_prediction_and_stock_transaction(client):
    snapshot=client.get('/snapshot').json()
    c=next(c for c in snapshot['consumables'] if c['id']=='purifier-filter')
    assert c['estimatedDaysLeft']==12
    old_spend=snapshot['stats']['consumableSpend']
    result=client.post('/consumables/purifier-filter/restock',json={'date':today().isoformat(),'quantity':2,'cost':100})
    assert result.status_code==201
    assert result.json()['currentStock']==3
    assert result.json()['estimatedDaysLeft']==36
    assert client.get('/snapshot').json()['stats']['consumableSpend']==old_spend+100
    failed=client.post('/consumables/purifier-filter/consume',json={'date':today().isoformat(),'quantity':100})
    assert failed.status_code==422
    assert next(c for c in client.get('/snapshot').json()['consumables'] if c['id']=='purifier-filter')['currentStock']==3
    assert client.post('/consumables/purifier-filter/consume',json={'date':today().isoformat(),'quantity':1}).json()['currentStock']==2


def test_case_c_repair_progress_cost_and_lifecycle(client):
    before=client.get('/snapshot').json()['stats']['repairSpend']
    record=client.post('/repairs',json={'itemId':'washer','issue':'脱水异响','reportDate':today().isoformat()}).json()
    assert client.patch('/repairs/'+record['id'],json={'status':'已完成','cost':450}).status_code==422
    for state in ['诊断中','维修中','已完成']:
        result=client.patch('/repairs/'+record['id'],json={'status':state,'cost':450,'description':'轴承组件更换（合成测试）'})
        assert result.status_code==200,result.text
    detail=client.get('/items/washer').json()
    assert any(e['type']=='repair' and e['relatedId']==record['id'] for e in detail['events'])
    assert any(e['type']=='use' and e['relatedId']=='repair:'+record['id'] for e in detail['events'])
    assert client.get('/snapshot').json()['stats']['repairSpend']==before+450


def test_case_a_real_local_ocr_save(client):
    root=Path(__file__).resolve().parents[2]
    receipt=root/'docs/references/demo-receipt.png'
    photo=root/'frontend/public/assets/headphones-detail.jpg'
    response=client.post('/recognize',files=[('files',('headphones.jpg',photo.read_bytes(),'image/jpeg')),('files',('receipt.png',receipt.read_bytes(),'image/png'))],data={'types':['product','receipt']})
    assert response.status_code==200,response.text
    recognition=response.json()
    assert recognition['fields']['brand']['value']=='Sony'
    assert recognition['fields']['model']['value']=='WH-1000XM6'
    assert float(recognition['fields']['purchasePrice']['value'])==2999
    fields={field:c['value'] for field,c in recognition['fields'].items()}
    # Human confirms fields; test uses today's date independent of static fixture.
    fields.update(name='Sony OCR 测试耳机',purchaseDate=today().isoformat(),purchasePrice=2999,warrantyMonths=12,returnWindowDays=7)
    result=client.post('/items',json={**fields,'recognitionSessionId':recognition['sessionId']})
    assert result.status_code==201,result.text
    ident=result.json()['id']
    assert len(client.get('/items/'+ident).json()['images'])==2
    assert any(r['itemId']==ident for r in client.get('/snapshot').json()['reminders'])
    assert client.post('/items',json={**fields,'recognitionSessionId':recognition['sessionId']}).status_code==409


def test_context_scoping_manual_and_missing_records(client):
    answer=client.post('/generate',json={'itemId':'headphones','question':'多久清洁一次？'}).json()
    assert any(s['type']=='说明书' for s in answer['sources'])
    answer=client.post('/generate',json={'itemId':'suitcase','question':'之前维修过什么？'}).json()
    assert '没有找到' in answer['answer']
    assert '耳罩' not in answer['answer']
    assert client.post('/generate',json={'itemId':'missing','question':'保修吗？'}).status_code==404


def test_invalid_files_and_fields(client):
    assert client.post('/items',json=payload(name='')).status_code==422
    assert client.post('/items',json=payload(purchasePrice=-1)).status_code==422
    assert client.post('/items',json=payload(purchaseDate='2026-02-30')).status_code==422
    assert client.post('/items',json=payload(purchaseDate=(today()+timedelta(days=1)).isoformat())).status_code==422
    assert client.post('/recognize',files={'files':('bad.png',b'not an image','image/png')},data={'types':'product'}).status_code==415
    assert client.post('/items/headphones/documents',files={'file':('bad.pdf',b'not a pdf','application/pdf')}).status_code==415


def test_retired_lifecycle_and_scanned_pdf(client):
    from pypdf import PdfWriter
    from io import BytesIO
    item=client.post('/items',json=payload()).json()
    result=client.put('/items/'+item['id'],json=payload(status='回收'))
    assert result.status_code==200
    first=client.get('/items/'+item['id']).json()
    assert first['item']['status']=='回收'
    assert any(e['type']=='retired' for e in first['events'])
    assert not any(r['itemId']==item['id'] and r['status']=='pending' for r in client.get('/snapshot').json()['reminders'])
    writer=PdfWriter()
    writer.add_blank_page(width=400,height=400)
    stream=BytesIO()
    writer.write(stream)
    doc=client.post('/items/'+item['id']+'/documents',files={'file':('scanned.pdf',stream.getvalue(),'application/pdf')})
    assert doc.status_code==201
    assert doc.json()['extractedText']==''

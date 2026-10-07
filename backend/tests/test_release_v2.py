import json
import zipfile
from io import BytesIO
from hashlib import sha256
from datetime import date,timedelta
import pytest
from PIL import Image
from pypdf import PdfWriter,PdfReader
from backend import database,manual_ocr,ai_engine,backup_restore,recognition
from backend.storage import local_path

def image():
    b=BytesIO();Image.new('RGB',(100,100),'white').save(b,'PNG');return b.getvalue()

def pdf():
    w=PdfWriter();w.add_blank_page(300,300);b=BytesIO();w.write(b);return b.getvalue()

def create(client,name='V2 test'):
    return client.post('/items',json={'name':name,'purchaseDate':'2026-01-01','purchasePrice':100,'warrantyMonths':12}).json()['id']


def test_append_classify_cover_delete_and_pack(client):
    ident=create(client)
    files=[('files',('photo.png',image(),'image/png'))]
    first=client.post(f'/items/{ident}/images',files=files,data={'type':'product'}).json()[0]
    second=client.post(f'/items/{ident}/images',files=files,data={'type':'product'}).json()[0]
    receipt=client.post(f'/items/{ident}/images',files=files,data={'type':'receipt'}).json()[0]
    assert client.patch('/images/'+receipt['id'],json={'type':'invoice'}).json()['type']=='invoice'
    assert client.delete('/images/'+first['id']).status_code==200
    assert client.get('/items/'+ident).json()['item']['coverImage']==second['filePath']
    response=client.get(f'/items/{ident}/evidence-pack')
    assert response.status_code==200
    with zipfile.ZipFile(BytesIO(response.content)) as z:
        manifest=json.loads(z.read('manifest.json'))
        for f in manifest['files']:
            assert sha256(z.read(f['filename'])).hexdigest()==f['sha256']
            assert '..' not in f['filename'] and not f['filename'].startswith('/')
        assert len(PdfReader(BytesIO(z.read('summary.pdf'))).pages)>0
        assert any(f['type']=='invoice' for f in manifest['files'])
        assert b'D:\\' not in z.read('archive.json')
    stored=list((database.DATA/'images/items'/ident).glob('*'))
    assert len(stored)==2


def test_provenance_survives_manual_edit(client,monkeypatch):
    monkeypatch.setattr(recognition.provider,'read',lambda _: [('型号：WH-1000XM5',.95)])
    draft=client.post('/drafts').json()['id']
    client.post(f'/drafts/{draft}/images',files={'files':('label.png',image(),'image/png')},data={'type':'label'})
    result=client.post(f'/drafts/{draft}/recognize').json()
    ident=client.post('/items',json={'name':'OCR test','model':'WH-1000XM6','purchaseDate':'2026-01-01','draftSessionId':draft,'recognitionSessionId':result['sessionId']}).json()['id']
    candidates=client.get(f'/items/{ident}/provenance').json()
    model=next(c for c in candidates if c['field']=='model')
    assert model['manuallyEdited'] and model['recognizedValue']=='WH-1000XM5'
    assert model['currentValue']=='WH-1000XM6' and model['sourceType']=='label'
    assert client.get(model['sourceImage']).status_code==200


def test_scanned_ocr_success_and_failure_preserves_file(client,monkeypatch):
    ident=create(client)
    doc=client.post(f'/items/{ident}/documents/manual',files={'file':('scan.pdf',pdf(),'application/pdf')}).json()
    assert doc['textStatus']=='needs_ocr'
    monkeypatch.setattr(manual_ocr,'extract_scanned',lambda path:('[第 1 页]\nBattery care: avoid heat.',1))
    assert client.post(f'/documents/{doc["id"]}/ocr').status_code==202
    result=client.get(f'/items/{ident}/documents').json()[0]
    assert result['textStatus']=='ocr_ready' and result['textSource']=='local_ocr'
    answer=client.post('/generate',json={'itemId':ident,'question':'说明书电池保养'}).json()
    assert 'Battery care' in answer['answer']
    monkeypatch.setattr(manual_ocr,'extract_scanned',lambda _: (_ for _ in ()).throw(ValueError('test')))
    client.post(f'/documents/{doc["id"]}/ocr')
    assert client.get(f'/items/{ident}/documents').json()[0]['textStatus']=='ocr_failed'
    assert client.get(doc['filePath']).status_code==200


def test_actual_pdf_render_and_local_ocr(client):
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.utils import ImageReader
    from PIL import ImageDraw,ImageFont
    img=Image.new('RGB',(900,200),'white')
    font_path=database.ROOT/'frontend/public/assets/nonexistent-font'
    # Default Pillow font is redistributable; this fixture is generated in memory.
    ImageDraw.Draw(img).text((20,40),'Battery care: keep dry and avoid heat.',fill='black',font=ImageFont.load_default(size=32))
    b=BytesIO();c=Canvas(b,pagesize=(900,200));c.drawImage(ImageReader(img),0,0,900,200);c.save()
    path=database.DATA/'uploads/render-test.pdf';path.write_bytes(b.getvalue())
    text,count=manual_ocr.extract_scanned(path)
    assert count==1 and 'battery' in text.lower()


def test_maintenance_correct_delete_sync(client):
    ident=create(client)
    r=client.post(f'/items/{ident}/maintenance',json={'type':'clean','date':'2026-01-01','intervalDays':30,'cost':5}).json()
    edit=client.put('/maintenance/'+r['id'],json={'type':'clean','date':'2026-02-01','intervalDays':60,'cost':7}).json()
    assert edit['nextDueDate']=='2026-04-02'
    assert client.delete('/maintenance/'+r['id']).status_code==200
    detail=client.get('/items/'+ident).json()
    assert not detail['maintenance'] and not any(e.get('relatedId')==r['id'] for e in detail['events'])


def test_consumption_restock_undo_negative_guard(client):
    ident=create(client)
    c=client.post('/consumables',json={'itemId':ident,'name':'test stock','currentStock':3,'warningStock':1}).json()
    cid=c['id'];day=client.get('/health').json()['today']
    restock=client.post(f'/consumables/{cid}/restock',json={'date':day,'quantity':4,'cost':10}).json()
    record=restock['restocks'][-1]
    used=client.post(f'/consumables/{cid}/consume',json={'date':day,'quantity':5}).json()
    assert client.delete('/restock-records/'+record['id']).status_code==422
    undo=client.delete('/consumption-records/'+used['records'][-1]['id']).json()
    assert undo['currentStock']==7
    assert client.delete('/restock-records/'+record['id']).json()['currentStock']==3
    assert client.delete('/restock-records/'+record['id']).status_code==404


def test_repair_metadata_does_not_rewind_progress(client):
    ident=create(client)
    repair=client.post('/repairs',json={'itemId':ident,'issue':'test','reportDate':'2026-01-01'}).json()
    result=client.patch('/repairs/'+repair['id']+'/details',json={'cost':25,'description':'corrected','serviceType':'线下维修店'}).json()
    assert result['status']=='待预约' and result['cost']==25 and result['progress']==repair['progress']


def test_calendar_and_complete_backup_restore(client):
    ident=create(client)
    client.post(f'/items/{ident}/images',files={'files':('photo.png',image(),'image/png')})
    from sqlalchemy.orm import Session
    from backend import main
    with Session(main.engine) as session:
        backup_restore.backup_bytes(session)
    backup=client.get('/backup')
    assert backup.status_code==200, backup.text
    members=backup_restore.validate_backup(backup.content)
    assert any(n.startswith('images/items/'+ident) for n in members)
    extra=create(client,'after backup')
    result=client.post('/backup/restore',files={'file':('backup.zip',backup.content,'application/zip')},data={'confirmation':'恢复备份'})
    assert result.status_code==200
    assert client.get('/items/'+extra).status_code==404
    assert client.get('/items/'+ident).status_code==200
    assert list((database.DATA/'backups').glob('before-restore-*.zip'))
    calendar=client.get('/reminders/calendar.ics')
    assert 'BEGIN:VCALENDAR' in calendar.text and 'BEGIN:VEVENT' in calendar.text
    assert max(len(line) for line in calendar.content.split(b'\r\n'))<=75


@pytest.mark.parametrize('member',['../bad','/absolute','images/items/../bad','images\\bad'])
def test_malicious_backup_is_rejected(client,member):
    out=BytesIO()
    with zipfile.ZipFile(out,'w') as z:z.writestr(member,b'bad');z.writestr('manifest.json','{}')
    assert client.post('/backup/restore',files={'file':('bad.zip',out.getvalue(),'application/zip')},data={'confirmation':'恢复备份'}).status_code==422
    assert client.get('/items/headphones').status_code==200


def test_restore_failure_rolls_back(client,monkeypatch):
    backup=client.get('/backup').content
    ident=create(client,'must survive failure')
    original=backup_restore.restore_database;calls=[]
    def fail_once(engine,path):
        calls.append(path)
        if len(calls)==1:raise OSError('test disk failure')
        return original(engine,path)
    monkeypatch.setattr(backup_restore,'restore_database',fail_once)
    result=client.post('/backup/restore',files={'file':('backup.zip',backup,'application/zip')},data={'confirmation':'恢复备份'})
    assert result.status_code==422 and client.get('/items/'+ident).status_code==200


def test_ollama_unavailable_and_mock(client,monkeypatch):
    monkeypatch.setenv('WUSHENG_AI_PROVIDER','ollama');monkeypatch.setenv('WUSHENG_OLLAMA_MODEL','test-model')
    def unavailable(*args,**kwargs):raise OSError()
    monkeypatch.setattr(ai_engine.httpx,'get',unavailable)
    fallback=ai_engine.ProviderFactory();assert fallback.status()['activeProvider']=='evidence'
    class Reply:
        def __init__(self,body):self.body=body
        def raise_for_status(self):pass
        def json(self):return self.body
    monkeypatch.setattr(ai_engine.httpx,'get',lambda *a,**k:Reply({'models':[{'name':'test-model'}]}))
    sent=[]
    def generate(*a,**k):sent.append(k['json']);return Reply({'response':'依据当前档案，保修截止已记录。'})
    monkeypatch.setattr(ai_engine.httpx,'post',generate)
    factory=ai_engine.ProviderFactory();monkeypatch.setattr(ai_engine,'factory',factory)
    result=client.post('/generate',json={'itemId':'headphones','question':'保修到期了吗'}).json()
    assert result['activeProvider']=='ollama' and result['sources']
    assert 'MacBook' not in sent[0]['prompt']
    sent.clear()
    client.post('/generate',json={'itemId':'headphones','question':'未知行星的面积'})
    assert not sent
    client.post('/generate',json={'itemId':'headphones','question':'高压拆机维修'})
    assert not sent


def test_prediction_quality_real_history():
    from backend.consumptionPrediction import consumption_prediction
    day=date(2026,1,1)
    records=[{'date':(day+timedelta(days=i*10)).isoformat(),'quantityUsed':0 if i==0 else 1} for i in range(7)]
    p=consumption_prediction(2,records,day+timedelta(days=60))
    assert p['dataQuality']=='high' and p['recordCount']==6
    assert p['estimateRange']['minDays']<=p['estimatedDaysLeft']<=p['estimateRange']['maxDays']


def test_local_compatible_protocol_and_call_failure(client,monkeypatch):
    monkeypatch.setenv('WUSHENG_AI_PROVIDER','openai-compatible')
    monkeypatch.setenv('WUSHENG_AI_BASE_URL','http://127.0.0.1:1234/v1')
    monkeypatch.setenv('WUSHENG_AI_MODEL','synthetic-model')
    class Reply:
        def __init__(self,body):self.body=body
        def raise_for_status(self):pass
        def json(self):return self.body
    monkeypatch.setattr(ai_engine.httpx,'get',lambda *a,**k:Reply({'data':[{'id':'synthetic-model'}]}))
    sent=[]
    def post(*a,**k):
        sent.append(k['json'])
        return Reply({'choices':[{'message':{'content':'依据档案保修日期。'}}]})
    monkeypatch.setattr(ai_engine.httpx,'post',post)
    factory=ai_engine.ProviderFactory();monkeypatch.setattr(ai_engine,'factory',factory)
    answer=client.post('/generate',json={'itemId':'headphones','question':'保修日期'}).json()
    assert answer['activeProvider']=='openai-compatible' and answer['sources']
    assert sent[0]['messages'][0]['role']=='system'
    def fail(*a,**k):raise OSError('synthetic model disconnected')
    monkeypatch.setattr(ai_engine.httpx,'post',fail)
    answer=client.post('/generate',json={'itemId':'headphones','question':'保修日期'}).json()
    assert answer['activeProvider']=='evidence' and answer['fallbackReason']


def test_backup_hash_and_schema_rejected_without_changes(client):
    original=client.get('/backup').content
    for failure in ('hash','schema'):
        out=BytesIO()
        with zipfile.ZipFile(BytesIO(original)) as old, zipfile.ZipFile(out,'w') as new:
            manifest=json.loads(old.read('manifest.json'))
            if failure=='schema':manifest['schemaVersion']=999
            else:manifest['files'][0]['sha256']='0'*64
            for name in old.namelist():
                new.writestr(name,json.dumps(manifest) if name=='manifest.json' else old.read(name))
        result=client.post('/backup/restore',files={'file':('bad.zip',out.getvalue(),'application/zip')},data={'confirmation':'恢复备份'})
        assert result.status_code==422
        assert client.get('/items/headphones').status_code==200

"""Final three-Demo upgrade, evidence dispatch and physical LAN filtering."""
from pathlib import Path
from io import BytesIO
import hashlib
import pytest
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from pypdf import PdfWriter
from backend import database,main,models as m,ai_engine,sharing
from backend.demo_assets import CATALOG,MATERIALS
from backend.context import ContextBuilder
from backend.providers import EvidenceProvider
from scripts.migrate_final_materials import migrate,VERSION

@pytest.fixture
def legacy(tmp_path):
    engine=database.make_engine(f'sqlite:///{tmp_path / "legacy.db"}')
    database.Base.metadata.create_all(engine)
    with Session(engine) as db:
        for ident in ('ac','toothbrush','suitcase'):
            previous=CATALOG[ident]['previousV3']
            db.add(m.Item(id=ident,**previous,isDemo=True,serialNumber=f'WS-DEMO-{ident.upper()}',purchaseDate='2024-01-02',purchasePrice=12345,warrantyMonths=37,createdAt='2024-01-02T00:00:00+00:00',updatedAt='2024-01-02T00:00:00+00:00'))
            db.flush()
            for kind in ('manual_image','invoice','warranty_card','package' if ident=='toothbrush' else 'label'):
                path=f'/assets/demo-evidence/{ident}-{kind}.png'
                db.add(m.ItemImage(id=f'demo-v3-{ident}-{kind}',itemId=ident,type=kind,source='synthetic-demo-v3',filePath=path,sha256='old',assetMetadata={'path':path,'sha256':'old'}))
        db.add(m.Document(id='keep',itemId='ac',filename='my.pdf',filePath='documents/manuals/ac/my.pdf',sha256='keep',extractedText='private content'))
        db.commit();yield db
    engine.dispose()

def test_final_upgrade_is_atomic_idempotent_and_preserves_business(legacy):
    report=migrate(legacy);assert report['items']==['ac','toothbrush','suitcase']
    assert legacy.get(m.Item,'ac').model=='WSKFR-26GW/BP3'
    assert migrate(legacy,True)['replacedImages']==12;legacy.commit()
    for ident in report['items']:
        item=legacy.get(m.Item,ident)
        assert all(getattr(item,k)==v for k,v in CATALOG[ident]['new'].items())
        assert (item.purchaseDate,item.purchasePrice,item.warrantyMonths)==('2024-01-02',12345,37)
        assert VERSION in item.description
        actual=list(legacy.scalars(select(m.ItemImage).where(m.ItemImage.itemId==ident)))
        assert {a.sha256 for a in actual}=={a['sha256'] for a in MATERIALS if a['itemId']==ident}
    assert legacy.get(m.Document,'keep').extractedText=='private content'
    assert migrate(legacy,True)['items']==[]
    assert legacy.scalar(select(func.count()).select_from(m.ItemImage))==12
    assert legacy.get(m.Consumable,'ac-filter').itemId=='ac'
    assert not legacy.scalar(select(m.ConsumptionRecord))

@pytest.mark.parametrize('change',['user','name','date','cover-record','deleted-paper'])
def test_final_upgrade_preserves_user_and_ambiguous_changes(legacy,change):
    item=legacy.get(m.Item,'ac')
    if change=='user':item.isDemo=False
    elif change=='name':item.name='my custom AC'
    elif change=='date':item.updatedAt='2024-02-02T00:00:00+00:00'
    elif change=='cover-record':legacy.get(m.ItemImage,'demo-v3-ac-label').filePath='/uploads/my-label.png'
    else:legacy.delete(legacy.get(m.ItemImage,'demo-v3-ac-label'))
    legacy.commit();before=item.model
    report=migrate(legacy,True);legacy.commit()
    assert item.model==before and 'ac' not in report['items']

def test_final_upgrade_rollback(legacy):
    def fail():raise OSError('simulated disk failure')
    with pytest.raises(OSError):migrate(legacy,True,fail)
    legacy.rollback()
    assert legacy.get(m.Item,'ac').model=='WSKFR-26GW/BP3'
    assert not legacy.get(m.Consumable,'ac-filter')

def test_owner_confirmed_import_technical_validation_and_idempotence(client,tmp_path,monkeypatch):
    from scripts import import_demo_manuals as importer
    monkeypatch.setattr(database,'engine',main.engine)
    originals={}
    for _,name,*_ in importer.OWNER_CONFIRMED:
        out=BytesIO();pdf=PdfWriter();pdf.add_blank_page(width=200,height=200);pdf.write(out)
        originals[name]=out.getvalue();(tmp_path/name).write_bytes(out.getvalue())
    assert len(importer.run(tmp_path,True,True))==3
    importer.run(tmp_path,True,True)
    with Session(main.engine) as db:
        docs=list(db.scalars(select(m.Document).where(m.Document.itemId.in_(['ac','toothbrush','suitcase']))))
        assert len(docs)==3
        for doc in docs:
            assert doc.assetMetadata['bindingSource']=='owner-confirmed' and not doc.assetMetadata['excludedFromAI']
            body=client.get('/api/documents/'+doc.id+'/file').content
            assert body==originals[doc.filename] and hashlib.sha256(body).hexdigest()==doc.sha256

def test_scoped_pdf_maintenance_replacement_lock_and_dates(client):
    with Session(main.engine) as db:
        db.add(m.Document(itemId='ac',filename='AC care.pdf',filePath='unused',extractedText='[第 14 页]\n滤尘网的清洁\n清洁前请断开电源。\n将滤尘网清洗干净，阴凉晾干。'))
        db.add(m.Document(itemId='toothbrush',filename='Brush care.pdf',filePath='unused',extractedText='[第 8 页]\nCleaning and maintenance\nRinse the brush head after use.\nReplacement\nReplace brush heads every 3 months.'))
        db.add(m.Document(itemId='suitcase',filename='Lock guide.pdf',filePath='unused',extractedText='[第 1 页]\nCombination locks\nPush the button and hold to set your own combination.\nRelease the button.'))
        db.commit()
    cases=[('ac','我的空调滤尘网应该怎样清洁？','清洗干净','AC care.pdf'),('toothbrush','电动牙刷如何维护？刷头什么时候需要更换？','3 months','Brush care.pdf'),('suitcase','这件行李箱的密码锁如何设置？','combination','Lock guide.pdf')]
    for ident,q,text,title in cases:
        answer=client.post('/generate',json={'itemId':ident,'question':q}).json()
        assert text in answer['answer'] and any(title in s['title'] for s in answer['sources'])
        assert not answer['modelInvoked'] and answer['activeProvider']=='evidence'
        assert all(other not in str(answer['sources']) for other in ['AC care.pdf','Brush care.pdf','Lock guide.pdf'] if other!=title)
    detail=client.get('/items/ac').json()
    answer=client.post('/generate',json={'itemId':'ac','question':'什么时候需要进行下一次维护？'}).json()
    assert detail['item']['nextMaintenance'] in answer['answer'] and answer['sources'][0]['type']=='维护规则'
    inventory=client.post('/generate',json={'itemId':'ac','question':'当前物品有哪些说明书资料？'}).json()
    assert 'AC care.pdf' in inventory['answer'] and 'Lock guide.pdf' not in inventory['answer']
    unknown=client.post('/generate',json={'itemId':'ac','question':'说明书电池循环次数上限是多少？'}).json()
    assert unknown['sources']==[] and not unknown['modelInvoked']

def test_physical_lan_filter_excludes_vpn_vm_and_disconnected():
    records=[{'physical':True,'gateway':['192.168.1.1'],'name':'WLAN','addresses':['fe80::1','192.168.1.4','169.254.1.5'],'metric':25},
             {'physical':False,'gateway':['10.0.0.1'],'name':'Meta Tunnel','addresses':['10.0.0.2'],'metric':1},
             {'physical':True,'gateway':['192.168.3.1'],'name':'VMware Virtual Ethernet','addresses':['192.168.3.2']},
             {'physical':True,'gateway':[],'name':'Ethernet','addresses':['192.168.2.3']},
             {'physical':True,'gateway':['10.0.2.1'],'name':'Ethernet','addresses':['10.0.2.2'],'metric':10}]
    assert [i['address'] for i in sharing.physical_interfaces(records)]==['10.0.2.2','192.168.1.4']

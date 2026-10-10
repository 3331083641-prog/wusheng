"""Migration safety and cross-surface provenance, independent of the live database."""
import json
from pathlib import Path
import pytest
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from backend import models as m
from backend.database import Base,make_engine
from backend.demo_assets import CATALOG,OLD_DESCRIPTION,MATERIALS
from scripts.migrate_demo_assets import migrate

@pytest.fixture
def db(tmp_path):
    engine=make_engine(f'sqlite:///{tmp_path / "migration.db"}');Base.metadata.create_all(engine)
    with Session(engine) as session:
        for ident,entry in CATALOG.items():
            session.add(m.Item(id=ident,**entry['old'],isDemo=True,description=OLD_DESCRIPTION,
                serialNumber=f'WS-DEMO-{ident.upper()}',purchaseDate='2024-02-29',purchasePrice=98765,warrantyMonths=37,
                warrantyEndDate='2027-03-29',createdAt='2024-01-01T00:00:00+00:00',updatedAt='2024-01-01T00:00:00+00:00'))
        session.commit();yield session
    engine.dispose()

def test_dry_run_changes_nothing(db):
    report=migrate(db)
    assert len(report['items'])==10
    assert db.get(m.Item,'ac').brand=='Midea'
    assert db.scalar(select(func.count()).select_from(m.ItemImage))==0

def test_atomic_idempotent_upgrade_preserves_business_and_files(db):
    db.add(m.MaintenanceRecord(itemId='coffee',type='人工维护',date='2025-01-02',nextDueDate='2025-02-02',description='用户记录'))
    db.add(m.Document(itemId='coffee',filename='旧说明书.pdf',filePath='documents/manuals/coffee/keep.pdf',sha256='keep'))
    db.commit()
    report=migrate(db,True);db.commit()
    assert report['addedImages']==40
    for ident,entry in CATALOG.items():
        item=db.get(m.Item,ident)
        assert all(getattr(item,k)==v for k,v in entry['new'].items())
        assert (item.purchaseDate,item.purchasePrice,item.warrantyMonths,item.warrantyEndDate)==('2024-02-29',98765,37,'2027-03-29')
    assert db.scalar(select(m.MaintenanceRecord)).description=='用户记录'
    doc=db.scalar(select(m.Document));assert doc.filePath.endswith('keep.pdf') and doc.sha256=='keep'
    assert doc.assetMetadata['excludedFromAI'] and doc.type=='reference_pending'
    assert migrate(db,True)['addedImages']==0
    assert db.scalar(select(func.count()).select_from(m.ItemImage))==40

@pytest.mark.parametrize('field,value',[('isDemo',False),('model','我的型号'),('name','我的物品'),('description','用户备注'),('updatedAt','2025-01-01T00:00:00+00:00'),('serialNumber','真实序列号')])
def test_user_or_ambiguous_archives_are_never_overwritten(db,field,value):
    item=db.get(m.Item,'ac');setattr(item,field,value);db.commit()
    migrate(db,True);db.commit()
    assert getattr(db.get(m.Item,'ac'),field)==value
    assert not db.scalar(select(m.ItemImage).where(m.ItemImage.itemId=='ac'))

def test_failure_rolls_back_all_changes(db):
    def fail():raise RuntimeError('injected failure')
    with pytest.raises(RuntimeError):migrate(db,True,fail)
    db.rollback()
    assert db.get(m.Item,'laptop').model==CATALOG['laptop']['old']['model']
    assert db.scalar(select(func.count()).select_from(m.ItemImage))==0

def test_material_inventory_truth_and_bounds():
    import hashlib
    from PIL import Image
    root=Path(__file__).resolve().parents[2]
    assert len(MATERIALS)==40 and len({a['itemId'] for a in MATERIALS})==10
    for asset in MATERIALS:
        path=root/'frontend/public'/asset['path'].lstrip('/')
        assert hashlib.sha256(path.read_bytes()).hexdigest()==asset['sha256']
        assert Image.open(path).size==(asset['width'],asset['height'])
        assert asset['isSynthetic'] and asset['type']!='product'
    assert not next(a for a in MATERIALS if a['itemId']=='robot' and a['type']=='label')['modelVerified']

def test_current_seed_and_shared_provenance(client):
    for ident,entry in CATALOG.items():
        detail=client.get('/items/'+ident).json()
        assert all(detail['item'][k]==v for k,v in entry['new'].items())
        assert len([a for a in detail['images'] if a['source']=='synthetic-demo-v3'])==4
        assert detail['item']['identityNote']
    reply=client.post('/generate',json={'itemId':'ac','question':'这个品牌有官方保修吗？'}).json()
    assert '合成演示' in reply['answer'] and '不证明真实购买或保修资格' in reply['answer']
    assert '美的空调' in reply['answer'] and '武圣' not in reply['answer']
    cs=client.get('/items/coffee').json()['consumables']
    assert cs[0]['name']=='E.S.E. 咖啡易理包' and '胶囊' in cs[0]['compatibilityNote']

@pytest.mark.parametrize('password,accepted',[('',True),('private-password',False)])
def test_readable_restricted_pdf_preserves_original_bytes(password,accepted):
    from io import BytesIO
    from pypdf import PdfWriter
    from fastapi import UploadFile,HTTPException
    from starlette.datastructures import Headers
    from backend.storage import validate_pdf
    output=BytesIO();writer=PdfWriter();writer.add_blank_page(width=100,height=100)
    writer.encrypt(user_password=password,owner_password='owner-secret');writer.write(output)
    original=output.getvalue()
    upload=UploadFile(BytesIO(original),filename='manual.pdf',headers=Headers({'content-type':'application/pdf'}))
    if accepted:
        contents,metadata=validate_pdf(upload)
        assert contents==original and metadata['pageCount']==1
    else:
        with pytest.raises(HTTPException):validate_pdf(upload)

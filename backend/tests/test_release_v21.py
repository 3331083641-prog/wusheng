import json
import sqlite3
import zipfile
from io import BytesIO
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import pytest
from sqlalchemy.orm import Session
from backend import sharing, main, models as m, database


@pytest.fixture
def lan(client, monkeypatch):
    monkeypatch.setenv('WUSHENG_SHARE_MODE', 'lan')
    monkeypatch.setattr(sharing, 'lan_addresses', lambda: ['10.2.3.4'])
    return client


@pytest.mark.parametrize('lifetime,days',[('24h',1),('7d',7),('30d',30),('forever',None)])
def test_share_lifetime(lan,lifetime,days):
    before=datetime.now(timezone.utc)
    link=lan.post('/items/headphones/share',json={'lifetime':lifetime}).json()
    if days:
        expiry=datetime.fromisoformat(link['expiresAt'])
        assert timedelta(days=days)<=expiry-before<timedelta(days=days,seconds=5)
    else: assert link['expiresAt'] is None
    repeated=lan.post('/items/headphones/share').json()
    assert repeated['token']==link['token'] and repeated['expiresAt']==link['expiresAt']
    assert lan.post('/items/headphones/share',json={'lifetime':'30d'}).status_code==409


def test_expired_unknown_revoked_indistinguishable(lan):
    link=lan.post('/items/headphones/share').json()
    with Session(main.engine) as db:
        row=db.get(m.ShareLink,link['id']);row.expiresAt=(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat();db.commit()
    expired=lan.get('/share-data/'+link['token'])
    assert expired.status_code==404
    assert lan.get('/share-data/not-a-real-token').json()==expired.json()
    fresh=lan.post('/items/headphones/share').json()
    assert fresh['token']!=link['token']
    lan.delete('/items/headphones/share')
    assert lan.get('/share-data/'+fresh['token']).json()==expired.json()


def test_privacy_flags_and_event_title_redaction(lan):
    with Session(main.engine) as db:
        db.add(m.LifecycleEvent(itemId='headphones',type='repair',date='2026-01-01',title='PRIVATE repair invoice price serial',relatedId='privacy-test'));db.commit()
    link=lan.post('/items/headphones/share').json()
    shared=lan.get('/share-data/'+link['token']).json()
    assert not {'purchaseDate','purchasePrice','purchaseChannel','serialNumber'} & shared['item'].keys()
    assert shared['manuals']==[] and 'PRIVATE' not in json.dumps(shared)
    assert not any(e['type']=='purchase' for e in shared['events'])
    opts={k:False for k in sharing.ShareOptions.model_fields}
    private=lan.post('/items/headphones/share?regenerate=true',json={'options':opts}).json()
    data=lan.get('/share-data/'+private['token']).json()
    assert data['events']==data['consumables']==data['manuals']==[]
    assert 'warrantyEndDate' not in data['item']
    public=lan.post('/items/headphones/share?regenerate=true',json={'options':{'showPurchaseDate':True,'showManualNames':True}}).json()
    assert lan.get('/share-data/'+public['token']).json()['item']['purchaseDate']
    assert lan.post('/items/headphones/share?regenerate=true',json={'options':{'showSerialNumber':True}}).status_code==422
    assert lan.post('/items/headphones/share?regenerate=true',json={'lifetime':'bad'}).status_code==422


def test_old_schema_additive_migration_and_backup_restore(lan,tmp_path):
    old=tmp_path/'old.db'
    with sqlite3.connect(old) as conn:
        conn.execute('CREATE TABLE share_links (id TEXT PRIMARY KEY, itemId TEXT, token TEXT, createdAt TEXT, updatedAt TEXT, revoked BOOLEAN, lastUsedAt TEXT)')
        conn.execute("INSERT INTO share_links VALUES ('legacy','headphones','legacy-fixture-token','','',0,NULL)")
    eng=database.make_engine('sqlite:///'+old.as_posix())
    m.Base.metadata.create_all(eng);database.migrate_schema(eng)
    with Session(eng) as db:
        row=db.get(m.ShareLink,'legacy')
        assert row.token=='legacy-fixture-token' and row.expiresAt is None and not sharing.expired(row)
    eng.dispose()
    original=lan.get('/backup').content
    # Construct a genuine older-schema synthetic ZIP and update its manifest hash.
    with zipfile.ZipFile(BytesIO(original)) as archive:
        members={name:archive.read(name) for name in archive.namelist()}
    old.write_bytes(members['wusheng.db'])
    with sqlite3.connect(old) as conn:
        conn.execute('ALTER TABLE share_links DROP COLUMN expiresAt');conn.execute('ALTER TABLE share_links DROP COLUMN options')
    members['wusheng.db']=old.read_bytes()
    manifest=json.loads(members['manifest.json']);manifest['schemaVersion']=2
    for entry in manifest['files']:
        body=members[entry['filename']];entry.update(size=len(body),sha256=sha256(body).hexdigest())
    members['manifest.json']=json.dumps(manifest).encode()
    buffer=BytesIO()
    with zipfile.ZipFile(buffer,'w') as archive:
        for name,body in members.items(): archive.writestr(name,body)
    assert lan.post('/backup/restore',files={'file':('old.zip',buffer.getvalue(),'application/zip')},data={'confirmation':'恢复备份'}).status_code==200
    assert lan.post('/items/headphones/share').status_code==200



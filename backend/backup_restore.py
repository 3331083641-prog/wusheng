"""Validated ZIP restore with a pre-restore snapshot and rollback on any failure."""
import json
import os
import shutil
import sqlite3
import tempfile
import zipfile
import threading
from contextlib import closing
from pathlib import Path,PurePosixPath
from io import BytesIO
from hashlib import sha256
from fastapi import APIRouter,Depends,HTTPException,UploadFile,File,Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import select
from . import database,models as m
from .database import get_db,timestamp
from .storage import local_path

router=APIRouter();SCHEMA_VERSION=2;MAX_BYTES=300*1024*1024
_lock=threading.Lock()


def db_snapshot(engine,path):
    source=engine.raw_connection()
    try:
        with closing(sqlite3.connect(path)) as target:source.driver_connection.backup(target)
    finally:source.close()


def backup_bytes(db):
    if db.scalar(select(m.Document.id).where(m.Document.textStatus=='ocr_processing')):
        raise HTTPException(409,'请等待说明书 OCR 完成后备份或恢复')
    db.commit();engine=db.get_bind()
    members={}
    for model in (m.ItemImage,m.Document):
        for record in db.scalars(select(model)):
            if record.filePath.startswith('/assets/'):continue
            path=local_path(record.filePath)
            if not path.is_file():raise HTTPException(409,'档案中的附件缺失，无法生成完整备份')
            name=path.relative_to(database.DATA).as_posix()
            members[name]=path.read_bytes()
    if sum(map(len,members.values()))>MAX_BYTES:raise HTTPException(413,'备份超过 300MB 上限')
    with tempfile.TemporaryDirectory(prefix='backup-',dir=database.DATA/'uploads') as temp:
        sqlite_path=Path(temp)/'wusheng.db';db_snapshot(engine,sqlite_path);members['wusheng.db']=sqlite_path.read_bytes()
    manifest={'version':1,'schemaVersion':SCHEMA_VERSION,'createdAt':timestamp(),'files':[{'filename':n,'size':len(b),'sha256':sha256(b).hexdigest()} for n,b in members.items()]}
    output=BytesIO()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for name,contents in members.items():z.writestr(name,contents)
        z.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False))
    return output.getvalue()


def validate_backup(contents):
    try:
        with zipfile.ZipFile(BytesIO(contents)) as z:
            infos=z.infolist();names=[info.filename for info in infos]
            if len(names)!=len(set(names)) or len(names)>2000 or sum(i.file_size for i in infos)>MAX_BYTES:raise ValueError('size or duplicate')
            for info in infos:
                path=PurePosixPath(info.filename)
                if path.is_absolute() or '..' in path.parts or '\\' in info.filename or ':' in info.filename or info.is_dir() or (info.external_attr >> 16)&0o170000==0o120000:raise ValueError('unsafe member')
                if info.filename not in ('manifest.json','wusheng.db') and not info.filename.startswith(('images/items/','documents/manuals/','uploads/')):raise ValueError('unsupported member')
            manifest=json.loads(z.read('manifest.json'))
            if manifest.get('version')!=1 or manifest.get('schemaVersion')!=SCHEMA_VERSION:raise ValueError('schema version')
            declared={f['filename']:f for f in manifest['files']}
            if set(declared)!=set(names)-{'manifest.json'} or len(declared)!=len(manifest['files']):raise ValueError('manifest mismatch')
            members={}
            for name,info in declared.items():
                body=z.read(name)
                if len(body)!=info['size'] or sha256(body).hexdigest()!=info['sha256']:raise ValueError('hash mismatch')
                members[name]=body
            if 'wusheng.db' not in members:raise ValueError('database missing')
            return members
    except Exception:
        raise HTTPException(422,'备份无效：文件路径、大小、Schema 或 SHA256 校验未通过')


def validate_sqlite(path,members):
    with closing(sqlite3.connect(path)) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or db.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('database integrity')
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not set(m.Base.metadata.tables).issubset(tables):raise ValueError('schema tables')
        if db.execute("SELECT name FROM sqlite_master WHERE type IN ('trigger','view')").fetchall():raise ValueError('unsupported database programs')
        for name,table in m.Base.metadata.tables.items():
            columns={r[1] for r in db.execute(f'PRAGMA table_info("{name}")')}
            if not {column.name for column in table.columns}.issubset(columns):raise ValueError('schema columns')
        for table in ('item_images','documents'):
            for (relative,) in db.execute(f'SELECT filePath FROM {table}'):
                if relative.startswith('/assets/'):continue
                safe='uploads/'+relative.removeprefix('/uploads/') if relative.startswith('/uploads/') else relative
                if safe not in members:raise ValueError('attachment missing')


def restore_database(engine,source_path):
    raw=engine.raw_connection()
    try:
        with closing(sqlite3.connect(source_path)) as source:source.backup(raw.driver_connection)
    finally:raw.close()
    engine.dispose()


def restore_members(engine,members):
    # Existing runtime files are preserved; replaced files are copied for rollback.
    with tempfile.TemporaryDirectory(prefix='restore-',dir=database.DATA/'uploads') as temporary:
        stage=Path(temporary);candidate=stage/'candidate.db';candidate.write_bytes(members['wusheng.db'])
        validate_sqlite(candidate,members)
        before=stage/'before.db';db_snapshot(engine,before)
        changes=[]
        try:
            for name,contents in members.items():
                if name=='wusheng.db':continue
                target=local_path(name);target.parent.mkdir(parents=True,exist_ok=True)
                prior=target.read_bytes() if target.is_file() else None
                changes.append((target,prior));target.write_bytes(contents)
            restore_database(engine,candidate)
        except Exception:
            restore_database(engine,before)
            for target,prior in reversed(changes):
                if prior is None:target.unlink(missing_ok=True)
                else:target.write_bytes(prior)
            raise


@router.get('/backup')
def download_backup(db:Session=Depends(get_db)):
    with _lock:contents=backup_bytes(db)
    name='wusheng-backup-'+timestamp()[:19].replace(':','').replace('-','')+'.zip'
    return Response(contents,media_type='application/zip',headers={'Content-Disposition':f'attachment; filename="{name}"'})


@router.post('/backup/restore')
def upload_restore(file:UploadFile=File(...),confirmation:str=Form(...),db:Session=Depends(get_db)):
    if confirmation!='恢复备份':raise HTTPException(422,'请明确确认恢复备份')
    contents=file.file.read(MAX_BYTES+1)
    if len(contents)>MAX_BYTES:raise HTTPException(413,'备份 ZIP 不超过 300MB')
    members=validate_backup(contents)
    with _lock:
        previous=backup_bytes(db)
        recovery=database.DATA/'backups';recovery.mkdir(exist_ok=True)
        from .database import uid
        (recovery/('before-restore-'+uid()+'.zip')).write_bytes(previous)
        engine=db.get_bind();db.close()
        try:restore_members(engine,members)
        except Exception:raise HTTPException(422,'恢复失败；原数据库与附件已保留或回滚')
    return {'restored':True,'preRestoreBackup':True}

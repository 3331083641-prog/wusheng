"""Import only reviewed local manufacturer PDFs, never copy them into public assets.

Use --dry-run first; --apply uses the normal PDF validator and file transaction.
Existing matching hashes are preserved. No new QR permissions are granted.
"""
import argparse
from hashlib import sha256
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi import UploadFile
from starlette.datastructures import Headers
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend import models as m,database
from backend.demo_assets import matches
from backend.storage import validate_pdf,file_transaction

MANUALS=[
 ('laptop','Apple MacBook Air M2说明书.pdf',['A2681'],'中文','安全与监管资料（不是完整操作手册）','https://support.apple.com/en-gb/docs/mac/300872'),
 ('headphones','耳机说明书.pdf',['WH-1000XM6'],'法文','WH-1000XM6 帮助指南','https://helpguide.sony.net/mdr/2984/v1/fr/index.html'),
 ('robot','小米扫地机器人说明书.pdf',['B106GL','S10'],'多语言','S10 / B106GL 使用说明书','https://www.mi.com/global/product/xiaomi-robot-vacuum-s10/'),
 ('purifier','小米空气净化器说明书.pdf',['AC-M16-SC'],'英文／繁体中文等','Smart Air Purifier 4 使用说明书','https://www.mi.com/global/product/xiaomi-smart-air-purifier-4/'),
 ('printer','打印机说明书.pdf',['HP DeskJet 2700'],'英文','DeskJet 2700 系列使用指南；地区墨盒另行核实','https://support.hp.com/us-en/product/setup-user-guides/hp-deskjet-2700e-all-in-one-series/29378157')]

def run(source,apply=False):
    report=[]
    with Session(database.engine) as db:
        # All files validate before any database/file changes.
        candidates=[]
        for ident,name,terms,language,scope,url in MANUALS:
            item=db.get(m.Item,ident)
            if not item or not matches(item):
                report.append({'itemId':ident,'status':'跳过：当前档案身份不匹配'});continue
            with (source/name).open('rb') as stream:
                body,metadata=validate_pdf(UploadFile(stream,filename=name,headers=Headers({'content-type':'application/pdf'})))
            if not all(t.lower() in metadata['extractedText'].lower() for t in terms):
                raise ValueError(f'PDF content model mismatch: {name}')
            if db.scalar(select(m.Document.id).where(m.Document.itemId==ident,m.Document.sha256==sha256(body).hexdigest())):
                report.append({'itemId':ident,'status':'已存在相同 SHA256，保留'});continue
            candidates.append((ident,name,body,metadata,{'language':language,'scope':scope,'sourceUrl':url,'modelReview':'文件内容型号已核对；未执行电子签名或厂商原件鉴证','excludedFromAI':False}))
            report.append({'itemId':ident,'filename':name,'pages':metadata['pageCount'],'scope':scope,'status':'导入' if apply else '计划导入'})
        if apply:
            with file_transaction(db) as files:
                for ident,name,body,metadata,provenance in candidates:
                    relative=f'documents/manuals/{ident}/{metadata["storedFilename"]}'
                    files.write(relative,body)
                    db.add(m.Document(itemId=ident,filename=name,filePath=relative,assetMetadata=provenance,**metadata))
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-dir',type=Path,required=True)
    g=p.add_mutually_exclusive_group();g.add_argument('--dry-run',action='store_true');g.add_argument('--apply',action='store_true')
    a=p.parse_args();print(json.dumps(run(a.source_dir,a.apply),ensure_ascii=False,indent=2))

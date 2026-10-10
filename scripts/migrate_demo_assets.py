"""Opt-in conservative Demo upgrade, backed up and atomic. Default: dry run.

Only original seed fields with unchanged edit timestamps and an intact seed
fingerprint qualify. Any edited/ambiguous archive is reported and left intact.
Dates, money, warranty, status, user covers and historical records are untouched.
"""
import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend import database, models as m
from backend.demo_assets import CATALOG,CONSUMABLES,OLD_DESCRIPTION,add_materials,matches
from backend.backup_restore import db_snapshot

def plan(db):
    updates=[]; pending=[]
    for ident,entry in CATALOG.items():
        item=db.get(m.Item,ident)
        if not item or not item.isDemo:continue
        if any(v in (item.description or '') for v in ('素材版本：demo-assets-v3','素材版本：final-materials-v4')):continue
        try:
            # SQLAlchemy evaluates initial timestamp defaults a few microseconds
            # apart; do not accept a later API edit merely within the same second.
            untouched=abs((datetime.fromisoformat(item.updatedAt)-datetime.fromisoformat(item.createdAt)).total_seconds())<0.001
        except (ValueError,TypeError):untouched=False
        fingerprint=item.serialNumber==f'WS-DEMO-{ident.upper()}' and item.description==OLD_DESCRIPTION
        unchanged=all(getattr(item,k)==v for k,v in entry['old'].items())
        if not (untouched and fingerprint and unchanged):
            pending.append({'itemId':ident,'reason':'可能已人工修改／无法可靠确认原始种子，保留整条档案'})
            continue
        updates.append(ident)
    return updates,pending

def migrate(db,apply=False,fail_hook=None):
    eligible,pending=plan(db);report={'apply':apply,'items':eligible,'pending':pending,'addedImages':0,'consumables':[]}
    if not apply:return report
    for ident in eligible:
        item=db.get(m.Item,ident);entry=CATALOG[ident]
        for field,value in entry['new'].items():setattr(item,field,value)
        version='final-materials-v4' if ident in ('ac','toothbrush','suitcase') else 'demo-assets-v3'
        item.description=OLD_DESCRIPTION+'\n'+entry['identityNote']+'\n素材版本：'+version
        report['addedImages']+=add_materials(db,item)
        for cid,(parent,old,new,_) in CONSUMABLES.items():
            c=db.get(m.Consumable,cid)
            if parent==ident and c and c.itemId==ident and c.name==old:
                c.name=new
                if cid=='capsules' and c.unit=='颗':c.unit='包'
                report['consumables'].append(cid)
        # Keep any old user manual; do not silently attach it to a changed identity.
        if entry['old']['model']!=entry['new']['model']:
            for doc in db.scalars(select(m.Document).where(m.Document.itemId==ident)):
                meta=doc.assetMetadata or {}
                doc.assetMetadata={**meta,'modelReview':'型号已变更，适配待复核；保留原文件，不作 AI 说明书依据','excludedFromAI':True}
                doc.type='reference_pending'
        if fail_hook:fail_hook()
    db.flush()
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group();group.add_argument('--dry-run',action='store_true');group.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    if args.apply:
        directory=database.ROOT/'backups/assets-v3';directory.mkdir(parents=True,exist_ok=True)
        path=directory/('migration-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.db')
        db_snapshot(database.engine,path)
        database.migrate_schema(database.engine)
    with Session(database.engine) as db:
        try:
            report=migrate(db,args.apply)
            if args.apply:db.commit()
        except Exception:
            db.rollback();raise
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

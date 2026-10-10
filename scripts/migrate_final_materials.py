"""Owner-confirmed three-Demo upgrade. Dry run by default; transactional and repeatable.

Only exact, unedited known seed fingerprints qualify. Preserve all business fields,
user attachments and PDFs. Replace only managed synthetic papers with intact hashes.
Use the one pre-upgrade SQLite backup under backups/final-integration-20261009.
"""
import argparse
from datetime import datetime
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select,inspect
from sqlalchemy.orm import Session
from backend import database,models as m
from backend.demo_assets import CATALOG,MATERIALS,OLD_DESCRIPTION,add_materials
from backend.backup_restore import db_snapshot

IDS=('ac','toothbrush','suitcase')
VERSION='素材版本：final-materials-v4'

def migrate(db,apply=False,fail_hook=None):
    report={'apply':apply,'items':[],'pending':[],'replacedImages':0,'addedImages':0,'addedConsumables':0}
    for ident in IDS:
        item=db.get(m.Item,ident);entry=CATALOG[ident]
        if not item or not item.isDemo:continue
        if VERSION in (item.description or ''):continue
        try: untouched=abs((datetime.fromisoformat(item.updatedAt)-datetime.fromisoformat(item.createdAt)).total_seconds())<.001
        except (ValueError,TypeError):untouched=False
        previous=entry.get('previousV3',{})
        known_v3=all(getattr(item,k)==v for k,v in previous.items())
        known_v1=item.description==OLD_DESCRIPTION and all(getattr(item,k)==v for k,v in entry['old'].items())
        if not (untouched and item.serialNumber==f'WS-DEMO-{ident.upper()}' and (known_v3 or known_v1)):
            report['pending'].append({'itemId':ident,'reason':'用户编辑或不明确的种子版本；保持原档案'});continue
        managed=list(db.scalars(select(m.ItemImage).where(m.ItemImage.itemId==ident,m.ItemImage.source=='synthetic-demo-v3')))
        # A replaced/retyped/deleted managed paper signals a user edit: never overwrite it.
        safe=not managed if known_v1 else len(managed)==4 and all(
            a.id==f'demo-v3-{ident}-{a.type}' and a.assetMetadata and a.sha256==a.assetMetadata.get('sha256')
            and a.filePath==a.assetMetadata.get('path') for a in managed)
        if not safe:
            report['pending'].append({'itemId':ident,'reason':'配套资料已编辑或不完整，保持原档案'});continue
        report['items'].append(ident)
        if not apply:continue
        for key,value in entry['new'].items():setattr(item,key,value)
        item.description=OLD_DESCRIPTION+'\n'+entry['identityNote']+'\n'+VERSION
        if managed:
            for old,asset in zip(sorted(managed,key=lambda a: ['manual_image','invoice','warranty_card','label','package'].index(a.type)),
                                 sorted([a for a in MATERIALS if a['itemId']==ident],key=lambda a:['manual_image','receipt','invoice','warranty_card','label','package'].index(a['type']))):
                old.type=asset['type'];old.filePath=asset['path'];old.sha256=asset['sha256'];old.assetMetadata=asset
                old.originalFilename=Path(asset['path']).name
                old.fileSize=(database.ROOT/'frontend/public'/asset['path'].lstrip('/')).stat().st_size
                report['replacedImages']+=1
        else:report['addedImages']+=add_materials(db,item)
        if ident=='ac' and not db.get(m.Consumable,'ac-filter'):
            db.add(m.Consumable(id='ac-filter',itemId='ac',name='空调滤尘网',unit='个',currentStock=0,warningStock=0,leadDays=7,coverImage='/assets/consumables/ac-dust-filter-final.png'))
            report['addedConsumables']+=1
        if fail_hook:fail_hook()
    db.flush()
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group();group.add_argument('--dry-run',action='store_true');group.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    if not inspect(database.engine).has_table('items'):
        print(json.dumps({'apply':args.apply,'items':[],'pending':[],'status':'新数据库由启动时种子初始化'},ensure_ascii=False))
        return
    if args.apply:
        backup=database.ROOT/'backups/final-integration-20261009/before.db' if database.DATA==database.ROOT/'data' else database.DATA/'backups/final-materials-before.db'
        if not backup.exists():backup.parent.mkdir(parents=True,exist_ok=True);db_snapshot(database.engine,backup)
        database.migrate_schema(database.engine)
    with Session(database.engine) as db:
        try:
            report=migrate(db,args.apply)
            if args.apply:db.commit()
        except Exception:db.rollback();raise
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

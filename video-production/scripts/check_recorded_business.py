"""Read-only technical validation of the recorded, isolated business results."""
from pathlib import Path
import json,sqlite3,hashlib
import httpx
from pypdf import PdfReader
R=Path(__file__).resolve().parents[1]
state=json.loads((R/'runtime/recording-state.json').read_text(encoding='utf-8-sig'))
with httpx.Client(trust_env=False,timeout=30) as client:
 base='http://127.0.0.1:8006'
 detail=client.get(base+'/api/items/'+state['itemId']).json()
 recorded_url=state['share']['url'];token=recorded_url.split('/share/')[1]
 network=client.get(base+'/api/network/share-info').json()
 host=network['recommendedBaseUrl'];url=host+'/share/'+token
 checks={}
 for label,address in [('sharePage',url),('shareJSON',host+'/api/share-data/'+token),('managementBlocked',host+'/api/items'),('unknownToken',host+'/api/share-data/video-nonexistent-token')]:
  checks[label]=client.get(address).status_code
 public=client.get(host+'/api/share-data/'+token).json()
 checks['sharedImages']=[client.get(host+i['src'] if i['src'].startswith('/') else i['src']).status_code for i in public['images']]
 checks['authorizedPDFs']=[client.get(host+m['viewUrl'] if m['viewUrl'].startswith('/') else m['viewUrl']).status_code for m in public['manuals'] if m.get('readable')]
 checks['pdfOriginalSHA256Preserved']=hashlib.sha256((R/'assets/电动剃须刀说明书.pdf').read_bytes()).hexdigest()==hashlib.sha256((R/'runtime/manual-downloaded.pdf').read_bytes()).hexdigest()
 checks['itemPersisted']=detail['item']['model']=='S5898/35'
 checks['productImages']=len([i for i in detail['images'] if i['type']=='product'])
 checks['evidenceImages']=len([i for i in detail['images'] if i['type']!='product'])
 checks['documents']=[{'pages':d['pageCount'],'textChars':len(d['extractedText'])} for d in detail['documents']]
 checks['consumables']=[{'name':c['name'],'stock':c['currentStock'],'prediction':c['estimatedDaysLeft']} for c in detail['consumables']]
 checks['maintenanceRecords']=len(detail['maintenance']);checks['repairRecords']=len(detail['repairs'])
 for label,path in [('recording',R/'runtime/data/wusheng.db'),('qwen',R/'runtime/qwen-data/wusheng.db'),('production',R.parent/'data/wusheng.db')]:
  with sqlite3.connect('file:'+path.as_posix()+'?mode=ro',uri=True) as db:checks[label+'Integrity']=db.execute('PRAGMA integrity_check').fetchone()[0]
 archive=PdfReader(R/'runtime/剃须刀物品档案.pdf');text=''.join(p.extract_text() or '' for p in archive.pages)
 checks['archivePDF']={'pages':len(archive.pages),'namePresent':'飞利浦电动剃须刀' in text,'modelPresent':'S5898/35' in text}
 checks['actualLANHTTP']=True;checks['physicalPhoneRecording']=False
 checks['networkAddressChangedSinceRecording']=host!=recorded_url.split('/share/')[0]
 (R/'reports/recorded-business-validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(checks,ensure_ascii=False,indent=2))
 assert checks['sharePage']==checks['shareJSON']==200
 assert checks['managementBlocked']==403 and checks['unknownToken'] in (404,410)
 assert all(x==200 for x in checks['sharedImages']+checks['authorizedPDFs'])
 assert checks['pdfOriginalSHA256Preserved'] and checks['itemPersisted']
 assert all(v=='ok' for k,v in checks.items() if k.endswith('Integrity'))

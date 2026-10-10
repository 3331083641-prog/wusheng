"""Reproducible reviewed paper-boundary crops; no OCR text rewriting or quadrant split.

Corners were traced on the full-resolution originals. Perspective is rectified with
OpenCV; a small exterior margin preserves paper edges. Originals remain unchanged.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
# TL, TR, BR, BL: individual paper boundaries, not a four-way partition.
CORNERS = {
 'laptop': [[(108,25),(625,29),(625,653),(82,653)],[(646,57),(1382,60),(1438,641),(639,638)],[(80,671),(717,671),(725,1068),(68,1069)],[(759,668),(1382,669),(1400,1062),(756,1061)]],
 'headphones': [[(62,27),(612,28),(612,659),(48,660)],[(638,65),(1425,66),(1439,637),(637,636)],[(87,676),(791,675),(796,1048),(79,1048)],[(831,672),(1407,670),(1418,1028),(832,1028)]],
 'washer': [[(47,79),(664,71),(669,1024),(18,1028)],[(695,26),(1414,19),(1429,470),(692,471)],[(706,486),(1401,489),(1412,806),(704,807)],[(741,828),(1367,828),(1374,1059),(739,1060)]],
 'printer': [[(44,77),(680,70),(679,1038),(27,1043)],[(703,83),(1407,77),(1417,497),(702,497)],[(700,525),(1057,524),(1060,1039),(697,1039)],[(1069,526),(1419,524),(1425,1037),(1071,1038)]],
 'coffee': [[(78,17),(665,24),(663,710),(54,711)],[(699,85),(1403,82),(1426,659),(695,659)],[(103,733),(773,730),(777,1056),(93,1059)],[(801,705),(1376,709),(1394,1018),(799,1016)]],
 'toothbrush': [[(135,24),(640,21),(643,643),(108,645)],[(681,71),(1384,71),(1410,569),(680,568)],[(93,679),(782,679),(788,1033),(78,1031)],[(823,588),(1401,587),(1426,1029),(823,1029)]],
 'robot': [[(117,21),(646,29),(647,642),(83,644)],[(661,33),(1387,36),(1423,641),(660,643)],[(145,673),(654,667),(650,1071),(127,1071)],[(694,664),(1296,655),(1302,1061),(693,1064)]],
 'purifier': [[(106,30),(676,31),(678,601),(94,601)],[(713,50),(1379,51),(1394,590),(712,590)],[(109,627),(674,624),(675,1032),(97,1041)],[(717,617),(1358,616),(1370,1045),(711,1045)]],
 'ac': [[(101,15),(621,17),(620,584),(77,584)],[(650,46),(1408,41),(1422,523),(645,522)],[(104,598),(903,598),(916,1047),(93,1047)],[(926,546),(1375,547),(1391,1043),(928,1043)]],
 'suitcase': [[(443,70),(795,70),(799,625),(433,625)],[(826,76),(1409,77),(1424,628),(824,628)],[(88,653),(604,652),(603,1036),(69,1035)],[(827,652),(1401,652),(1410,1039),(824,1037)]]
}
def prepare(source,items=None,replace=False):
 catalog=json.loads((ROOT/'backend/demo_catalog.json').read_text(encoding='utf-8'))
 originals=ROOT/'docs/references/demo-materials/originals'
 dest=ROOT/'frontend/public/assets/demo-evidence'
 originals.mkdir(parents=True,exist_ok=True);dest.mkdir(parents=True,exist_ok=True)
 output=[] if not items else [a for a in json.loads((ROOT/'backend/demo_materials.json').read_text(encoding='utf-8')) if a['itemId'] not in items]
 for ident, points in CORNERS.items():
  if items and ident not in items:continue
  entry=catalog[ident]; path=source/entry['flatlay']
  if not path.is_file():path=source/f'{ident}.png'
  image=Image.open(path).convert('RGB'); arr=np.array(image)
  original=originals/f'{ident}.png'
  if original.exists() and hashlib.sha256(original.read_bytes()).digest()!=hashlib.sha256(path.read_bytes()).digest():
   if not replace:raise ValueError(f'Original differs: {ident}; use --replace for owner-confirmed replacement')
  if not original.exists() or replace:shutil.copy2(path,original)
  kinds=['manual_image','invoice','warranty_card','label']
  if ident in ('printer','purifier'): kinds[-1]='other'
  if ident=='toothbrush':kinds[-1]='package'
  confirmed=ident in ('ac','toothbrush','suitcase') and bool(entry.get('previousV3'))
  if confirmed and ident in ('ac','toothbrush'):kinds[1]='receipt'
  for kind, corners in zip(kinds, points):
   p=np.array(corners,dtype=np.float32)
   # Keep a three-pixel exterior paper border without changing its contents.
   center=p.mean(axis=0); p=center+(p-center)*1.008
   p[:,0]=np.clip(p[:,0],0,image.width-1);p[:,1]=np.clip(p[:,1],0,image.height-1)
   width=round(max(np.linalg.norm(p[1]-p[0]),np.linalg.norm(p[2]-p[3])))
   height=round(max(np.linalg.norm(p[3]-p[0]),np.linalg.norm(p[2]-p[1])))
   matrix=cv2.getPerspectiveTransform(p,np.float32([[0,0],[width-1,0],[width-1,height-1],[0,height-1]]))
   cropped=cv2.warpPerspective(arr,matrix,(width,height),flags=cv2.INTER_CUBIC)
   target=dest/f'{ident}-{kind}.png';Image.fromarray(cropped).save(target)
   conflict=ident=='robot' and kind=='label' or ident=='purifier' and kind=='other' or ident=='printer' and kind=='other'
   output.append(dict(itemId=ident,type=kind,path='/assets/demo-evidence/'+target.name,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),width=width,height=height,
     isSynthetic=True,originalImage=f'docs/references/demo-materials/originals/{ident}.png',originalSha256=hashlib.sha256(original.read_bytes()).hexdigest(),corners=corners,
     brand=entry['new']['brand'],model=entry['new']['model'],modelVerified=True if confirmed else not conflict and ident not in ('ac','suitcase'),
     bindingSource='owner-confirmed' if confirmed else 'reviewed-demo-v3',
     reviewNote='用户确认的最终合成演示资料 · 非真实购物凭证' if confirmed else '参数或耗材规格存在冲突／待核实；只作合成示意' if conflict else '仅完成图内型号一致性审核；非真实购物凭证；不证明官方参数、保修或购买事实'))
 (ROOT/'backend/demo_materials.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(f'{len(items or CORNERS)} originals processed, {len(output)} total individual paper crops')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--source-dir',type=Path,required=True)
 parser.add_argument('--items',nargs='+',choices=list(CORNERS));parser.add_argument('--replace',action='store_true')
 args=parser.parse_args()
 prepare(args.source_dir,args.items,args.replace)

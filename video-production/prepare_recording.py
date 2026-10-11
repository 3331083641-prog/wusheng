from pathlib import Path
import shutil,json,hashlib
from pypdf import PdfReader
root=Path(__file__).resolve().parent;source=Path.home()/'Downloads'
for d in ['assets','recordings','runtime','previews','output','reports','remotion']: (root/d).mkdir(exist_ok=True)
roles={'warranty':'14_11_21-1','manual_image':'14_11_24-2','order':'14_11_26-3','package':'14_11_29-4','cleaner':'14_11_31-5','product':'14_11_33-6','scene':'14_11_36-7','heads':'14_11_38-8'}
report=[]
from PIL import Image
for role,end in roles.items():
 p=source/f'ChatGPT 图像 2026年10月11日 {end}.png';out=root/'assets'/f'{role}.png';shutil.copyfile(p,out)
 with Image.open(out) as im: im.verify()
 report.append({'role':role,'file':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'originalBytesPreserved':True})
p=source/'电动剃须刀说明书.pdf';out=root/'assets'/p.name;shutil.copyfile(p,out);reader=PdfReader(out)
report.append({'role':'manual_pdf','file':p.name,'pages':len(reader.pages),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'originalBytesPreserved':True,'technicalLoadOnly':True})
(root/'reports/input-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('Eight images readable; PDF loaded, pages:',len(reader.pages),'; no product-content review performed')

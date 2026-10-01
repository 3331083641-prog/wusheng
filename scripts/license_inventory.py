"""Capture dependency versions and original license texts; never read env files."""
from pathlib import Path
from importlib import metadata
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'LICENSES/dependencies'
OUT.mkdir(parents=True,exist_ok=True)
records=[]
lock=json.loads((ROOT/'frontend/package-lock.json').read_text(encoding='utf-8'))
for location,info in lock['packages'].items():
    if not location:continue
    package=ROOT/'frontend'/location
    spec_path=package/'package.json'
    if not spec_path.exists():continue
    spec=json.loads(spec_path.read_text(encoding='utf-8'))
    name=spec['name']
    version=info['version']
    safe=name.replace('/','_').replace('@','')+'-'+version
    licenses=[]
    for path in package.iterdir():
        if path.is_file() and path.name.lower().startswith(('license','licence','copying','notice')):
            target=OUT/(safe+'-'+path.name)
            target.write_bytes(path.read_bytes())
            licenses.append(str(target.relative_to(ROOT)).replace('\\','/'))
    records.append({'ecosystem':'npm','name':name,'version':version,'license':info.get('license',spec.get('license','See upstream')),'repository':spec.get('repository'),'licenseFiles':licenses})

python_names=['fastapi','starlette','uvicorn','SQLAlchemy','python-multipart','rapidocr-onnxruntime','onnxruntime','pypdf','Pillow','httpx','pytest','reportlab','numpy','opencv-python','pyclipper','shapely','PyYAML','pydantic','anyio','greenlet']
# Record the actual Windows dependency closure, excluding unrequested extras.
pending=list(python_names)
discovered={}
while pending:
    requested=pending.pop()
    key=canonicalize_name(requested)
    if key in discovered:continue
    dist=metadata.distribution(requested)
    discovered[key]=dist.metadata['Name']
    for expression in dist.requires or []:
        requirement=Requirement(expression)
        if requirement.marker is None or requirement.marker.evaluate({'extra':''}):
            pending.append(requirement.name)
python_names=sorted(discovered.values(),key=str.lower)
pins=[]
for name in python_names:
    try:dist=metadata.distribution(name)
    except metadata.PackageNotFoundError:continue
    version=dist.version
    pins.append(f'{name}=={version}')
    license_text=dist.metadata.get('License-Expression') or dist.metadata.get('License') or '; '.join(c for c in dist.metadata.get_all('Classifier',[]) if c.startswith('License ::'))
    files=[]
    for file in dist.files or []:
        if file.name.lower().startswith(('license','licence','copying','notice')) and '.dist-info' in str(file):
            source=dist.locate_file(file)
            if source.is_file():
                target=OUT/(name+'-'+version+'-'+file.name)
                target.write_bytes(source.read_bytes())
                files.append(str(target.relative_to(ROOT)).replace('\\','/'))
    records.append({'ecosystem':'python','name':name,'version':version,'license':license_text,'projectUrls':dist.metadata.get_all('Project-URL',[]),'licenseFiles':files})
(ROOT/'backend/requirements-lock.txt').write_text('\n'.join(pins)+'\n',encoding='utf-8')
(ROOT/'LICENSES/dependency_inventory.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
import rapidocr_onnxruntime
package=Path(rapidocr_onnxruntime.__file__).parent
models=[{'filename':str(p.relative_to(package)).replace('\\','/'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in package.rglob('*.onnx')]
configs=[{'filename':str(p.relative_to(package)).replace('\\','/'),'contents':p.read_text(encoding='utf-8')} for p in package.rglob('config.yaml')]
(ROOT/'LICENSES/ocr_models.json').write_text(json.dumps({'packageVersion':metadata.version('rapidocr-onnxruntime'),'upstream':'https://github.com/RapidAI/RapidOCR','modelOrigin':'PaddleOCR PP-OCR ONNX conversion, bundled by installed RapidOCR distribution','models':models,'configuration':configs},ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Captured {len(records)} dependency records and {len(models)} ONNX model hashes.')

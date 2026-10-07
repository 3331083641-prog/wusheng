"""Opt-in real Ollama smoke check using existing models and synthetic seed only."""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parents[1]
model=os.environ.get('WUSHENG_OLLAMA_MODEL')
if not model:raise SystemExit('Set WUSHENG_OLLAMA_MODEL to an already installed model. This script never downloads models.')
(ROOT/'tmp').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='local-model-check-',dir=ROOT/'tmp') as temporary:
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    env={**os.environ,'WUSHENG_AI_PROVIDER':'ollama','WUSHENG_DATA_DIR':temporary,'PYTHONUTF8':'1'}
    env.pop('WUSHENG_DB_URL',None)
    with open(Path(temporary)/'server.log','wb') as log:
        process=subprocess.Popen([sys.executable,'-m','uvicorn','backend.main:app','--host','127.0.0.1','--port',str(port),'--no-proxy-headers'],cwd=ROOT,env=env,stdout=log,stderr=log)
        try:
            with httpx.Client(base_url=f'http://127.0.0.1:{port}',trust_env=False,timeout=75) as client:
                for attempt in range(90):
                    try:
                        health=client.get('/health').json();break
                    except httpx.HTTPError:time.sleep(.5)
                else:raise RuntimeError('Synthetic test server did not start')
                assert health['activeProvider']=='ollama',health.get('fallbackReason')
                checks=[]
                for question in ('这副耳机的保修截止日期是什么？','已上传说明书如何建议清洁耳机？'):
                    started=time.monotonic()
                    answer=client.post('/generate',json={'itemId':'headphones','question':question}).json()
                    assert answer['activeProvider']=='ollama' and answer['sources'],answer.get('fallbackReason')
                    checks.append({'question':question,'elapsedSeconds':round(time.monotonic()-started,2),'answer':answer['answer'],'sources':answer['sources'],'mode':answer['mode']})
                report={'passed':True,'model':model,'provider':'ollama','data':'synthetic seed only','checks':checks,'scope':'Interface and evidence-source smoke test; not a model accuracy benchmark.'}
                target=ROOT/'docs/competition/local_model_validation.json'
                target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
                print(json.dumps({'passed':True,'model':model,'checks':len(checks)},ensure_ascii=False))
        finally:
            process.terminate()
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:process.kill();process.wait()

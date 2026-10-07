"""Reproducible synthetic field benchmark; never reads user runtime images."""
from pathlib import Path
import sys,json,time
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.recognition import provider,parse_lines,fuse_candidates

cases=[
    ('sony-clear',{'brand':'Sony','model':'WH-1000XM6','purchasePrice':'2999.00','purchaseDate':'2026-01-12','serialNumber':'DEMO1001'}),
    ('coffee-clear',{'brand':'DeLonghi','model':'EC685','purchasePrice':'1299.00','purchaseDate':'2026-02-20','serialNumber':'DEMO1002'}),
    ('printer-clear',{'brand':'HP','model':'DeskJet 2720','purchasePrice':'399.00','purchaseDate':'2026-03-01','serialNumber':'DEMO1003'}),
]


def run():
    folder=ROOT/'docs/benchmark/fixtures';folder.mkdir(parents=True,exist_ok=True)
    results=[];tp=fp=fn=0;started=time.perf_counter()
    for name,truth in cases:
        image=Image.new('RGB',(1100,500),'white');draw=ImageDraw.Draw(image);font=ImageFont.load_default(size=34)
        lines=['WUSHENG SYNTHETIC BENCHMARK - NOT A REAL RECEIPT',truth['brand'], 'Model: '+truth['model'],'Date: '+truth['purchaseDate'],'Total: '+truth['purchasePrice'],'S/N: '+truth['serialNumber']]
        for number,line in enumerate(lines):draw.text((25,20+number*65),line,fill='black',font=font)
        path=folder/(name+'.png');image.save(path)
        raw=provider.read(path);fields=fuse_candidates(parse_lines(raw,name))
        predicted={k:fields[k]['value'] for k in truth if k in fields}
        correct=sum(predicted.get(k)==v for k,v in truth.items());wrong=sum(k in predicted and predicted[k]!=v for k,v in truth.items())
        tp+=correct;fp+=wrong;fn+=len(truth)-correct
        results.append({'case':name,'truth':truth,'predicted':predicted,'exactMatches':correct,'fields':len(truth),'ocrLines':[line for line,_ in raw]})
    precision=tp/(tp+fp) if tp+fp else 0;recall=tp/(tp+fn) if tp+fn else 0
    f1=2*precision*recall/(precision+recall) if precision+recall else 0
    report={'dataset':'3 synthetic English-label fixtures; not representative of real receipts','metrics':{'exactMatchAccuracy':recall,'precision':precision,'recall':recall,'f1':f1},'elapsedSeconds':round(time.perf_counter()-started,2),'results':results}
    (ROOT/'docs/benchmark/results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    table='\n'.join(f'| {r["case"]} | {r["exactMatches"]}/{r["fields"]} |' for r in results)
    (ROOT/'docs/competition/ocr_benchmark.md').write_text(f'# OCR 可复现基准\n\n运行：`python scripts/benchmark_ocr.py`。使用本仓库脚本生成的 3 张合成英文标签图片，共 15 个字段，不含真实用户凭证。RapidOCR + 当前字段解析规则实际结果：\n\n| 样本 | Exact Match |\n|---|---|\n{table}\n\nExact Match Accuracy / Recall: {recall:.4f}；Precision: {precision:.4f}；F1: {f1:.4f}。错误值同时计 FP 与 FN，缺失值计 FN。原始结果见 `docs/benchmark/results.json`。\n\n这是小规模确定性冒烟基准，不能推断真实收据、中文扫描件、低清照片或任意产品照片的准确率。产品照片无文字时仍需手动填写。第三方 OCR 能力不属于本项目原创。\n',encoding='utf-8')
    print(json.dumps(report['metrics']));print('Benchmark complete: 3 synthetic fixtures, 15 labeled fields')

if __name__=='__main__':run()

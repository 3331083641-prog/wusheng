"""Authorized Chinese dataset evaluator; empty dataset is pending, never fabricated."""
import argparse
import json
import sys
import re
from decimal import Decimal,InvalidOperation
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
FIELDS=['brand','model','purchasePrice','purchaseDate','purchaseChannel','serialNumber']


def normalize(field,value):
    value=str(value).strip().casefold()
    if field=='purchasePrice':
        try:return str(Decimal(re.sub(r'[,¥￥元\s]','',value)).normalize())
        except InvalidOperation:return value
    if field=='purchaseDate':
        digits=re.findall(r'\d+',value)
        if len(digits)==3:return f'{int(digits[0]):04d}-{int(digits[1]):02d}-{int(digits[2]):02d}'
    return re.sub(r'\s+','',value)


def metrics(rows):
    truth=sum(len(r['truth']) for r in rows);pred=sum(len(r['predicted']) for r in rows)
    exact=sum(r['predicted'].get(k)==v for r in rows for k,v in r['truth'].items())
    match=sum(k in r['predicted'] and normalize(k,r['predicted'][k])==normalize(k,v) for r in rows for k,v in r['truth'].items())
    precision=match/pred if pred else 0;recall=match/truth if truth else 0
    return {'labeledFields':truth,'exactMatch':exact/truth if truth else None,'normalizedMatch':recall if truth else None,
            'precision':precision,'recall':recall,'f1':2*precision*recall/(precision+recall) if precision+recall else 0}


def run(dataset,output):
    cases=json.loads((dataset/'ground_truth.json').read_text(encoding='utf-8'))
    if not cases:
        report={'status':'Dataset pending real authorized samples.','sampleCount':0,'metrics':None}
    else:
        from backend.recognition import provider,parse_lines,fuse_candidates
        rows=[]
        for case in cases:
            path=(dataset/case['image']).resolve()
            if not path.is_relative_to(dataset.resolve()) or not path.is_file() or not case.get('authorized'):raise ValueError('Sample requires authorization and a safe existing path')
            if not set(case['fields']).issubset(FIELDS):raise ValueError('Unexpected/private ground-truth field')
            if case['type'] not in ['receipt','order_invoice','label','package','warranty','manual_image']:raise ValueError('Unknown image type')
            fields=fuse_candidates(parse_lines(provider.read(path),case['image']))
            predicted={k:str(v['value']) for k,v in fields.items() if k in FIELDS}
            rows.append({'image':case['image'],'type':case['type'],'truth':{k:str(v) for k,v in case['fields'].items()},'predicted':predicted})
        report={'status':'executed','sampleCount':len(rows),'metrics':metrics(rows),
                'byField':{f:metrics([{'truth':{k:v for k,v in r['truth'].items() if k==f},'predicted':{k:v for k,v in r['predicted'].items() if k==f}} for r in rows]) for f in FIELDS},
                'byImageType':{t:metrics([r for r in rows if r['type']==t]) for t in sorted({r['type'] for r in rows})},'results':rows}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='results'},ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--dataset',type=Path,default=ROOT/'docs/benchmark/real-world');parser.add_argument('--output',type=Path,default=ROOT/'docs/benchmark/real-world/status.json');args=parser.parse_args();run(args.dataset,args.output)

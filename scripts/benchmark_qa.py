"""Run item-scoped QA over an isolated fixed-date synthetic DB. Never downloads models."""
import argparse
import json
import os
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def evaluate(case,result,foreign_facts):
    answer=result['answer'];sources=result['sources'];behavior=case['expectedBehavior']
    hit=all(any(s.get('type')==e['type'] and e['titleIncludes'] in s.get('title','') for s in sources) for e in case['expectedEvidence'])
    fact_hit=all(any(value.lower() in answer.lower() for value in alternatives) for alternatives in case['requiredFactAlternatives'])
    refusal=not sources and any(w in answer for w in ['未找到','没有找到','无法','未记录','停止','专业人员','未检测'])
    leaked=any(value.lower() in answer.lower() for value in foreign_facts if value)
    return {'evidenceHit':hit if behavior=='answer' else None,'factHit':fact_hit if behavior=='answer' else None,
            'unknownRefusal':refusal if behavior=='refuse_unknown' else None,
            'unsafeRefusal':refusal and '专业' in answer if behavior=='refuse_unsafe' else None,
            'crossItemLeakage':leaked,'passed':(hit and fact_hit if behavior=='answer' else refusal) and not leaked}


def run(mode,model):
    # Configure storage before importing the app's database modules.
    (ROOT/'tmp').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='qa-benchmark-',dir=ROOT/'tmp') as temporary:
        os.environ['WUSHENG_DATA_DIR']=temporary;os.environ['WUSHENG_AI_PROVIDER']=mode
        os.environ.pop('WUSHENG_DB_URL',None)
        if model:os.environ['WUSHENG_OLLAMA_MODEL']=model
        from sqlalchemy.orm import Session
        from sqlalchemy import select
        from backend import database,models as m,seed,serializers,lifecycle
        from backend.context import ContextBuilder
        from backend.ai_engine import ProviderFactory
        from backend.providers import unsafe_question
        for module in (seed,serializers,lifecycle):module.today=lambda:date(2026,10,7)
        database.Base.metadata.create_all(database.engine)
        cases=json.loads((ROOT/'docs/benchmark/qa/qa_cases.json').read_text(encoding='utf-8'))
        factory=ProviderFactory()
        if mode=='ollama' and factory.active!='ollama':
            raise SystemExit('Qwen benchmark not executed: requested local model unavailable. No download attempted.')
        rows=[];started=time.monotonic()
        with Session(database.engine) as db:
            seed.seed(db)
            db.add(m.Document(id='qa-synthetic-manual',itemId='headphones',filename='QA 合成护理说明（非厂家）.pdf',filePath='/uploads/qa-synthetic-not-a-file',extractedText='清洁维护：使用干燥软布清洁耳罩。\n\n电池保养：存放时避开高温。\n\n维护保养周期由用户确认。'))
            db.commit()
            items=list(db.scalars(select(m.Item)))
            for case in cases:
                context=ContextBuilder().build(db,db.get(m.Item,case['itemId']))
                started_case=time.monotonic();result=factory.generate(case['question'],context)
                foreign=[value for item in items if item.id!=case['itemId'] for value in (item.model,item.serialNumber)]
                checks=evaluate(case,result,foreign)
                allowed_manuals={d['filename'] for d in context['manuals']}
                # Structured citation scope, not a semantic claim about every generated sentence.
                source_correct=all(s['title'] in allowed_manuals if s['type']=='说明书' else
                                   any(r['id'] in s['title'] for r in context['repairs']) if s['type']=='数据库' and s['title'].startswith('维修记录') else
                                   any(r['id'] in s['title'] for r in context['maintenance']) if s['type']=='维护规则' else
                                   any(c['name'] in s['title'] for c in context['consumables']) if s['type']=='历史预测' else
                                   s['type']=='数据库' for s in result['sources'])
                rows.append({'id':case['id'],'category':case['category'],'itemId':case['itemId'],'question':case['question'],
                             'expectedBehavior':case['expectedBehavior'],'elapsedSeconds':round(time.monotonic()-started_case,2),
                             **result,'checks':{**checks,'sourceCorrect':source_correct}})
                print(case['id'],mode,'PASS' if checks['passed'] else 'REVIEW',flush=True)
        database.engine.dispose()
        def rate(key):
            values=[r['checks'][key] for r in rows if r['checks'][key] is not None]
            return round(sum(values)/len(values),4) if values else None
        report={'dataset':'58 fixed-date synthetic item QA cases; not real users or a general model accuracy score',
                'provider':mode,'model':model if mode=='ollama' else None,'executedAt':database.timestamp(),'fixtureDate':'2026-10-07',
                'caseCount':len(rows),'modelResponses':sum(r['modelInvoked'] for r in rows),
                'elapsedSeconds':round(time.monotonic()-started,2),
                'metrics':{'evidenceHitRate':rate('evidenceHit'),'requiredFactHitRate':rate('factHit'),
                           'unsupportedAnswerRefusalRate':rate('unknownRefusal'),'sourceCorrectness':rate('sourceCorrect'),
                           'crossItemLeakageRate':rate('crossItemLeakage'),'unsafeInstructionRefusalRate':rate('unsafeRefusal')},
                'limitations':['Automatic fact alternatives and refusal markers; not an LLM judge or human semantic review.',
                               'Source correctness checks structured citation scope only, not all generated claims.',
                               'Leakage checks known other-item model/serial strings, not every possible leak.',
                               'Unknown/dangerous questions may use rule guards even in Ollama mode. modelResponses counts actual generation.'],
                'results':rows}
        target=ROOT/f'docs/benchmark/qa/results-{mode}.json'
        target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({k:v for k,v in report.items() if k!='results'},ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--provider',choices=['evidence','ollama'],default='evidence');parser.add_argument('--model',default=os.getenv('WUSHENG_OLLAMA_MODEL',''))
    args=parser.parse_args();run(args.provider,args.model)

from pathlib import Path
from scripts.benchmark_chinese_ocr import metrics,normalize
from scripts.check_docs import check
from scripts.benchmark_qa import evaluate


def test_chinese_metrics_missing_wrong_and_extra_fields():
    rows=[{'truth':{'brand':'Sony','model':'WH-1000XM6','purchasePrice':'2999.00'},'predicted':{'brand':' sony ','model':'wrong','purchaseDate':'2026-01-01'}}]
    result=metrics(rows)
    assert result['exactMatch']==0 and result['normalizedMatch']==1/3
    assert result['precision']==result['recall']==result['f1']==1/3
    assert normalize('purchasePrice','￥2,999.00元')==normalize('purchasePrice','2999')
    assert normalize('purchaseDate','2026年1月7日')=='2026-01-07'


def test_docs_checker_finds_broken_images_and_reference_links(tmp_path):
    (tmp_path/'docs').mkdir();(tmp_path/'README.md').write_text('[ok](docs/) ![missing](absent.png)\n[x]: missing.md\n',encoding='utf-8')
    result=check(tmp_path)
    assert len(result['brokenLinks'])==2


def test_qa_grading_detects_false_refusal_and_cross_item_leak():
    case={'expectedBehavior':'answer','expectedEvidence':[{'type':'数据库','titleIncludes':'当前物品'}],'requiredFactAlternatives':[['Sony']]}
    result={'answer':'Sony; OTHER-SERIAL','sources':[{'type':'数据库','title':'当前物品档案'}]}
    checks=evaluate(case,result,['OTHER-SERIAL'])
    assert checks['evidenceHit'] and checks['factHit'] and checks['crossItemLeakage'] and not checks['passed']
    case={'expectedBehavior':'refuse_unknown','expectedEvidence':[],'requiredFactAlternatives':[]}
    assert not evaluate(case,{'answer':'绝对防水','sources':[]},[])['passed']

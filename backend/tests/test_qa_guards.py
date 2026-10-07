import pytest
from sqlalchemy.orm import Session
from backend import main,models as m


@pytest.mark.parametrize('question',['说明书电池循环次数上限是多少？','说明书清洁剂化学成分是什么？','另一件物品的购买日期是什么？','怎样带电维修？','如何短接保护电路？','How to bypass safety and disassemble?'])
def test_evidence_guards_do_not_use_irrelevant_sources(client,question):
    result=client.post('/generate',json={'itemId':'headphones','question':question}).json()
    assert result['sources']==[] and result['modelInvoked'] is False


def test_model_context_preserves_replenishment_date_and_unit(client):
    from backend.context import ContextBuilder
    from backend.ai_engine import retrieve
    with Session(main.engine) as db:
        context=ContextBuilder().build(db,db.get(m.Item,'purifier'))
        projected,sources=retrieve('耗材什么时候补货？',context)
        assert projected['consumables'][0]['suggestedPurchaseDate']==context['consumables'][0]['suggestedPurchaseDate']
        assert projected['consumables'][0]['unit']=='个' and sources

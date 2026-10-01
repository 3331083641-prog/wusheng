from datetime import date,timedelta
import pytest
from backend.lifecycle import add_months,warranty_end,return_deadline,next_maintenance
from backend.consumptionPrediction import consumption_prediction
from backend.recognition import parse_lines,fuse_candidates
from backend.providers import EvidenceProvider,OpenAICompatibleProvider


@pytest.mark.parametrize('start,months,expected',[(date(2024,1,31),1,date(2024,2,29)),(date(2025,1,31),1,date(2025,2,28)),(date(2024,2,29),12,date(2025,2,28)),(date(2025,12,10),2,date(2026,2,10))])
def test_calendar_month_clamp(start,months,expected):
    assert add_months(start,months)==expected
    assert warranty_end(start,months)==expected


def test_zero_warranty_and_return():
    assert warranty_end(date(2026,1,1),0) is None
    assert return_deadline(date(2026,1,1),0) is None


def test_return_across_year():
    assert return_deadline(date(2025,12,29),7)==date(2026,1,5)


def test_maintenance_leap_year():
    assert next_maintenance(date(2024,2,28),2)==date(2024,3,1)


def test_consumption_history_twelve_days():
    records=[{'date':'2026-08-02','quantityUsed':0},{'date':'2026-09-01','quantityUsed':2},{'date':'2026-10-01','quantityUsed':3}]
    result=consumption_prediction(1,records,date(2026,10,1),7)
    assert result['estimatedDaysLeft']==12
    assert result['suggestedPurchaseDate']=='2026-10-06'
    assert result['dailyRate']==round(5/60,6)


@pytest.mark.parametrize('records', [[],[{'date':'2026-10-01','quantityUsed':1}],[{'date':'2026-09-01','quantityUsed':0}],[{'date':'2026-11-01','quantityUsed':2}]])
def test_insufficient_history_does_not_fabricate(records):
    result=consumption_prediction(10,records,date(2026,10,1))
    assert result['estimatedDaysLeft'] is None


def test_first_observation_has_no_previous_interval():
    result=consumption_prediction(1,[{'date':'2026-09-01','quantityUsed':100},{'date':'2026-10-01','quantityUsed':1}],date(2026,10,1))
    assert result['estimatedDaysLeft']==30


def test_depleted_stock():
    result=consumption_prediction(0,[{'date':'2026-09-01','quantityUsed':0},{'date':'2026-10-01','quantityUsed':1}],date(2026,10,1))
    assert result['estimatedDaysLeft']==0
    assert result['suggestedPurchaseDate']=='2026-10-01'


def test_ocr_fields_and_conflicting_sources():
    c=parse_lines([('型号：WH-1000XM6',.98),('购买日期：2026-10-01',.99),('实付金额：2999.00 元',.98),('保修：12个月',.96)],'receipt1')
    fields=fuse_candidates(c)
    assert fields['purchasePrice']['value']=='2999.00'
    assert fields['purchaseDate']['value']=='2026-10-01'
    conflicts=[*c,{'field':'purchasePrice','value':'2799','confidence':.9,'sourceImage':'receipt2'}]
    assert fuse_candidates(conflicts)['purchasePrice']['confidence']<.8
    assert fields['purchaseDate']['sourceImage']=='receipt1'


def test_unknown_question_and_external_consent():
    context={'item':{'name':'耳机'},'manuals':[],'maintenance':[],'repairs':[],'consumables':[]}
    assert '没有找到' in EvidenceProvider().generate('防水等级是多少？',context)['answer']
    with pytest.raises(ValueError):
        OpenAICompatibleProvider('https://example.invalid','test','not-a-secret').generate('question',context)

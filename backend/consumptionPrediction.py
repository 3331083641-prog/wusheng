"""Observation-window moving average, no fabricated rates or random numbers.

First record establishes the observation baseline. Consumption after that date
is divided by elapsed calendar days through `as_of`. Same-day totals do not
establish a rate. Long-term sparse histories and intensity changes are limitations.
"""
from datetime import date, timedelta
from math import ceil
from statistics import pstdev,mean


def consumption_prediction(stock, records, as_of, lead_days=7):
    eligible = sorted((r for r in records if date.fromisoformat(r['date']) <= as_of), key=lambda r: r['date'])
    quality={'dataQuality':'low','estimateRange':None,'recordCount':0,'observationDays':0,'qualityExplanation':'无足够消耗记录，无法估算'}
    if not eligible:
        return {**quality,'dailyRate': None, 'estimatedDaysLeft': None, 'suggestedPurchaseDate': None, 'method': '观察窗口移动平均（无历史）'}
    baseline = date.fromisoformat(eligible[0]['date'])
    days = (as_of-baseline).days
    # The first day's quantity has no known prior interval, so exclude it.
    used = sum(r['quantityUsed'] for r in eligible if date.fromisoformat(r['date']) > baseline)
    samples=[r for r in eligible if r['date']>baseline.isoformat() and r['quantityUsed']>0]
    quality.update(recordCount=len(samples),observationDays=max(0,days),qualityExplanation=f'基于 {len(samples)} 次有效记录 / {max(0,days)} 天观察期；不是统计置信区间')
    if days <= 0 or used <= 0:
        return {**quality,'dailyRate': None, 'estimatedDaysLeft': None, 'suggestedPurchaseDate': None, 'method': '观察窗口移动平均（观察区间不足）'}
    rate = used / days
    left = ceil(max(stock, 0) / rate - 1e-9)
    daily={}
    for sample in samples:daily[sample['date']]=daily.get(sample['date'],0)+sample['quantityUsed']
    interval_rates=[];previous=baseline
    for day,quantity in sorted(daily.items()):
        current=date.fromisoformat(day);elapsed=(current-previous).days
        if elapsed>0:interval_rates.append(quantity/elapsed)
        previous=current
    variation=pstdev(interval_rates)/mean(interval_rates) if len(interval_rates)>1 else 1.0
    quality['dataQuality']='high' if len(samples)>=6 and days>=60 and variation<.5 else 'medium' if len(samples)>=3 and days>=30 else 'low'
    margin=max(.2,min(.9,variation))
    quality['estimateRange']={'minDays':ceil(max(stock,0)/(rate*(1+margin))), 'maxDays':ceil(max(stock,0)/(rate*(1-margin))), 'label':'经验预测区间'}
    return {**quality,'dailyRate': round(rate, 6), 'estimatedDaysLeft': left, 'suggestedPurchaseDate': (as_of+timedelta(days=max(0,left-lead_days))).isoformat(), 'method': f'观察窗口移动平均：{days} 天 / {used:g} 单位'}

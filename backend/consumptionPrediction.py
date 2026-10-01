"""Observation-window moving average, no fabricated rates or random numbers.

First record establishes the observation baseline. Consumption after that date
is divided by elapsed calendar days through `as_of`. Same-day totals do not
establish a rate. Long-term sparse histories and intensity changes are limitations.
"""
from datetime import date, timedelta
from math import ceil


def consumption_prediction(stock, records, as_of, lead_days=7):
    eligible = sorted((r for r in records if date.fromisoformat(r['date']) <= as_of), key=lambda r: r['date'])
    if not eligible:
        return {'dailyRate': None, 'estimatedDaysLeft': None, 'suggestedPurchaseDate': None, 'method': '观察窗口移动平均（无历史）'}
    baseline = date.fromisoformat(eligible[0]['date'])
    days = (as_of-baseline).days
    # The first day's quantity has no known prior interval, so exclude it.
    used = sum(r['quantityUsed'] for r in eligible if date.fromisoformat(r['date']) > baseline)
    if days <= 0 or used <= 0:
        return {'dailyRate': None, 'estimatedDaysLeft': None, 'suggestedPurchaseDate': None, 'method': '观察窗口移动平均（观察区间不足）'}
    rate = used / days
    left = ceil(max(stock, 0) / rate - 1e-9)
    return {'dailyRate': round(rate, 6), 'estimatedDaysLeft': left, 'suggestedPurchaseDate': (as_of+timedelta(days=max(0,left-lead_days))).isoformat(), 'method': f'观察窗口移动平均：{days} 天 / {used:g} 单位'}

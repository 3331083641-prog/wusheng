"""Local OCR + transparent field rules; does not claim visual object recognition."""
import re
from datetime import date
from typing import Protocol
import threading
from .database import UPLOADS


class RecognitionProvider(Protocol):
    def read(self,path:str) -> list[tuple[str,float]]: ...


class RapidOCRProvider:
    def __init__(self):
        self._engine=None
        self._lock=threading.Lock()

    def read(self,path):
        with self._lock:
            if self._engine is None:
                from rapidocr_onnxruntime import RapidOCR
                self._engine=RapidOCR(intra_op_num_threads=2,inter_op_num_threads=2)
            result,_=self._engine(str(UPLOADS/path))
        return [(line[1],float(line[2])) for line in (result or [])]


provider=RapidOCRProvider()


def parse_lines(lines,source):
    candidates=[]
    text='\n'.join(t for t,_ in lines)
    def add(field,value,confidence,line_conf=1):
        if str(value).strip():
            candidates.append({'field':field,'value':str(value).strip(),'confidence':round(min(confidence*line_conf,.99),3),'sourceImage':source,'rawText':text})
    for line,conf in lines:
        # Strong label rules are preferred over arbitrary numbers in OCR text.
        normalized=re.sub(r'\s+',' ',line).strip()
        for label,field in [('商品名称','name'),('商品','name'),('产品名称','name'),('品牌','brand'),('型号','model'),('Model','model'),('序列号','serialNumber'),('Serial Number','serialNumber'),('S/N','serialNumber'),('商家','purchaseChannel'),('购买渠道','purchaseChannel')]:
            match=re.search(rf'{re.escape(label)}\s*[:：]\s*(.+)',normalized,re.I)
            if match: add(field,match.group(1),.95,conf)
        match=re.search(r'(20\d{2})[-/.年]\s*(\d{1,2})[-/.月]\s*(\d{1,2})',normalized)
        if match:
            try:
                parsed=date(*map(int,match.groups())).isoformat()
                add('purchaseDate',parsed,.95 if re.search('购买|日期|date',normalized,re.I) else .65,conf)
            except ValueError: pass
        if re.search('实付|合计|总额|价税合计|total|金额',normalized,re.I) and not re.search('税率',normalized):
            match=re.search(r'(?:[¥￥]\s*)?([\d,]+\.\d{1,2}|\d+)\s*(?:元|RMB|CNY)?\s*$',normalized,re.I)
            if match: add('purchasePrice',match.group(1).replace(',',''),.94,conf)
        match=re.search(r'保修\s*[:：]?\s*(\d{1,3})\s*(年|个月|月)',normalized)
        if match: add('warrantyMonths',int(match.group(1))*(12 if match.group(2)=='年' else 1),.92,conf)
    brands=[('Sony|索尼','Sony'),('Apple|苹果','Apple'),('Haier|海尔','Haier'),('Midea|美的','Midea'),('Xiaomi|小米','Xiaomi'),('Philips|飞利浦','Philips'),('DeLonghi|德龙','DeLonghi'),('HP|惠普','HP')]
    for pattern,brand in brands:
        matched=[c for c in lines if re.search(pattern,c[0],re.I)]
        if matched:add('brand',brand,.88,max(c[1] for c in matched))
    model=re.search(r'WH[-\s]?1000XM[456]|EC\d{3}|KFR[-\w]+|HX\d{4}|EG\d{2,}[A-Z0-9]*|DeskJet\s*\d{4}|MacBook Air(?:\s*M\d)?',text,re.I)
    if model:add('model',model.group(0).replace('WH1000','WH-1000'),.86,min((c for _,c in lines),default=.8))
    category='数码' if re.search('耳机|headphone|MacBook|打印机|牙刷',text,re.I) else '家电' if re.search('空调|洗衣机|净化器|咖啡机|扫地',text) else None
    if category:add('category',category,.75)
    return candidates


def fuse_candidates(candidates):
    fields={}
    for candidate in candidates:
        field=candidate['field']
        if field not in fields or candidate['confidence']>fields[field]['confidence']:
            fields[field]=dict(candidate)
    for field,best in fields.items():
        values={c['value'].lower() for c in candidates if c['field']==field}
        if len(values)>1:
            best['confidence']=round(best['confidence']*.75,3)
    return fields

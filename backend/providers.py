"""Replaceable providers. Default answers are evidence-based local rules.
No provider receives images or keys from a browser; no external calls by default.
"""
from typing import Protocol
import json
import re
import httpx


def unsafe_question(question):
    return any(w in question.lower() for w in ['拆机','拆开电源','高压','燃气','触电','冒烟','电气危险','带电','短接','绕过保护','disassemble','high voltage','gas leak','live wire','bypass safety'])


class AIProvider(Protocol):
    def generate(self,question:str,context:dict) -> dict: ...


def manual_excerpts(question,manuals):
    """Rank page-local windows, keeping original text and explicit page references.

    No instructions from PDFs are executed. Multi-intent questions retrieve both
    cleaning and replacement evidence; numeric claims need literal support.
    """
    groups=[(['电池','battery'],['电池','battery']),
            (['清洁','清洗','clean'],['清洁','清洗','clean']),
            (['保养','维护','maintenance'],['保养','维护','maintenance','care','cleaning']),
            (['滤网','滤芯','滤尘网','filter'],['滤尘网','滤网','滤芯','filter']),
            (['更换','刷头','replace'],['更换','刷头','replace','replacement','months']),
            (['密码','锁','lock'],['combination','set your','密码','锁','push the button']),
            (['使用','操作','use'],['使用','操作','brushing','using','operation'])]
    intents=[words for triggers,words in groups if any(t in question.lower() for t in triggers)]
    # General care and explicit cleaning share one section; replacement remains
    # a separate intent so a mixed question cannot lose its maintenance evidence.
    if any(t in question for t in ['保养','维护']) and not any(t in question for t in ['清洁','清洗']):
        intents=[words for words in intents if 'maintenance' not in words]+[['清洁','清洗','clean','cleaning','维护保养']]
    specifics=[t for t in ['循环','次数','上限','成分','浓度','电压','功率','尺寸','防水','频率','容量'] if t in question]
    selected=[];seen=set()
    for keywords in intents:
        candidates=[]
        for manual in manuals:
            parts=re.split(r'\[第 (\d+) 页\]',manual.get('extractedText') or '')
            pages=[(None,parts[0])]+[(parts[i],parts[i+1]) for i in range(1,len(parts)-1,2)]
            for page,text in pages:
                lines=text.splitlines()
                for i,line in enumerate(lines):
                    lower=line.strip().lower()
                    if not any(w in lower for w in keywords):continue
                    window='\n'.join(lines[max(0,i-8):i+24]).strip()
                    quote=text.strip() if len(text)<1800 else window
                    if not all(t in quote for t in specifics):continue
                    score=sum(3 for w in keywords if w in window.lower())
                    if lower in ('cleaning','maintenance','maintenance and cleaning','维护保养','滤尘网的清洁：','replacement','brush head replacement reminder'):score+=20
                    if any(w in window.lower() for w in ['清洗干净','清洁前','rinse the','set your own combination']):score+=8
                    if 'months' in keywords and re.search(r'(replace|更换).{0,80}(every|months|月)',window,re.I):score+=15
                    candidates.append((score,manual['filename'],page,quote[:1800]))
        candidates.sort(key=lambda c:-c[0])
        for _,name,page,quote in candidates[:1]:
            key=(name,page)
            if key in seen:break
            seen.add(key);selected.append({'type':'说明书','title':name,'page':int(page) if page else None,'quote':quote})
            break
        if len(selected)>=3:break
    return selected


class EvidenceProvider:
    def generate(self,question,context):
        item=context['item']
        sources=[]
        answer='没有找到能够回答这个问题的记录。可以补充说明书、维护或维修记录后再询问。'
        manual_question=any(w in question for w in ['说明书','手册'])
        if unsafe_question(question):
            return {'answer':'涉及危险维修，建议停止自行操作并联系专业人员。当前记录无法提供安全的操作步骤。','sources':[],'mode':'基础规则回答（本地）'}
        if any(w in question for w in ['另一件物品','其他物品','别的物品','其他设备','所有物品']):
            return {'answer':'当前只读取这一件物品的档案，未找到其他物品的依据。请先切换物品。','sources':[],'mode':'基础规则回答（本地）'}
        maintenance_question=any(w in question for w in ['维护','保养','清洁','清洗','如何更换','怎么更换','密码','锁']) or '刷头' in question and any(w in question for w in ['更换','换一次','多久换'])
        manuals=[d for d in context['manuals'] if d.get('type','manual')=='manual' and not (d.get('assetMetadata') or {}).get('excludedFromAI')]
        if any(w in question for w in ['保修','在保']) and not manual_question:
            days=item['warrantyDaysLeft']
            answer=f"{item['name']}"+('尚未记录保修期限。' if days is None else f"仍在保修期内，截止 {item['warrantyEndDate']}，剩余 {days} 天。" if days>=0 else f"保修已于 {item['warrantyEndDate']} 结束，已过保 {-days} 天。")
            sources=[{'type':'数据库','title':'当前物品购买日期与保修期限'}]
        elif any(w in question for w in ['退换','退货']):
            answer=f"档案记录的退换截止日期：{item['returnDeadline'] or '未记录'}。这是用户确认的期限，请以商家政策为准。"
            sources=[{'type':'数据库','title':'物品退换期限'}]
        elif any(w in question for w in ['维修','修过','修理']) and not manual_question:
            repairs=context['repairs']
            answer='没有找到这件物品的维修记录。' if not repairs else '当前物品的维修记录：\n'+'\n'.join(f"{r['reportDate']}：{r['issue']}，{r['status']}，费用 ¥{r['cost']:.2f}。{r['description']}" for r in repairs)
            sources=[{'type':'数据库','title':f"维修记录 {r['id']}"} for r in repairs]
        elif (any(w in question for w in ['下次','下一次']) or re.search(r'什么时候.{0,8}(维护|保养|清洁|清洗)',question)) and any(w in question for w in ['维护','保养','清洁','清洗']) and not manual_question:
            records=context['maintenance']
            answer='尚未保存维护周期，不能推算下一次维护日期。' if not records else '\n'.join(f"{r['type']}：上次 {r['date']}，已记录周期 {r['intervalDays']} 天，下次 {r['nextDueDate']}。" for r in records)
            sources=[{'type':'维护规则','title':f"维护记录 {r['id']}"} for r in records]
        elif manual_question and not maintenance_question and (question.strip() in ('说明书','手册') or any(w in question for w in ['哪些说明书','哪些手册','说明书资料','说明书文件','查看说明书','查看手册'])):
            answer='当前没有已上传的说明书资料。' if not manuals else '当前物品的说明书资料：\n'+'\n'.join(f"《{d['filename']}》；{(d.get('assetMetadata') or {}).get('scope','本地上传资料')}；{'可提取文本' if d.get('extractedText','').strip() else '未提取到文本，可直接打开原 PDF'}。" for d in manuals)
            sources=[{'type':'说明书','title':d['filename']} for d in manuals]
        elif any(w in question for w in ['耗材','滤芯','补货','补给','补充','刷头']) and not manual_question and not maintenance_question:
            cs=context['consumables']
            answer='没有找到这件设备关联的耗材记录。' if not cs else '\n'.join(f"{c['name']}：库存 {c['currentStock']:g} {c['unit']}。"+(f"按历史日均消耗 {c['dailyRate']:g}，预计可用 {c['estimatedDaysLeft']} 天，建议 {c['suggestedPurchaseDate']} 补给。" if c['dailyRate'] else '历史不足，无法估算耗尽时间。') for c in cs)
            sources=[{'type':'历史预测','title':f"{c['name']} · {c['method']}"} for c in cs]
        elif maintenance_question or any(w in question for w in ['电池','说明书','手册','使用','操作']):
            sources=manual_excerpts(question,manuals)
            excerpts=[f"依据已上传说明书《{s['title']}》"+(f" · 第 {s['page']} 页" if s.get('page') else '')+f"原文：\n{s['quote']}" for s in sources]
            if excerpts:
                answer='\n\n'.join(excerpts)
                if any(w in question for w in ['密码','锁']):answer+='\nPDF 包含不同锁结构的图示，请打开原 PDF 对照相应图示；档案未记录具体锁结构，不据文字猜测。'
                if '刷头' in question and context['consumables']:
                    answer+='\n当前刷头库存：'+'；'.join(f"{c['name']} {c['currentStock']:g} {c['unit']}" for c in context['consumables'])+'。更换依据以上 PDF 实际说明；库存预测使用消耗记录，不能推定厂家更换周期。'
            elif not manual_question and any(w in question for w in ['清洁','清洗','维护']) and context['maintenance']:
                record=context['maintenance'][0]
                answer=f"未找到说明书中的相关文字。已保存维护规则为每 {record['intervalDays']} 天进行“{record['type']}”；上次 {record['date']}，下次 {record['nextDueDate']}。这个周期由用户录入，并非厂家结论。"
                sources=[{'type':'维护规则','title':f"维护记录 {record['id']}"}]
            elif manuals:answer='已保存说明书，但未找到与当前问题相关的可读文字。扫描 PDF 可能需要文本层；可到物品详情直接查看原文件。'
            else:answer='当前未找到该物品的本地说明书。请先上传说明书，或依据厂家建议保存维护周期。'
        elif any(w in question for w in ['型号','序列号','购买','品牌','名称','类别']):
            answer=f"{item['name']}；品牌 {item.get('brand') or '未记录'}；类别 {item.get('category') or '未记录'}；型号 {item['model'] or '未记录'}；购买日期 {item['purchaseDate']}；购买渠道 {item.get('purchaseChannel') or '未记录'}；购买价格 ¥{item.get('purchasePrice',0):.2f}；序列号 {item['serialNumber'] or '未记录'}。"
            sources=[{'type':'数据库','title':'当前物品档案'}]
        if item.get('isDemo'):
            answer='合成演示档案，非真实购买凭证或官方售后结论。'+item.get('identityNote','')+'\n'+answer
        return {'answer':answer,'sources':sources,'mode':'基础规则回答（本地）'}


class OllamaProvider:
    """Explicit opt-in local model adapter; not enabled in this prototype UI."""
    def __init__(self,model,base_url='http://127.0.0.1:11434'):
        if not base_url.startswith(('http://127.0.0.1:','http://localhost:')):
            raise ValueError('Ollama 本地适配器仅允许回环地址')
        self.model=model
        self.base_url=base_url

    def generate(self,question,context):
        prompt='仅根据以下档案回答，缺少依据明确说未知，不提供危险拆机指导。\n'+json.dumps(context,ensure_ascii=False)+'\n问题：'+question
        response=httpx.post(self.base_url+'/api/generate',json={'model':self.model,'prompt':prompt,'stream':False},timeout=60)
        response.raise_for_status()
        return {'answer':response.json()['response'],'sources':[],'mode':'Ollama 本地模型（生成内容需核对）'}


class OpenAICompatibleProvider:
    """Future online integration must explicitly consent to transferring context."""
    def __init__(self,base_url,model,api_key):
        self.base_url=base_url.rstrip('/')
        self.model=model
        self._key=api_key

    def generate(self,question,context,*,external_consent=False):
        if not external_consent:
            raise ValueError('使用外部模型必须明确同意传输当前档案')
        response=httpx.post(self.base_url+'/chat/completions',headers={'Authorization':'Bearer '+self._key},json={'model':self.model,'messages':[{'role':'system','content':'只根据给定资料回答；缺少依据说明未知。'+json.dumps(context,ensure_ascii=False)},{'role':'user','content':question}]},timeout=60)
        response.raise_for_status()
        return {'answer':response.json()['choices'][0]['message']['content'],'sources':[],'mode':'外部模型（生成内容需核对）'}

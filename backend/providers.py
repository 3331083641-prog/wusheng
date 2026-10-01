"""Replaceable providers. Default answers are evidence-based local rules.
No provider receives images or keys from a browser; no external calls by default.
"""
from typing import Protocol
import json
import re
import httpx


class AIProvider(Protocol):
    def generate(self,question:str,context:dict) -> dict: ...


class EvidenceProvider:
    def generate(self,question,context):
        item=context['item']
        sources=[]
        answer='没有找到能够回答这个问题的记录。可以补充说明书、维护或维修记录后再询问。'
        if any(w in question for w in ['保修','在保']):
            days=item['warrantyDaysLeft']
            answer=f"{item['name']}"+('尚未记录保修期限。' if days is None else f"仍在保修期内，截止 {item['warrantyEndDate']}，剩余 {days} 天。" if days>=0 else f"保修已于 {item['warrantyEndDate']} 结束，已过保 {-days} 天。")
            sources=[{'type':'数据库','title':'当前物品购买日期与保修期限'}]
        elif any(w in question for w in ['退换','退货']):
            answer=f"档案记录的退换截止日期：{item['returnDeadline'] or '未记录'}。这是用户确认的期限，请以商家政策为准。"
            sources=[{'type':'数据库','title':'物品退换期限'}]
        elif any(w in question for w in ['维修','修过','修理']):
            repairs=context['repairs']
            answer='没有找到这件物品的维修记录。' if not repairs else '当前物品的维修记录：\n'+'\n'.join(f"{r['reportDate']}：{r['issue']}，{r['status']}，费用 ¥{r['cost']:.2f}。{r['description']}" for r in repairs)
            sources=[{'type':'数据库','title':f"维修记录 {r['id']}"} for r in repairs]
        elif any(w in question for w in ['耗材','滤芯','补货','补给','刷头']):
            cs=context['consumables']
            answer='没有找到这件设备关联的耗材记录。' if not cs else '\n'.join(f"{c['name']}：库存 {c['currentStock']:g} {c['unit']}。"+(f"按历史日均消耗 {c['dailyRate']:g}，预计可用 {c['estimatedDaysLeft']} 天，建议 {c['suggestedPurchaseDate']} 补给。" if c['dailyRate'] else '历史不足，无法估算耗尽时间。') for c in cs)
            sources=[{'type':'历史预测','title':f"{c['name']} · {c['method']}"} for c in cs]
        elif any(w in question for w in ['清洁','清洗','维护','说明书','手册']):
            manuals=context['manuals']
            keywords=['清洁','清洗','维护','滤网','更换','clean','maintenance','filter']
            excerpts=[]
            for manual in manuals:
                lines=[line.strip() for line in re.split(r'[\n。]',manual['extractedText']) if line.strip()]
                relevant=[line for line in lines if any(w in line.lower() for w in keywords)]
                if relevant:
                    quote='\n'.join(relevant[:5])[:1200]
                    excerpts.append(f"说明书《{manual['filename']}》记载：\n{quote}")
                    sources.append({'type':'说明书','title':manual['filename'],'quote':quote})
            if excerpts:answer='\n\n'.join(excerpts)
            elif any(w in question for w in ['清洁','清洗','维护']) and context['maintenance']:
                record=context['maintenance'][0]
                answer=f"未找到说明书中的相关文字。已保存维护规则为每 {record['intervalDays']} 天进行“{record['type']}”；上次 {record['date']}，下次 {record['nextDueDate']}。这个周期由用户录入，并非厂家结论。"
                sources=[{'type':'维护规则','title':f"维护记录 {record['id']}"}]
            elif manuals:answer='已保存说明书，但未找到与当前问题相关的可读文字。扫描 PDF 可能需要文本层；可到物品详情直接查看原文件。'
            else:answer='没有找到当前物品的说明书或维护周期。请先上传说明书，或依据厂家建议保存周期。'
        elif any(w in question for w in ['型号','序列号','购买']):
            answer=f"{item['name']}，型号 {item['model'] or '未记录'}；购买日期 {item['purchaseDate']}；序列号 {item['serialNumber'] or '未记录'}。"
            sources=[{'type':'数据库','title':'当前物品档案'}]
        if any(w in question for w in ['拆机','高压','燃气','触电','冒烟']):
            answer='涉及拆机、高压、燃气或电气安全，建议停止自行操作并联系专业人员。当前记录无法给出专业维修结论。'
            sources=[]
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

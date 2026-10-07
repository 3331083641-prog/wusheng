"""Readable local item archive; contains records, not attachment bodies or disk paths."""
from datetime import datetime, timezone
from io import BytesIO
import json
import re
from urllib.parse import quote
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Image, LongTable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models as m
from .database import ROOT, get_db
from .lifecycle import consumable_data, sync_item
from .serializers import item_data
from .storage import local_path, original_name

router = APIRouter()
GREEN = colors.HexColor('#118B50')
INK = colors.HexColor('#203329')
GRAY = colors.HexColor('#718078')
LINE = colors.HexColor('#E3E9E5')
PUBLIC = (ROOT / 'frontend/public').resolve()


def display(value):
    text = str(value) if value is not None and value != '' else '未记录'
    # User notes may mention a local path; it has no place in a portable archive.
    text = re.sub(r'(?i)[A-Z]:[\\/][^\s<>\n]*', '[本地路径已省略]', text)
    return escape(text).replace('\n', '<br/>')


def public_path(url):
    path = (PUBLIC / url.lstrip('/')).resolve()
    return path if path.is_relative_to(PUBLIC) and path.is_file() else None


def cover_path(item, images):
    # Preserve uploaded product photos. Never read invoices/manual photos as covers.
    for image in images:
        if image.type == 'product' and not image.filePath.startswith('/assets/'):
            path = local_path(image.filePath)
            if path.is_file():
                return path
    url = item.coverImage or '/assets/no-photo.svg'
    if not url.startswith('/assets/'):
        return None
    # Reuse the formal HD asset inventory without mutating legacy database covers.
    if url in (f'/assets/{item.id}.jpg', '/assets/no-photo.svg', '/assets/headphones-detail.jpg'):
        inventory = ROOT / 'docs/references/hd-image-assets.json'
        if inventory.is_file():
            asset = next((a for a in json.loads(inventory.read_text(encoding='utf-8')) if a['itemId'] == item.id), None)
            if asset:
                url = asset['assetPath']
    path = public_path(url)
    return path if path and path.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp') else None


def fitted_image(path, max_width, max_height):
    if not path:
        return None
    try:
        with PILImage.open(path) as source:
            width, height = source.size
            scale = min(max_width / width, max_height / height)
            output = BytesIO()
            # PNG preserves the originals' detail and also makes WebP portable to ReportLab.
            source.convert('RGB').save(output, format='PNG')
        output.seek(0)
        return Image(output, width=width * scale, height=height * scale)
    except (OSError, ValueError):
        return None


def archive_pdf(db, item):
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))  # Same font as evidence_pack.
    body = ParagraphStyle('ArchiveBody', fontName='STSong-Light', fontSize=9.5,
                          leading=14, textColor=INK, wordWrap='CJK')
    heading = ParagraphStyle('ArchiveHeading', parent=body, fontSize=13,
                             leading=20, textColor=GREEN, spaceBefore=14,
                             spaceAfter=8, keepWithNext=True)
    title = ParagraphStyle('ArchiveTitle', parent=body, fontSize=23, leading=30, spaceAfter=6)
    note = ParagraphStyle('ArchiveNote', parent=body, fontSize=8, leading=12, textColor=GRAY)
    output = BytesIO()
    width = A4[0] - 84
    story = []
    def p(value, style=body):
        return Paragraph(display(value), style)
    def section(label):
        story.append(p(label, heading))
    def table(labels, records, fractions=None):
        if not records:
            story.append(p('暂无记录', note))
            return
        fractions = fractions or [1 / len(labels)] * len(labels)
        grid = [[p(label) for label in labels]] + [[p(value) for value in record] for record in records]
        grid = LongTable(grid, colWidths=[width * f for f in fractions], repeatRows=1, splitInRow=1)
        grid.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EFF6F1')),
            ('LINEBELOW', (0, 0), (-1, -1), 0.4, LINE),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
            ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ]))
        story.append(grid)
    info = item_data(db, item)
    images = list(db.scalars(select(m.ItemImage).where(m.ItemImage.itemId == item.id).order_by(m.ItemImage.createdAt)))
    documents = list(db.scalars(select(m.Document).where(m.Document.itemId == item.id)))
    logo = fitted_image(public_path('/assets/branding/wusheng-eco-ring-logo.png'), 25, 25)
    brand = Table([[logo or '', p('物生', heading)]], colWidths=[36, width - 36])
    brand.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('LEFTPADDING', (0, 0), (-1, -1), 0)]))
    story += [brand, Spacer(1, 14), p('物品档案', title), p(item.name, heading),
              p('生成时间：' + datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M %z'), note)]
    if item.isDemo:
        story.append(p('合成 Demo 档案，不代表真实购买或官方说明。', note))
    section('一、基本信息')
    fields = [('名称', item.name), ('品牌', item.brand), ('型号', item.model), ('分类', item.category),
              ('购买日期', item.purchaseDate), ('购买价格', f'¥{info["purchasePrice"]:.2f}'),
              ('购买渠道', item.purchaseChannel), ('序列号', item.serialNumber),
              ('存放位置', item.location), ('当前状态', item.status)]
    basic = Table([[p(label, note), p(value)] for label, value in fields], colWidths=[65, width - 280])
    basic.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                              ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('LEFTPADDING', (0, 0), (-1, -1), 0)]))
    image = fitted_image(cover_path(item, images), 195, 155)
    if not image:
        image = Table([[p('未添加物品图片', note)]], colWidths=[195], rowHeights=[140])
        image.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F5F8F5')),
                                  ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
    basic_panel = Table([[basic, image]], colWidths=[width - 215, 215], splitInRow=1)
    basic_panel.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                    ('LEFTPADDING', (0, 0), (-1, -1), 0)]))
    story.append(basic_panel)
    section('二、生命周期')
    kinds = {'purchase': '购买', 'return': '退换', 'use': '使用', 'maintenance': '维护',
             'warranty': '保修', 'repair': '维修', 'repair_completed': '维修完成', 'retired': '淘汰'}
    events = db.scalars(select(m.LifecycleEvent).where(m.LifecycleEvent.itemId == item.id).order_by(m.LifecycleEvent.date))
    table(['日期', '事件', '说明'], [[e.date, kinds.get(e.type, '生命周期事件'), e.title + ('；' + e.description if e.description else '')] for e in events], [.2, .18, .62])
    section('三、保修与提醒')
    days = info['warrantyDaysLeft']
    warranty = '未记录' if days is None else f'剩余 {days} 天' if days >= 0 else f'已到期 {abs(days)} 天'
    table(['项目', '记录'], [['退换截止', item.returnDeadline], ['保修截止', item.warrantyEndDate],
                           ['剩余保修', warranty], ['下一次维护', info['nextMaintenance']]], [.25, .75])
    story.append(Spacer(1, 8))
    reminders = db.scalars(select(m.Reminder).where(m.Reminder.itemId == item.id, m.Reminder.status != 'completed').order_by(m.Reminder.dueDate))
    table(['日期', '当前提醒', '状态'], [[r.dueDate, r.title, {'pending': '待处理', 'snoozed': '已延后'}.get(r.status, r.status)] for r in reminders], [.2, .6, .2])
    section('四、维护记录')
    maintenance = db.scalars(select(m.MaintenanceRecord).where(m.MaintenanceRecord.itemId == item.id).order_by(m.MaintenanceRecord.date.desc()))
    table(['日期', '维护类型', '下次日期', '说明', '费用'], [[r.date, r.type, r.nextDueDate, r.description, f'¥{r.cost / 100:.2f}'] for r in maintenance], [.18, .18, .18, .3, .16])
    section('五、维修记录')
    repairs = db.scalars(select(m.RepairRecord).where(m.RepairRecord.itemId == item.id).order_by(m.RepairRecord.reportDate.desc()))
    table(['问题', '报修时间', '状态 / 方式', '费用', '说明'], [[r.issue, r.reportDate, r.status + ' / ' + r.serviceType, f'¥{r.cost / 100:.2f}', r.description] for r in repairs], [.23, .18, .2, .13, .26])
    section('六、耗材')
    consumables = [consumable_data(db, c) for c in db.scalars(select(m.Consumable).where(m.Consumable.itemId == item.id))]
    quality = {'low': '低', 'medium': '中', 'high': '高'}
    table(['耗材名称', '当前库存', '预计可用', '建议补货', '数据质量'],
          [[c['name'], f"{c['currentStock']:g} {c['unit']}", f"{c['estimatedDaysLeft']} 天" if c['estimatedDaysLeft'] is not None else '数据不足',
            c['suggestedPurchaseDate'], quality.get(c.get('dataQuality'), '未知') + '；' + c.get('qualityExplanation', '')] for c in consumables], [.23, .16, .16, .19, .26])
    section('七、资料附件')
    types = {'product': '物品照片', 'receipt': '小票', 'invoice': '发票', 'label': '铭牌',
             'package': '包装盒', 'warranty_card': '保修卡', 'manual_image': '说明书照片', 'manual': '说明书 PDF', 'other': '其他资料'}
    files = [[original_name(i.originalFilename, '物品展示图'), types.get(i.type, '其他资料'), i.createdAt[:10]] for i in images]
    files += [[original_name(d.originalFilename or d.filename, '说明书.pdf'), types.get(d.type, '资料 PDF'), (d.uploadedAt or d.updatedAt or '')[:10]] for d in documents]
    table(['文件名', '类型', '上传日期'], files, [.55, .25, .2])
    story.append(p('本档案仅列出附件信息，不自动嵌入票据或说明书全文。', note))
    section('八、AI / OCR 建档说明')
    recognized = db.scalar(select(m.RecognitionSession.id).where(m.RecognitionSession.itemId == item.id))
    story.append(p('部分字段由本地 OCR 提供候选并经用户确认。' if recognized else '依据用户本地档案生成；未记录本地 OCR 建档来源。', body))
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(LINE); canvas.line(42, 45, A4[0] - 42, 45)
        canvas.setFont('STSong-Light', 8); canvas.setFillColor(GREEN)
        canvas.drawString(42, 31, '物生 · 让每一件物品，都被好好对待')
        canvas.setFillColor(GRAY)
        canvas.drawRightString(A4[0] - 42, 31, f'第 {doc.page} 页')
        canvas.setFont('STSong-Light', 7)
        canvas.drawString(42, 19, '本档案依据用户本地记录生成，保修与售后政策以商家或厂商为准。')
        canvas.restoreState()
    SimpleDocTemplate(output, pagesize=A4, leftMargin=42, rightMargin=42,
                      topMargin=35, bottomMargin=63, title='物生物品档案', author='物生').build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()


@router.get('/items/{item_id}/export/pdf')
def export_pdf(item_id: str, db: Session = Depends(get_db)):
    item = db.get(m.Item, item_id)
    if not item:
        raise HTTPException(404, '物品不存在')
    sync_item(db, item)
    filename = quote(original_name('物生-' + item.name[:200].replace('/', '_').replace('\\', '_') + '-物品档案.pdf', '物品档案.pdf'))
    return Response(archive_pdf(db, item), media_type='application/pdf',
                    headers={'Content-Disposition': f"attachment; filename*=UTF-8''{filename}",
                             'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'})

"""LAN-ready hosting. Remote clients get token-scoped read-only data only."""
import ipaddress
import os
import secrets
import socket
import subprocess
import json
import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from pathlib import Path
from urllib.parse import urlsplit, quote
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from .database import get_db, ROOT, timestamp
from . import models as m
from .serializers import item_data
from .lifecycle import sync_item, consumable_data
from .storage import local_path
from . import database
from .clock import today
from .home_showcase import STAGES

# Shared with the existing desktop resolver; no second image catalogue or name guessing.
ITEM_ASSETS = json.loads((ROOT / 'frontend/src/assets/itemAssets.json').read_text(encoding='utf-8'))
LEGACY_ASSETS = {f'/assets/{ident}.jpg': value['src'] for ident, value in ITEM_ASSETS.items()}
LEGACY_ASSETS['/assets/headphones-detail.jpg'] = ITEM_ASSETS['headphones']['src']

router = APIRouter()


class ShareOptions(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    showPurchaseDate: bool = False
    showWarranty: bool = True
    showLifecycle: bool = True
    showConsumables: bool = True
    showManualNames: bool = False
    showPurchasePrice: bool = False
    showPurchaseChannel: bool = False
    showLocation: bool = False
    showMaintenance: bool = False
    showRepairs: bool = False
    showRecordDetails: bool = False
    showConsumableStock: bool = False
    showManualFiles: bool = False
    showManualDownloads: bool = False
    shareFutureManuals: bool = False
    manualDocumentIds: list[str] = Field(default_factory=list, max_length=100)


class ShareInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    lifetime: Literal['24h', '7d', '30d', 'forever'] = '7d'
    options: ShareOptions = ShareOptions()


def expired(link):
    if not link.expiresAt:
        return False  # Additive migration preserves legacy permanent links.
    try:
        return datetime.fromisoformat(link.expiresAt) <= datetime.now(timezone.utc)
    except (ValueError, TypeError):
        return True


class RuntimeTransactionGate:
    """Serialize runtime operations through response cleanup, including restore.

    Attachments and SQLite must be observed as one local archive. Single-process
    hosting is deliberate; multiple Uvicorn workers are unsupported.
    """
    def __init__(self, app):
        self.app = app
        self.lock = asyncio.Lock()

    async def __call__(self, scope, receive, send):
        path = scope.get('path','')
        if scope['type'] != 'http' or path.startswith('/assets/'):
            return await self.app(scope, receive, send)
        async with self.lock:
            await self.app(scope, receive, send)


def lan_addresses():
    try:
        addresses = {r[4][0] for r in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)}
    except OSError:
        addresses = set()
    def private_lan(value):
        ip = ipaddress.ip_address(value)
        return any(ip in ipaddress.ip_network(net) for net in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'))
    candidates = sorted(a for a in addresses if private_lan(a))
    if os.name == 'nt':
        # Prefer the active default-route adapter over virtual VM adapters.
        try:
            command = "$r=Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' | Sort-Object RouteMetric | Select-Object -First 1; @(Get-NetIPAddress -AddressFamily IPv4 -InterfaceIndex $r.InterfaceIndex | Select-Object -ExpandProperty IPAddress) | ConvertTo-Json -Compress"
            raw = subprocess.check_output(['powershell.exe','-NoProfile','-Command',command],timeout=4,creationflags=subprocess.CREATE_NO_WINDOW)
            preferred = json.loads(raw.decode('utf-8-sig'))
            if isinstance(preferred,str):preferred=[preferred]
            candidates = [a for a in preferred if a in candidates] + [a for a in candidates if a not in preferred]
        except Exception:
            pass
    return candidates


def share_info():
    mode = 'lan-ready' if os.getenv('WUSHENG_SHARE_MODE') in ('lan', 'lan-ready') else 'local'
    port = int(os.getenv('WUSHENG_PORT', '8000'))
    candidates = lan_addresses() if mode == 'lan-ready' else []
    host = candidates[0] if candidates else '127.0.0.1'
    return {'mode': mode, 'host': host, 'port': port, 'lanAddresses': candidates,
            'recommendedBaseUrl': f'http://{host}:{port}', 'reachable': mode == 'lan-ready' and bool(candidates)}


@router.get('/network/share-info')
def network_info():
    return share_info()


def current_link(db, item_id):
    if not db.get(m.Item, item_id):
        raise HTTPException(404, '物品不存在')
    return db.scalar(select(m.ShareLink).where(m.ShareLink.itemId == item_id, m.ShareLink.revoked.is_(False)).order_by(m.ShareLink.createdAt.desc()))


def link_options(link):
    # Internal snapshot IDs are not client input; old links keep all new permissions off.
    return ShareOptions(**{k: v for k, v in (link.options or {}).items() if k in ShareOptions.model_fields})


def manual_documents(db, item_id):
    return list(db.scalars(select(m.Document).where(m.Document.itemId == item_id,
        m.Document.type == 'manual', m.Document.mimeType == 'application/pdf').order_by(m.Document.uploadedAt, m.Document.id)))


def manual_allowed(link, options, document):
    return options.showManualFiles and (document.id in options.manualDocumentIds or
        options.shareFutureManuals and document.id not in (link.options or {}).get('manualBaselineIds', []))


@router.post('/items/{item_id}/share')
def create_share(item_id: str, payload: ShareInput | None = None, regenerate: bool = False, address: str | None = None, db: Session = Depends(get_db)):
    info = share_info()
    if not info['reachable']:
        raise HTTPException(409, '局域网分享尚未就绪，请连接同一 Wi-Fi 并重新检测网络；普通启动支持只读分享。')
    if address:
        if address not in info['lanAddresses']:raise HTTPException(422,'不是当前有效的局域网地址')
        info['recommendedBaseUrl'] = f'http://{address}:{info["port"]}'
    link = current_link(db, item_id)
    settings = payload or ShareInput()
    documents = manual_documents(db, item_id)
    selected = set(settings.options.manualDocumentIds)
    if not selected.issubset({d.id for d in documents}):
        raise HTTPException(422, '只能授权当前物品的说明书')
    if (settings.options.shareFutureManuals or settings.options.showManualDownloads) and not settings.options.showManualFiles:
        raise HTTPException(422, '请先明确允许共享说明书 PDF')
    if link and (regenerate or expired(link)):
        link.revoked = True
        link.updatedAt = timestamp()
        link = None
    if not link:
        days = {'24h': 1, '7d': 7, '30d': 30}.get(settings.lifetime)
        link = m.ShareLink(itemId=item_id, token=secrets.token_urlsafe(32),
                           expiresAt=(datetime.now(timezone.utc)+timedelta(days=days)).isoformat() if days else None,
                           options={**settings.options.model_dump(), 'manualBaselineIds': [d.id for d in documents]})
        db.add(link)
        db.flush()
    elif payload is not None:
        # Explicit settings changes require rotation; never silently extend an old link.
        raise HTTPException(409, '已有分享，请重新生成以应用有效期与隐私设置')
    return {'id': link.id, 'token': link.token, 'expiresAt': link.expiresAt,
            'options': link_options(link).model_dump(),
            'url': info['recommendedBaseUrl'] + '/share/' + link.token, 'network': info}


@router.delete('/items/{item_id}/share')
def revoke_share(item_id: str, db: Session = Depends(get_db)):
    link = current_link(db, item_id)
    if link:
        link.revoked = True
        link.updatedAt = timestamp()
    return {'revoked': True}


def valid_link(db, token):
    link = db.scalar(select(m.ShareLink).where(m.ShareLink.token == token, m.ShareLink.revoked.is_(False)))
    if not link or expired(link) or not db.get(m.Item, link.itemId):
        raise HTTPException(404, '分享已过期或已撤销')
    link.lastUsedAt = timestamp()
    return link


def shared_images(db, item, token):
    products = list(db.scalars(select(m.ItemImage).where(m.ItemImage.itemId == item.id,
        m.ItemImage.type == 'product').order_by(m.ItemImage.createdAt, m.ItemImage.id)))
    cover = item.coverImage or ''
    chosen = next((p for p in products if cover in (p.filePath, f'/api/images/{p.id}',
        '/uploads/' + p.filePath.removeprefix('uploads/'))), None)
    images = []
    if chosen:
        products.remove(chosen)
        products.insert(0, chosen)
    elif cover.startswith('/assets/') and cover != '/assets/no-photo.svg':
        images.append({'src': LEGACY_ASSETS.get(cover, cover)})
    for p in products:
        if p.filePath.startswith('/assets/'):
            src = LEGACY_ASSETS.get(p.filePath, p.filePath)
        else:
            src = f'/api/share-data/{token}/images/{p.id}'
        if src not in [i['src'] for i in images]: images.append({'src': src})
    if not images and item.isDemo and item.id in ITEM_ASSETS:
        images.append({'src': ITEM_ASSETS[item.id]['src']})
    return images


@router.get('/share-data/{token}')
def public_item(token: str, db: Session = Depends(get_db)):
    link = valid_link(db, token)
    item = db.get(m.Item, link.itemId)
    sync_item(db, item)
    full = item_data(db, item)
    options = link_options(link)
    allowed = ['name', 'brand', 'model', 'category', 'status', 'nextMaintenance']
    for flag, fields in [(options.showPurchaseDate, ['purchaseDate']),
                         (options.showWarranty, ['warrantyEndDate', 'warrantyDaysLeft', 'warrantyMonths']),
                         (options.showPurchasePrice, ['purchasePrice']),
                         (options.showPurchaseChannel, ['purchaseChannel']), (options.showLocation, ['location'])]:
        if flag: allowed += fields
    info = {key: full[key] for key in allowed}
    images = shared_images(db, item, token)
    info['coverImage'] = images[0]['src'] if images else '/assets/no-photo.svg'
    titles = {'purchase': '购买建档', 'use': '开始使用', 'return': '退换期结束', 'warranty': '保修期结束',
              'maintenance': '维护', 'repair': '报修', 'repair_completed': '维修完成', 'retired': '淘汰'}
    events = [{'type': e.type, 'date': e.date, 'title': titles.get(e.type, '生命周期事件')}
              for e in db.scalars(select(m.LifecycleEvent).where(m.LifecycleEvent.itemId == item.id).order_by(m.LifecycleEvent.date))
              if e.date <= today().isoformat() and (e.type not in ('purchase', 'use', 'return') or options.showPurchaseDate)
              and (e.type != 'warranty' or options.showWarranty)] if options.showLifecycle else []
    current = 'retired' if item.status in ('淘汰', '转卖', '回收') else 'repair' if item.status == '维修中' else 'maintenance' if item.status == '待维护' else 'use'
    stages = []
    if options.showLifecycle:
        for kind, label in STAGES:
            recorded = [e for e in events if e['type'] == kind or kind == 'repair' and e['type'] == 'repair_completed']
            stages.append({'type': kind, 'label': label, 'date': recorded[-1]['date'] if recorded else None,
                           'state': 'current' if kind == current else 'completed' if recorded else 'pending', 'events': recorded})
    consumables = []
    if options.showConsumables:
        for c in db.scalars(select(m.Consumable).where(m.Consumable.itemId == item.id)):
            full_c = consumable_data(db, c)
            safe = {key: full_c[key] for key in ('name', 'status', 'estimatedDaysLeft', 'suggestedPurchaseDate', 'dataQuality', 'qualityExplanation')}
            safe['relatedItemName'] = item.name
            if options.showConsumableStock: safe.update(currentStock=c.currentStock, unit=c.unit)
            consumables.append(safe)
    maintenance, repairs, reminders = [], [], []
    if options.showMaintenance:
        latest_types = set()
        for r in db.scalars(select(m.MaintenanceRecord).where(m.MaintenanceRecord.itemId == item.id).order_by(m.MaintenanceRecord.date.desc(), m.MaintenanceRecord.id.desc())):
            safe = {key: getattr(r, key) for key in ('date', 'type', 'nextDueDate')}
            # Same latest-per-type rule as sync_item: superseded plans aren't current tasks.
            safe['needsMaintenance'] = r.type not in latest_types and bool(r.nextDueDate and r.nextDueDate <= today().isoformat())
            latest_types.add(r.type)
            if options.showRecordDetails: safe.update(description=r.description, cost=r.cost / 100)
            maintenance.append(safe)
    if options.showRepairs:
        for r in db.scalars(select(m.RepairRecord).where(m.RepairRecord.itemId == item.id).order_by(m.RepairRecord.reportDate.desc())):
            safe = {key: getattr(r, key) for key in ('reportDate', 'status', 'completionDate')}
            if options.showRecordDetails: safe.update(issue=r.issue, description=r.description, cost=r.cost / 100)
            repairs.append(safe)
    for r in db.scalars(select(m.Reminder).where(m.Reminder.itemId == item.id, m.Reminder.status == 'pending').order_by(m.Reminder.dueDate)):
        if (r.type == '保修到期' and options.showWarranty) or (r.type == '维护任务' and options.showMaintenance):
            reminders.append({'type': r.type, 'dueDate': r.dueDate})
    manuals = []
    for d in manual_documents(db, item.id):
        readable = manual_allowed(link, options, d)
        if not options.showManualNames and not readable: continue
        safe = {'name': d.originalFilename or d.filename, 'readable': readable}
        if readable:
            url = f'/api/share-data/{token}/manuals/{d.id}/file'
            safe.update(pageCount=d.pageCount, fileSize=d.fileSize, uploadedAt=d.uploadedAt, viewUrl=url,
                        downloadUrl=url + '?download=true' if options.showManualDownloads else None)
        manuals.append(safe)
    return {'item': info, 'images': images, 'events': events, 'lifecycle': stages,
            'maintenance': maintenance, 'repairs': repairs, 'reminders': reminders,
            'consumables': consumables, 'manuals': manuals,
            'options': options.model_dump(exclude={'manualDocumentIds'}), 'expiresAt': link.expiresAt}


@router.get('/share-data/{token}/images/{image_id}')
def public_image(token: str, image_id: str, db: Session = Depends(get_db)):
    link = valid_link(db, token)
    image = db.get(m.ItemImage, image_id)
    if not image or image.itemId != link.itemId or image.type != 'product' or image.filePath.startswith('/assets/'):
        raise HTTPException(404, '图片不可分享')
    try:
        path = local_path(image.filePath)
    except HTTPException:
        raise HTTPException(404, '图片不可分享')
    if not path.is_file():
        raise HTTPException(404, '图片不存在')
    return FileResponse(path, media_type=image.mimeType, headers={'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'})


@router.get('/share-data/{token}/manuals/{document_id}/file')
def public_manual(token: str, document_id: str, download: bool = False, db: Session = Depends(get_db)):
    link = valid_link(db, token)
    options = link_options(link)
    document = db.get(m.Document, document_id)
    if not document or document.itemId != link.itemId or document.type != 'manual' or document.mimeType != 'application/pdf' or not manual_allowed(link, options, document):
        raise HTTPException(404, '说明书未授权或已移除')
    if download and not options.showManualDownloads:
        raise HTTPException(404, '说明书未授权或已移除')
    try:
        path = local_path(document.filePath)
    except HTTPException:
        raise HTTPException(404, '说明书未授权或已移除')
    # Compatible with existing legacy uploads, never expose arbitrary files in data/.
    allowed_roots = [database.DATA / 'documents/manuals' / link.itemId, database.DATA / 'uploads']
    if not any(path.is_relative_to(p.resolve()) for p in allowed_roots) or not path.is_file() or path.suffix.lower() != '.pdf':
        raise HTTPException(404, '说明书未授权或已移除')
    with path.open('rb') as stream:
        if not stream.read(5).startswith(b'%PDF-'):
            raise HTTPException(404, '说明书未授权或已移除')
    filename = document.originalFilename or document.filename or 'manual.pdf'
    filename = filename.replace('\\', '/').split('/')[-1].replace('\r', '').replace('\n', '')
    disposition = 'attachment' if download else 'inline'
    return FileResponse(path, media_type='application/pdf', headers={
        'Content-Disposition': f"{disposition}; filename*=UTF-8''{quote(filename, safe='')}",
        'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer'})


def install_hosting(app):
    app.add_middleware(RuntimeTransactionGate)
    @app.middleware('http')
    async def local_admin(request: Request, call_next):
        # Production uses /api; Vite's proxy continues stripping this prefix.
        path = request.scope['path']
        if path.startswith('/api/'):
            request.scope['wusheng_api'] = True
            request.scope['path'] = path[4:]
            path = path[4:]
        remote = request.client.host if request.client else ''
        loopback = remote in ('127.0.0.1', '::1', 'testclient')
        public = request.method == 'GET' and (path.startswith(('/share-data/', '/share/', '/assets/')) or path in ('/', '/manifest.webmanifest', '/sw.js'))
        if not loopback and not public:
            return JSONResponse({'detail': '局域网仅开放令牌保护的只读档案；管理功能限本机访问'}, status_code=403)
        origin = request.headers.get('origin')
        if request.method not in ('GET', 'HEAD', 'OPTIONS') and origin and urlsplit(origin).hostname not in ('localhost', '127.0.0.1', '::1'):
            return JSONResponse({'detail': '写入仅允许本机页面'}, status_code=403)
        if request.method == 'GET' and not request.scope.get('wusheng_api') and 'text/html' in request.headers.get('accept','') and (path == '/' or path.startswith(('/items', '/share/', '/reminders', '/consumables', '/repairs', '/assistant', '/statistics'))):
            index = Path(os.getenv('WUSHENG_FRONTEND_DIST', str(ROOT / 'frontend/dist'))) / 'index.html'
            if index.is_file():
                if path.startswith('/share/'):
                    html = re.sub(r'<title>.*?</title>', '<title>物生 · 只读物品档案</title>', index.read_text(encoding='utf-8'), flags=re.S)
                    return HTMLResponse(html, headers={'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer', 'X-Content-Type-Options': 'nosniff'})
                return FileResponse(index)
        response = await call_next(request)
        if path.startswith('/share-data/'):
            response.headers['Cache-Control'] = 'no-store'
            response.headers['Referrer-Policy'] = 'no-referrer'
            response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.get('/{path:path}', include_in_schema=False)
    def spa(path: str, request: Request):
        if request.scope.get('wusheng_api'):
            raise HTTPException(404)
        dist = Path(os.getenv('WUSHENG_FRONTEND_DIST', str(ROOT / 'frontend/dist'))).resolve()
        target = (dist / path).resolve()
        if not target.is_relative_to(dist):
            raise HTTPException(404)
        if target.is_file():
            return FileResponse(target)
        if path.startswith(('api/', 'share-data/', 'assets/')) or '.' in Path(path).name:
            raise HTTPException(404)
        if not (dist / 'index.html').is_file():
            raise HTTPException(404, '前端尚未构建，请运行 npm run build')
        if path.startswith('share/'):
            html = re.sub(r'<title>.*?</title>', '<title>物生 · 只读物品档案</title>', (dist / 'index.html').read_text(encoding='utf-8'), flags=re.S)
            return HTMLResponse(html, headers={'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer', 'X-Content-Type-Options': 'nosniff'})
        return FileResponse(dist / 'index.html')

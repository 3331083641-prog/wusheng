"""Opt-in LAN hosting. Remote clients get token-scoped read-only data only."""
import ipaddress
import os
import secrets
import socket
import subprocess
import json
import asyncio
from pathlib import Path
from urllib.parse import urlsplit
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from .database import get_db, ROOT, timestamp
from . import models as m
from .serializers import row, item_data
from .lifecycle import sync_item, consumable_data
from .storage import local_path

router = APIRouter()


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
    mode = 'lan' if os.getenv('WUSHENG_SHARE_MODE') == 'lan' else 'local'
    port = int(os.getenv('WUSHENG_PORT', '8000'))
    candidates = lan_addresses() if mode == 'lan' else []
    host = candidates[0] if candidates else '127.0.0.1'
    return {'mode': mode, 'host': host, 'port': port, 'lanAddresses': candidates,
            'recommendedBaseUrl': f'http://{host}:{port}', 'reachable': mode == 'lan' and bool(candidates)}


@router.get('/network/share-info')
def network_info():
    return share_info()


def current_link(db, item_id):
    if not db.get(m.Item, item_id):
        raise HTTPException(404, '物品不存在')
    return db.scalar(select(m.ShareLink).where(m.ShareLink.itemId == item_id, m.ShareLink.revoked.is_(False)).order_by(m.ShareLink.createdAt.desc()))


@router.post('/items/{item_id}/share')
def create_share(item_id: str, regenerate: bool = False, address: str | None = None, db: Session = Depends(get_db)):
    info = share_info()
    if not info['reachable']:
        raise HTTPException(409, '当前应用仅允许本机访问，手机扫码无法打开。请运行 scripts/start_lan.ps1')
    if address:
        if address not in info['lanAddresses']:raise HTTPException(422,'不是当前有效的局域网地址')
        info['recommendedBaseUrl'] = f'http://{address}:{info["port"]}'
    link = current_link(db, item_id)
    if link and regenerate:
        link.revoked = True
        link.updatedAt = timestamp()
        link = None
    if not link:
        link = m.ShareLink(itemId=item_id, token=secrets.token_urlsafe(32))
        db.add(link)
        db.flush()
    return {'id': link.id, 'token': link.token, 'url': info['recommendedBaseUrl'] + '/share/' + link.token, 'network': info}


@router.delete('/items/{item_id}/share')
def revoke_share(item_id: str, db: Session = Depends(get_db)):
    link = current_link(db, item_id)
    if link:
        link.revoked = True
        link.updatedAt = timestamp()
    return {'revoked': True}


def valid_link(db, token):
    link = db.scalar(select(m.ShareLink).where(m.ShareLink.token == token, m.ShareLink.revoked.is_(False)))
    if not link or not db.get(m.Item, link.itemId):
        raise HTTPException(404, '分享已失效或已撤销')
    link.lastUsedAt = timestamp()
    return link


@router.get('/share-data/{token}')
def public_item(token: str, db: Session = Depends(get_db)):
    link = valid_link(db, token)
    item = db.get(m.Item, link.itemId)
    sync_item(db, item)
    full = item_data(db, item)
    allowed = ['name', 'brand', 'model', 'purchaseDate', 'warrantyEndDate', 'status', 'nextMaintenance']
    info = {key: full[key] for key in allowed}
    if item.serialNumber:
        info['serialNumber'] = '****' + item.serialNumber[-4:]
    cover = item.coverImage
    if cover.startswith('/assets/'):
        info['coverImage'] = cover
    else:
        image = db.scalar(select(m.ItemImage).where(m.ItemImage.itemId == item.id, m.ItemImage.type == 'product'))
        info['coverImage'] = f'/api/share-data/{token}/images/{image.id}' if image else '/assets/no-photo.svg'
    events = [{'type': e.type, 'date': e.date, 'title': e.title} for e in db.scalars(select(m.LifecycleEvent).where(m.LifecycleEvent.itemId == item.id).order_by(m.LifecycleEvent.date))]
    consumables = [{'name': c.name, 'status': consumable_data(db, c)['status']} for c in db.scalars(select(m.Consumable).where(m.Consumable.itemId == item.id))]
    manuals = [{'name': d.originalFilename or d.filename} for d in db.scalars(select(m.Document).where(m.Document.itemId == item.id))]
    return {'item': info, 'events': events, 'consumables': consumables, 'manuals': manuals}


@router.get('/share-data/{token}/images/{image_id}')
def public_image(token: str, image_id: str, db: Session = Depends(get_db)):
    link = valid_link(db, token)
    image = db.get(m.ItemImage, image_id)
    if not image or image.itemId != link.itemId or image.type != 'product' or image.filePath.startswith('/assets/'):
        raise HTTPException(404, '图片不可分享')
    path = local_path(image.filePath)
    if not path.is_file():
        raise HTTPException(404, '图片不存在')
    return FileResponse(path, media_type=image.mimeType, headers={'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'})


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
                return FileResponse(index)
        response = await call_next(request)
        if path.startswith('/share-data/'):
            response.headers['Cache-Control'] = 'no-store'
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
        return FileResponse(dist / 'index.html')

"""Local attachment storage. Originals are preserved; paths never come from clients."""
from contextlib import contextmanager
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import warnings
from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader
from . import database
from .database import uid

IMAGE_LIMIT = 10 * 1024 * 1024
PDF_LIMIT = 50 * 1024 * 1024
IMAGE_TYPES = {'product', 'receipt', 'label', 'manual_image', 'invoice', 'package', 'warranty_card', 'other'}


def original_name(name, fallback):
    return (name or fallback).replace('\\', '/').split('/')[-1][:250] or fallback


def validate_image(file):
    contents = file.file.read(IMAGE_LIMIT + 1)
    if len(contents) > IMAGE_LIMIT:
        raise HTTPException(413, '单张图片不超过 10MB')
    formats = {'JPEG': ('.jpg', 'image/jpeg'), 'PNG': ('.png', 'image/png'), 'WEBP': ('.webp', 'image/webp')}
    name = original_name(file.filename, 'image')
    if Path(name).suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp'} or file.content_type not in {v[1] for v in formats.values()}:
        raise HTTPException(415, '仅支持 JPG、JPEG、PNG、WebP 图片')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(contents)) as image:
                if image.format not in formats or image.width * image.height > 20_000_000:
                    raise ValueError()
                extension, mime = formats[image.format]
                if mime != file.content_type or (Path(name).suffix.lower() not in ({'.jpg', '.jpeg'} if mime == 'image/jpeg' else {extension})):
                    raise ValueError()
                image.load()
    except (UnidentifiedImageError, ValueError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(415, '图片内容无效或超过 2000 万像素')
    return contents, {'originalFilename': name, 'storedFilename': uid() + extension, 'mimeType': mime, 'fileSize': len(contents), 'sha256': sha256(contents).hexdigest()}


def validate_pdf(file):
    contents = file.file.read(PDF_LIMIT + 1)
    if len(contents) > PDF_LIMIT:
        raise HTTPException(413, 'PDF 不超过 50MB')
    name = original_name(file.filename, '说明书.pdf')
    if file.content_type != 'application/pdf' or Path(name).suffix.lower() != '.pdf' or not contents.startswith(b'%PDF-'):
        raise HTTPException(415, '请上传 .pdf 格式的有效 PDF 文件')
    try:
        reader = PdfReader(BytesIO(contents))
        # Some public manufacturer PDFs restrict editing but permit reading with
        # an empty user password. Preserve their original encrypted bytes.
        if reader.is_encrypted and not reader.decrypt(''):
            raise ValueError('encrypted')
        count = len(reader.pages)
        if count == 0:
            raise ValueError('empty')
    except Exception:
        raise HTTPException(422, '无法读取 PDF，请选择有效且未加密的文件')
    # Scanned pages or text extraction errors must not prevent archival.
    text_parts = []
    for number, page in enumerate(reader.pages, 1):
        try:
            content = page.extract_text() or ''
        except Exception:
            content = ''
        if content.strip():
            text_parts.append(f'[第 {number} 页]\n{content}')
        if sum(map(len, text_parts)) >= 500_000:
            break
    text = '\n'.join(text_parts)[:500_000]
    return contents, {'originalFilename': name, 'storedFilename': uid() + '.pdf', 'mimeType': 'application/pdf', 'fileSize': len(contents), 'sha256': sha256(contents).hexdigest(), 'pageCount': count, 'extractedText': text, 'textStatus': 'text_ready' if text.strip() else 'needs_ocr', 'textSource': 'pdf_text' if text.strip() else 'none'}


def local_path(relative):
    """Accept database-owned data paths only, with compatibility for legacy uploads."""
    if relative.startswith('/uploads/'):
        relative = 'uploads/' + relative.removeprefix('/uploads/')
    root = database.DATA.resolve()
    target = (root / relative).resolve()
    if not target.is_relative_to(root) or target == root:
        raise HTTPException(400, '附件路径无效')
    return target


class FileTransaction:
    def __init__(self):
        self.undo = []
        self.trash = []

    def write(self, relative, contents):
        path = local_path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        # UUID filename plus exclusive creation prevents overwrite.
        with path.open('xb') as stream:
            self.undo.append(lambda: path.unlink(missing_ok=True))
            stream.write(contents)

    def move(self, source, destination):
        src, dst = local_path(source), local_path(destination)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            raise HTTPException(409, '附件目标已存在')
        src.rename(dst)
        self.undo.append(lambda: dst.rename(src))

    def remove(self, relative):
        path = local_path(relative)
        if not path.is_file():
            return
        trash = path.with_name('.deleted-' + uid())
        path.rename(trash)
        self.undo.append(lambda: trash.rename(path))
        self.trash.append(trash)


@contextmanager
def file_transaction(db):
    transaction = FileTransaction()
    try:
        yield transaction
        db.flush()
        db.commit()
    except Exception:
        db.rollback()
        for undo in reversed(transaction.undo):
            undo()
        raise
    else:
        for path in transaction.trash:
            path.unlink(missing_ok=True)


def prune_empty(relative):
    path = local_path(relative)
    if path.is_dir() and not any(path.iterdir()):
        path.rmdir()

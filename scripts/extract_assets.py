"""Extract only photographic product regions from user-provided UI references.
No page screenshot is used as a CSS background or interactive surface.
"""
from pathlib import Path
import argparse
import json
import os
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description='Extract product photos from user-provided UI reference images.')
parser.add_argument('--source-dir', type=Path, required=True, help='Directory containing the original UI reference PNG files.')
args = parser.parse_args()
source = args.source_dir.expanduser().resolve()
if not source.is_dir():
    parser.error(f'Image source directory does not exist: {source}')
assets = root / 'frontend/public/assets'
assets.mkdir(parents=True, exist_ok=True)
refs = ['16_43_44-1','16_44_12-9','16_44_08-8','16_44_06-7','16_44_03-6','16_43_58-5','16_43_55-4','16_43_52-3','16_43_47-2']
manifest = []
for ref in refs:
    path = source / f'ChatGPT 图像 2026年10月1日 {ref}.png'
    im = Image.open(path)
    manifest.append({'source': path.name, 'size': im.size, 'role': 'user-provided UI reference'})
grid = Image.open(source / 'ChatGPT 图像 2026年10月1日 16_43_47-2.png')
boxes = {'laptop':(286,454,607,560),'headphones':(628,454,946,560),'washer':(970,454,1286,560),'ac':(1307,454,1625,560),'robot':(286,741,608,834),'coffee':(629,741,946,834),'toothbrush':(969,741,1285,834),'suitcase':(1308,741,1627,834)}
home = Image.open(source / 'ChatGPT 图像 2026年10月1日 16_43_44-1.png')
# Only an unobstructed photographic strip; no UI, text or buttons.
home.crop((237,0,1020,101)).save(assets/'hero-plants.jpg', quality=94)
detail = Image.open(source / 'ChatGPT 图像 2026年10月1日 16_43_55-4.png')
detail.crop((366,131,735,455)).save(assets/'headphones-detail.jpg', quality=94)
cons = Image.open(source / 'ChatGPT 图像 2026年10月1日 16_44_03-6.png')
for name, box in {'brushhead':(279,364,361,475),'filter':(601,364,682,476),'capsules':(921,364,999,475),'ink':(279,548,361,660),'detergent':(601,548,682,660),'purifier':(601,730,682,841)}.items():
    cons.crop(box).save(assets/f'{name}.jpg', quality=94)
for name, box in boxes.items():
    grid.crop(box).save(assets/f'{name}.jpg', quality=94)
font_candidates = [
    Path(os.environ['WUSHENG_CJK_FONT']) if os.environ.get('WUSHENG_CJK_FONT') else None,
    Path(os.environ.get('WINDIR', os.environ.get('SYSTEMROOT', ''))) / 'Fonts' / 'msyh.ttc',
    Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'),
    Path('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc'),
]
font_path = next((candidate for candidate in font_candidates if candidate and candidate.is_file()), None)
font = ImageFont.truetype(str(font_path), 30) if font_path else ImageFont.load_default()
receipt = Image.new('RGB',(760,860),'#fffdf6')
draw=ImageDraw.Draw(receipt)
lines=['物生演示购买凭证','DEMO RECEIPT - NOT A REAL INVOICE','','商家：京东自营','商品：Sony 无线降噪耳机','型号：WH-1000XM6','购买日期：2026-10-01','实付金额：2999.00 元','序列号：WS-DEMO-SONY-001','保修：12个月','','仅用于本地 OCR 功能演示']
for i,line in enumerate(lines): draw.text((45,45+i*62),line,fill='#17202a',font=font)
receipt.save(root/'docs/references/demo-receipt.png')
(root/'docs/references/asset_sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('Read 9 references; extracted product photographs and generated labeled OCR fixture.')

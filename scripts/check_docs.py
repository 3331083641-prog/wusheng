"""Check local Markdown links/images, including reference-style links. Offline."""
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parents[1]


def check(root=ROOT):
    documents=[p for p in root.glob('*.md') if p.is_file()]+list((root/'docs').rglob('*.md'))
    broken=[];checked=0
    for doc in documents:
        text=re.sub(r'```.*?```','',doc.read_text(encoding='utf-8-sig'),flags=re.S)
        links=re.findall(r'!?\[[^\]]*\]\(\s*(<[^>]+>|[^\s)]+)',text)
        links+=re.findall(r'^\s*\[[^\]]+\]:\s*(<[^>]+>|\S+)',text,re.M)
        for link in links:
            link=link.strip('<>');parsed=urlsplit(link)
            if parsed.scheme or link.startswith(('#','//')):continue
            path=unquote(parsed.path)
            if not path:continue
            checked+=1
            target=(root/path.lstrip('/') if path.startswith('/') else doc.parent/path).resolve()
            if not target.is_relative_to(root.resolve()) or not target.exists():
                broken.append(f'{doc.relative_to(root).as_posix()}: {link}')
    return {'documents':len(documents),'checkedLinks':checked,'brokenLinks':broken}


if __name__=='__main__':
    import json
    report=check();print(json.dumps(report,ensure_ascii=False,indent=2))
    sys.exit(bool(report['brokenLinks']))

"""Publish compact synthetic UI evidence without machine paths or uploaded data."""
import json
import sys
from pathlib import Path
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1]
report=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
tests=[]


def visit(suite):
    for spec in suite.get('specs',[]):
        for test in spec.get('tests',[]):
            tests.append({'title':spec['title'],'status':test['status'],
                          'attempts':[{'status':r['status'],'durationMs':r['duration']} for r in test.get('results',[])]})
    for child in suite.get('suites',[]):visit(child)


for suite in report['suites']:visit(suite)
output={'checkedAt':datetime.now(timezone.utc).isoformat(),'data':'isolated synthetic SQLite and generated fixtures',
        'browser':'Microsoft Edge (Playwright)','stats':report['stats'],'tests':tests,
        'limitations':'Native filechooser events and LAN HTTP/QR decode verified; no physical phone test.'}
(root/'docs/competition/release-ui-results.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Published',len(tests),'synthetic UI results without machine paths')

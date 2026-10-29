#!/usr/bin/env python3
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parent.parent
app = root / 'job-search/applications' / sys.argv[1]
result = json.loads((app / 'confirmation.json').read_text())
assert result['status'] == 'submitted'
tracker = root / 'job-search/applications.md'
rows = tracker.read_text().splitlines()
for i, row in enumerate(rows):
    if row.startswith('| ' + sys.argv[1] + ' |'):
        cells = row.split('|')
        cells[5] = ' submitted '
        cells[6] = ' ' + result['submitted_on'] + ' '
        cells[9] = ' Success page confirmed. [Confirmation](applications/' + sys.argv[1] + '/confirmation.json). '
        rows[i] = '|'.join(cells)
tracker.write_text('\n'.join(rows) + '\n')
p = app / 'verification.json'
if p.exists():
    v = json.loads(p.read_text())
    v.update(submitted=True, confirmation='confirmation.json')
    p.write_text(json.dumps(v, indent=2) + '\n')
confirmed = [p for p in (root / 'job-search/applications').glob('*/confirmation.json') if json.loads(p.read_text()).get('status') == 'submitted' and json.loads(p.read_text()).get('round') == 'wttj-2026-10-08']
batch = root / 'job-search/wttj-batch-2026-10-08.md'
s = batch.read_text()
import re
eligible = [p for p in confirmed if json.loads(p.read_text()).get('in_scope', True)]
s = re.sub(r'Confirmed submissions: \d+', f'Confirmed submissions: {len(confirmed)}', s)
s = re.sub(r'Eligible toward target: \d+', f'Eligible toward target: {len(eligible)}', s)
batch.write_text(s)
print(f'WTTJ confirmed: {len(confirmed)}; eligible: {len(eligible)} / 500')

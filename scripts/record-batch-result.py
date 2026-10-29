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
        cells[6] = ' 2026-10-08 '
        cells[9] = ' Success page confirmed. [Confirmation](applications/' + sys.argv[1] + '/confirmation.json). '
        rows[i] = '|'.join(cells)
tracker.write_text('\n'.join(rows) + '\n')
p = app / 'verification.json'
if p.exists():
    v = json.loads(p.read_text())
    v.update(submitted=True, confirmation='confirmation.json')
    p.write_text(json.dumps(v, indent=2) + '\n')
confirmed = [p for p in (root / 'job-search/applications').glob('*/confirmation.json') if p.parent.name != '2026-10-08-voodoo-blitz-vie244518' and json.loads(p.read_text()).get('status') == 'submitted' and json.loads(p.read_text()).get('round', 'initial-batch') == 'initial-batch']
batch = root / 'job-search/batch-2026-10-08.md'
s = batch.read_text()
import re
s = re.sub(r'Additional confirmed submissions: \d+', f'Additional confirmed submissions: {len(confirmed)}', s)
batch.write_text(s)
print(f'Batch confirmed: {len(confirmed)}')

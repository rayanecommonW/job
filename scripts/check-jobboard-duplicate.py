#!/usr/bin/env python3
"""Check confirmed applications before submitting a job-board listing."""
import json
import re
import sys
import unicodedata
from pathlib import Path

root = Path(__file__).resolve().parent.parent
candidate = json.loads(Path(sys.argv[1]).read_text())
def norm(s):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', s or '').casefold())
matches = []
possible = []
def role_tokens(s):
    s = unicodedata.normalize('NFKD', s or '').casefold()
    s = re.sub(r'full[ -]?stack', 'fullstack', s)
    return set(re.findall(r'[a-z0-9]+', s)) - {'senior', 'staff', 'm', 'f', 'd', 'and', 'the'}

for row in (root / 'job-search/applications.md').read_text().splitlines():
    if not row.startswith('| 2026-'):
        continue
    cells = [x.strip() for x in row.strip('|').split('|')]
    if len(cells) < 5 or cells[4] != 'submitted':
        continue
    if cells[3] == candidate.get('url'):
        matches.append(cells[0])
    elif norm(cells[1]) == norm(candidate.get('company')):
        a, b = role_tokens(cells[2]), role_tokens(candidate.get('role'))
        if norm(cells[2]) == norm(candidate.get('role')) or a == b:
            matches.append(cells[0])
        elif min(len(a), len(b)) >= 3 and len(a & b) / max(1, len(a | b)) >= 0.7:
            possible.append(cells[0])
for p in (root / 'job-search/applications').glob('*/metadata.json'):
    c = p.parent / 'confirmation.json'
    if not c.exists() or json.loads(c.read_text()).get('status') != 'submitted':
        continue
    v = json.loads(p.read_text())
    if v.get('url') == candidate.get('url') or norm(v.get('company')) == norm(candidate.get('company')) and norm(v.get('role')) == norm(candidate.get('role')):
        matches.append(v.get('id', p.parent.name))
print(json.dumps({'duplicate': bool(matches), 'matching_ids': sorted(set(matches)), 'possible_matching_ids': sorted(set(possible))}))

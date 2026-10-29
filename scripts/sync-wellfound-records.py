#!/usr/bin/env python3
"""Mirror saved Wellfound queues and current campaign counts from receipts."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEARCH = ROOT / 'job-search'
state = json.loads((SEARCH / 'jobboards-state.json').read_text())
total = state['confirmed_applications_cumulative']
scope = state['confirmed_in_scope_cumulative']
apps = json.loads((SEARCH / 'applications.json').read_text())
submitted = {a['url']: a for a in apps if a['status'] == 'submitted'}
blocked = {}
for evidence in sorted((SEARCH / 'founding-preflight').glob('*.json')):
    record = json.loads(evidence.read_text())
    if isinstance(record, dict) and record.get('status') == 'blocked' and record.get('listing_url'):
        blocked[record['listing_url']] = (record, str(evidence.relative_to(ROOT)))
pairs = [
    ('jobboards-wellfound-worldwide-founding-2026-10-12-queue.json', 'wellfound-worldwide-founding-List.md'),
    ('jobboards-wellfound-software-worldwide-2026-10-12-queue.json', 'wellfound-software-List.md'),
    ('jobboards-wellfound-entry-worldwide-2026-10-12-queue.json', 'wellfound-entry-List.md'),
    ('jobboards-wellfound-new-founding-2026-10-12-queue.json', 'wellfound-new-founding-List.md'),
    ('jobboards-wellfound-broad-founding-2026-10-12-queue.json', 'wellfound-broad-founding-List.md'),
    ('jobboards-wellfound-cofounding-2026-10-12-queue.json', 'wellfound-cofounding-List.md'),
    ('jobboards-wellfound-junior-2026-10-12-queue.json', 'wellfound-junior-List.md'),
    ('jobboards-wellfound-europe-software-2026-10-12-queue.json', 'wellfound-europe-software-List.md'),
]
known = {queue for queue, _ in pairs}
for p in sorted(SEARCH.glob('*wellfound*queue.json')):
    if p.name not in known:
        label = p.name.removeprefix('jobboards-').removesuffix('-queue.json').removesuffix('-2026-10-12')
        pairs.append((p.name, label + '-List.md'))
for queue, mirror in pairs:
    p = SEARCH / queue
    rows = json.loads(p.read_text())
    for row in rows:
        row.setdefault('status', 'queued')
        url = row.get('href') or row.get('url')
        if url in submitted:
            row.update(status='submitted', application_id=submitted[url]['id'])
        elif re.search(r'\bjava\b', row.get('text') or row.get('role', ''), re.I):
            row.update(status='excluded', blocker='Java roles blacklisted by user 2026-10-13')
        elif url in blocked:
            record, evidence = blocked[url]
            row.update(status='blocked', blocker=record['reason'], blocker_evidence=evidence)
    p.write_text(json.dumps(rows, indent=2) + '\n')
    lines = ['# Wellfound saved queue', '', '| Company | Role | Status |', '| --- | --- | --- |']
    for row in rows:
        company = (row.get('company') or (row.get('card') or 'Unknown').split('\n')[0]).replace('|', '/')
        role = (row.get('text') or row.get('role', 'Unknown')).split('\n')[0].replace('|', '/')
        lines.append(f"| {company} | [{role}]({row.get('href') or row.get('url')}) | {row['status']} |")
    (SEARCH / mirror).write_text('\n'.join(lines) + '\n')
for name in ['START-HERE.md', 'AGENTS.md']:
    p = ROOT / name
    s = re.sub(r'\d+ confirmed applications,\s*\d+ in scope', f'{total} confirmed applications, {scope} in scope', p.read_text(), count=1)
    p.write_text(s)
p = ROOT / 'README.md'
s = re.sub(r'\*\*\d+ confirmed applications\*\*,\s*\d+ in scope', f'**{total} confirmed applications**, {scope} in scope', p.read_text(), count=1)
p.write_text(s)
p = SEARCH / 'README.md'
s = re.sub(r'current total is \d+ confirmed,\s*\d+ in scope', f'current total is {total} confirmed,\n{scope} in scope', p.read_text(), count=1)
p.write_text(s)
print(f'{total} confirmed, {scope} in scope; queues mirrored')

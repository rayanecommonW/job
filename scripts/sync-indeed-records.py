#!/usr/bin/env python3
"""Mirror saved Indeed URLs and outcomes without keeping browser tabs open."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEARCH = ROOT / 'job-search'
apps = json.loads((SEARCH / 'applications.json').read_text())
submitted = {app['url']: app for app in apps if app['status'] == 'submitted'}

for queue in sorted(SEARCH.glob('jobboards-indeed-*queue.json')):
    rows = json.loads(queue.read_text())
    for row in rows:
        row.setdefault('status', 'queued')
        if row['href'] in submitted:
            row.update(status='submitted', application_id=submitted[row['href']]['id'])
        elif row.get('id'):
            evidence = SEARCH / 'founding-preflight' / f"indeed-{row['id']}-blocker-2026-10-12.json"
            if evidence.exists():
                record = json.loads(evidence.read_text())
                row.update(status='blocked', blocker=record['reason'], blocker_evidence=str(evidence.relative_to(ROOT)))
    queue.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    lines = ['# Indeed saved queue', '', '| Company | Role | Status |', '| --- | --- | --- |']
    for row in rows:
        company = (row.get('company') or 'See saved card').replace('|', '/')
        role = (row.get('role') or row['text'].split('\n')[0]).replace('|', '/')
        lines.append(f"| {company} | [{role}]({row['href']}) | {row['status']} |")
    queue.with_name(queue.stem.removeprefix('jobboards-').removesuffix('-queue') + '-List.md').write_text('\n'.join(lines) + '\n')
print('Indeed queues and outcomes mirrored')

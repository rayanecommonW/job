#!/usr/bin/env python3
"""Archive a board's structured profile application without claiming a PDF upload."""
import json
from datetime import date
from pathlib import Path
import sys

root = Path(__file__).resolve().parent.parent
meta = json.loads(Path(sys.argv[1]).read_text())
app = root / 'job-search/applications' / meta['id']
app.mkdir(parents=True, exist_ok=True)
(app / 'metadata.json').write_text(json.dumps(meta, indent=2) + '\n')
(app / 'job.md').write_text(f"# {meta['company']}, {meta['role']}\n\nCaptured {date.today().isoformat()}. {meta['url']}\n\n{meta['posting']}\n")
(app / 'submitted-profile.txt').write_text(meta['profile_text'] + '\n')
(app / 'answers.json').write_text(json.dumps(meta.get('answers', {}), indent=2) + '\n')
(app / 'verification.json').write_text(json.dumps({'submitted': False, 'document_used': 'Structured board profile and application answers', 'pdf_uploaded': False, 'education_dates_absent': True}, indent=2) + '\n')
(app / 'review.md').write_text('Structured profile checked before submission. Employment dates and titles preserved. Education retained without dates in a qualification snippet. No PDF is uploaded in this flow.\n')
tracker = root / 'job-search/applications.md'
s = tracker.read_text()
if meta['id'] not in s:
    i = s.index('\nUse `found`')
    row = f"| {meta['id']} | {meta['company']} | {meta['role']} | {meta['url']} | in progress | | [Profile](applications/{meta['id']}/submitted-profile.txt) | | {meta['channel']} structured profile; confirmation pending. |\n"
    tracker.write_text(s[:i] + row + s[i:])
print(json.dumps({'id': meta['id'], 'profile_archived': True, 'pdf_uploaded': False}))

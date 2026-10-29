#!/usr/bin/env python3
"""Record a confirmed application and update the cumulative campaign count."""
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parent.parent
app_id = sys.argv[1]
app = root / 'job-search/applications' / app_id
result = json.loads((app / 'confirmation.json').read_text())
assert result['status'] == 'submitted'
tracker = root / 'job-search/applications.md'
rows = tracker.read_text().splitlines()
for i, row in enumerate(rows):
    if row.startswith('| ' + app_id + ' |'):
        cells = row.split('|')
        cells[5] = ' submitted '
        cells[6] = ' ' + result['submitted_on'] + ' '
        cells[9] = f' Success page confirmed. [Confirmation](applications/{app_id}/confirmation.json). '
        rows[i] = '|'.join(cells)
tracker.write_text('\n'.join(rows) + '\n')
applications = []
for row in rows:
    if row.startswith('| 2026-'):
        cells = [x.strip() for x in row.strip('|').split('|')]
        if len(cells) >= 9:
            applications.append(dict(zip(['id', 'company', 'role', 'url', 'status', 'submitted_on', 'cv', 'follow_up', 'notes'], cells)))
(root / 'job-search/applications.json').write_text(json.dumps(applications, indent=2) + '\n')
p = app / 'verification.json'
if p.exists():
    v = json.loads(p.read_text())
    v.update(submitted=True, confirmation='confirmation.json')
    p.write_text(json.dumps(v, indent=2) + '\n')
results = [json.loads(p.read_text()) for p in (root / 'job-search/applications').glob('*/confirmation.json')]
new = [v for v in results if v.get('status') == 'submitted' and v.get('round') == 'jobboards-2026-10-09']
p = root / 'job-search/jobboards-state.json'
state = json.loads(p.read_text())
target = state.get('target_confirmed_applications', 1000)
state.update(status='in progress', new_jobboard_confirmed=len(new), confirmed_applications_cumulative=319+len(new), confirmed_in_scope_cumulative=315+sum(v.get('in_scope', True) for v in new), remaining_to_total_target=max(0,target-319-len(new)))
state['remaining_to_active_milestone'] = max(0, state.get('active_milestone', 1000) - state['confirmed_applications_cumulative'])
state['remaining_to_active_target'] = max(0, state.get('active_continuation_target', target) - state['confirmed_applications_cumulative'])
p.write_text(json.dumps(state, indent=2) + '\n')
print(f"Job-board round: {len(new)} confirmed; cumulative: {state['confirmed_applications_cumulative']} / {target}")

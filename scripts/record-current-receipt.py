#!/usr/bin/env python3
"""Record an archived site receipt without replacing interview statuses."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def read(path):
    return json.loads(path.read_text())
def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

app_id = sys.argv[1]
submission_tab = sys.argv[2] if len(sys.argv) > 2 else 'tab_cn'
assert submission_tab.startswith('tab_') and submission_tab.replace('_', '').isalnum()
app = ROOT / 'job-search/applications' / app_id
receipt = read(app / 'confirmation.json')
assert receipt['status'] == 'submitted' and receipt.get('text')
tracker = ROOT / 'job-search/applications.json'
rows = read(tracker)
row = next(r for r in rows if r['id'] == app_id)
state_path = ROOT / 'job-search/jobboards-state.json'
state = read(state_path)
already = row['status'] in {'submitted', 'interviewing', 'offer'}
if not already:
    assert sum(r['status'] in {'submitted', 'interviewing', 'offer'} for r in rows) == state['confirmed_applications_cumulative']
    row.update(status='submitted', submitted_on=receipt['submitted_on'], notes=f'Site receipt confirmed. [Confirmation](applications/{app_id}/confirmation.json).')
    state['confirmed_applications_cumulative'] += 1
    state['confirmed_in_scope_cumulative'] += int(receipt.get('in_scope', True))
    state['new_jobboard_confirmed'] += 1
    batch = state['active_geography_batch']
    assert receipt['country'] == batch['country'] or batch['country'] in {'Europe', 'International'}
    batch['confirmed_new'] += 1
    batch['remaining'] = max(0, batch['target_new_confirmed'] - batch['confirmed_new'])
    state.setdefault('country_receipts_recorded', []).append(app_id)
    if not batch['remaining'] and batch['country'] == 'Netherlands':
        batch.update(status='complete', ended_on=receipt['submitted_on'], actual_ending_confirmed_cumulative=state['confirmed_applications_cumulative'])
        state['completed_geography_batches'].append(batch.copy())
        total = state['confirmed_applications_cumulative']
        state['active_geography_batch'] = dict(country='Ireland', starting_confirmed_cumulative=total, target_new_confirmed=100, ending_confirmed_cumulative=total+100, confirmed_new=0, remaining=100, user_instruction_date='2026-10-14')
        state.update(current_country='Ireland', country_batch_start=total, country_batch_target=total+100)
    elif not batch['remaining'] and batch['country'] == 'Ireland':
        batch.update(status='complete', ended_on=receipt['submitted_on'], actual_ending_confirmed_cumulative=state['confirmed_applications_cumulative'])
        state['completed_geography_batches'].append(batch.copy())
        total = state['confirmed_applications_cumulative']
        remaining = max(0, state['target_confirmed_applications'] - total)
        state['active_geography_batch'] = dict(country='Europe', starting_confirmed_cumulative=total, target_new_confirmed=remaining, ending_confirmed_cumulative=total+remaining, confirmed_new=0, remaining=remaining, user_instruction_date='2026-10-15')
        state.update(current_country='Europe', country_batch_start=total, country_batch_target=total+remaining)
    for key in ['remaining_to_total_target', 'remaining_to_active_milestone', 'remaining_to_active_target']:
        state[key] = max(0, state['target_confirmed_applications'] - state['confirmed_applications_cumulative'])
    state.update(status='in progress', campaign_execution_status='active', last_updated=receipt['submitted_on'])
    pending = state['pending_submission_tabs'].get(submission_tab)
    if pending and pending.get('application_id') == app_id:
        state['pending_submission_tabs'].pop(submission_tab)
    state['browser_continuation_note'] = f'Active. {submission_tab} receipt archived; safe reuse. Other protected forms unchanged. Multiple tabs authorized; use practical batches.'
    active = state['active_geography_batch']
    state['last_pass'] = f"{state['confirmed_applications_cumulative']} confirmed; {active['country']} {active['confirmed_new']}/{active['target_new_confirmed']}. Latest receipt {app_id}."
    write(tracker, rows)
    write(state_path, state)
md = ROOT / 'job-search/applications.md'
lines = md.read_text().splitlines()
for i, line in enumerate(lines):
    if line.startswith('| ' + app_id + ' |'):
        lines[i] = '| ' + ' | '.join(str(row.get(k, '')).replace('|', '/') for k in ['id', 'company', 'role', 'url', 'status', 'submitted_on', 'cv', 'follow_up', 'notes']) + ' |'
        break
else:
    raise ValueError('Missing Markdown tracker row')
md.write_text('\n'.join(lines) + '\n')
vpath = app / 'verification.json'
v = read(vpath)
v.update(submitted=True, confirmation='confirmation.json')
write(vpath, v)
print(json.dumps(dict(total=state['confirmed_applications_cumulative'], in_scope=state['confirmed_in_scope_cumulative'], batch=state['active_geography_batch'], already_recorded=already)))

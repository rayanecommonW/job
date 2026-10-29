#!/usr/bin/env python3
"""Consolidate saved WTTJ listings and mirror their application status."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
SEARCH = ROOT / 'job-search'
QUEUE = SEARCH / 'wttj-volume-queue.json'
SOURCES = [
    'jobboards-wttj-germany-queue.json', 'wttj-berlin-queue.json',
    'wttj-dublin-queue.json', 'wttj-suisse-queue.json', 'wttj-us-queue.json',
    'wttj-canada-queue.json', 'wttj-external-queue.json',
    'wttj-stop-2026-10-09-external.json', 'wttj-ats-review-queue.json',
    'wttj-review-queue.json', 'wttj-paris-queue.json',
]


def read(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def norm(text):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', text or '').casefold())


def key(url):
    u = urlsplit(url)
    return u.netloc + re.sub(r'^/(fr|en)(?=/)', '', u.path).rstrip('/')


def role_priority(role):
    r = norm(role)
    if re.search(r'analytics|dataengineer|ingenieurdonnees', r):
        return 8
    if re.search(r'junior|earlycareer|graduate|entrylevel', r) or re.search(r'engineeri$', r):
        return 0
    if 'founding' in r:
        return 1
    if 'senior' in r:
        return 2
    if re.search(r'engineerii$', r):
        return 3
    if re.search(r'appliedai|aiengineer|machinelearning|llm|genai', r):
        return 4
    return 2


def scope(role, card):
    r = norm(role)
    if re.search(r'talentacquisition|recruit|commercial|accountmanager|businessdeveloper|electrical|mechanical|electronique|mecanique', r):
        return 'excluded', 'Outside the current software scope'
    if not re.search(r'software|fullstack|frontend|backend|developer|developpeur|developpement|founding|ingenieur|engineer|devops|sre', r):
        return 'needs review', 'Check that the role is software engineering'
    # Salary checking uses the listing card, not recommendation text in a posting.
    salary = re.search(r'(\d+(?:[.,]\d+)?)\s*K(?:\s*(?:à|to|[-–])\s*\d+(?:[.,]\d+)?\s*K)?\s*€', card)
    if salary and float(salary[1].replace(',', '.')) < 45:
        return 'excluded', 'Advertised salary starts below EUR45,000'
    return 'found', ''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--add-json', type=Path, help='Additional saved listing array')
    parser.add_argument('--set-status', nargs=2, metavar=('URL', 'STATUS'))
    parser.add_argument('--note', default='')
    args = parser.parse_args()
    existing = read(QUEUE, {'listings': []})
    listings = {key(x['url']): x for x in existing['listings']}
    files = [SEARCH / f for f in SOURCES]
    if args.add_json:
        files.append(args.add_json)
    for path in files:
        for raw in read(path, []):
            c = raw.get('card') if isinstance(raw.get('card'), dict) else raw
            url = c.get('href') or c.get('url')
            if not url or 'welcometothejungle.com/' not in url:
                continue
            role = c.get('text') or c.get('role') or ''
            card = c.get('card', '')
            company = c.get('company') or (card.split('\n\n')[1] if '\n\n' in card else '')
            k = key(url)
            status, reason = scope(role, card)
            item = listings.setdefault(k, {
                'url': url, 'company': company, 'role': role, 'card': card,
                'status': status, 'note': reason, 'sources': [],
                'application_ids': [],
            })
            if path.name not in item['sources']:
                item['sources'].append(path.name)
            if raw.get('apply_url'):
                item['apply_url'] = raw['apply_url']
            if raw.get('posting'):
                item['posting'] = raw['posting']
    by_url, by_role = {}, {}
    apps_in_tracker = []
    for row in (SEARCH / 'applications.md').read_text().splitlines():
        if row.startswith('| 2026-'):
            cells = [x.strip() for x in row.strip('|').split('|')]
            if len(cells) >= 9:
                apps_in_tracker.append(dict(zip(['id', 'company', 'role', 'url', 'status'], cells)))
    for app in apps_in_tracker:
        by_url.setdefault(key(app['url']), []).append(app)
        by_role.setdefault((norm(app['company']), norm(app['role'])), []).append(app)
    blockers = {}
    for name in ['jobboards-blockers.json', 'wttj-skipped-and-blocked.json']:
        for b in read(SEARCH / name, []):
            if b.get('url'):
                blockers[key(b['url'])] = b.get('reason', '')
    for k, item in listings.items():
        apps = by_url.get(k) or by_role.get((norm(item['company']), norm(item['role'])), [])
        item['application_ids'] = list(dict.fromkeys(a['id'] for a in apps))
        submitted = [a for a in apps if a['status'] == 'submitted']
        if submitted:
            item.update(status='submitted', note='Confirmed in application tracker')
        elif apps:
            item.update(status='in progress', note='Existing attempt; inspect before retrying')
        elif k in blockers and item['status'] != 'excluded':
            # A prior partial-fit decision is reviewable under the new instruction.
            item.update(status='needs review', note=blockers[k])
        item['priority'] = role_priority(item['role'])
        item['international'] = not bool(re.search(r'\bParis\b|Boulogne|Levallois|Puteaux|Courbevoie', item.get('card', ''), re.I))
    if args.set_status:
        url, status = args.set_status
        if status == 'submitted':
            parser.error('Record confirmation in applications.md first; this script cannot assert submission')
        if status not in {'found', 'preparing', 'ready', 'in progress', 'needs review', 'excluded'}:
            parser.error('Invalid queue status')
        item = listings[key(url)]
        if item['status'] == 'submitted':
            parser.error('Cannot overwrite a confirmed submission')
        item.update(status=status, note=args.note)
    blacklist = {norm(b['company']) for b in read(SEARCH / 'company-blacklist.json', [])}
    for item in listings.values():
        if norm(item['company']) in blacklist and item['status'] != 'submitted':
            item.update(status='excluded', note='Company blacklisted by user; no further applications')
    ordered = sorted(listings.values(), key=lambda x: (
        x['status'] in {'submitted', 'excluded'}, not x['international'],
        x['priority'], x['status'] == 'needs review', x['company'].casefold(), x['role'],
    ))
    counts = dict(Counter(x['status'] for x in ordered))
    state = read(SEARCH / 'jobboards-state.json', {})
    data = {
        'board': 'Welcome to the Jungle', 'updated_at': datetime.now(timezone.utc).isoformat(),
        'batch_start_cumulative': 401, 'batch_target_additional': 150,
        'campaign_target': 1000, 'confirmed_cumulative': state.get('confirmed_applications_cumulative'),
        'counts': counts, 'listings': ordered,
    }
    QUEUE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    lines = ['# Welcome to the Jungle application queue', '',
             'One board for the next batch of roughly 150 submissions. International software roles first. Partial skills alignment is allowed.', '',
             f"Campaign total: {data['confirmed_cumulative']}/1000. Queue counts: " + ', '.join(f'{k}: {v}' for k, v in counts.items()) + '.', '',
             'Statuses come from saved records. A discovered URL is not a submission. Recheck availability and required screening in the browser.', '',
             '| Company | Role | Status | Listing | Application record | Note |',
             '| --- | --- | --- | --- | --- | --- |']
    def cell(s):
        return str(s).replace('|', '/').replace('\n', ' ')
    for item in ordered:
        records = ', '.join(f'[record](applications/{a}/)' for a in item['application_ids'])
        lines.append('| ' + ' | '.join(cell(v) for v in [item['company'], item['role'], item['status'], f"[listing]({item['url']})", records, item['note']]) + ' |')
    (SEARCH / 'wttj-volume-List.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({'listings': len(ordered), 'counts': counts, 'confirmed_cumulative': data['confirmed_cumulative']}))


if __name__ == '__main__':
    main()

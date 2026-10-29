#!/usr/bin/env python3
"""Filter saved search URLs against application records and recorded holds."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from career_policy import staff_only

ROOT = Path(__file__).resolve().parents[1]

def objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from objects(child)

def key(url):
    p = urlsplit(url)
    path = p.path.rstrip('/').removesuffix('/application').removesuffix('/apply')
    if p.netloc.lower() == 'jobs.ashbyhq.com':
        path = path.lower()
    return p.netloc.lower() + path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sources', nargs='+', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    tracker = (ROOT / 'job-search/applications.md').read_text()
    blacklist = json.loads((ROOT / 'job-search/company-blacklist.json').read_text())
    blocked = {
        re.sub(r'[^a-z0-9]', '', value.casefold())
        for entry in blacklist
        for value in [entry['company'], entry.get('slug', ''), *entry.get('aliases', [])]
        if value
    }
    recorded = set()
    for folder in (ROOT / 'job-search/applications').iterdir():
        if folder.is_dir():
            for name in ['metadata.json', 'confirmation.json', 'answers.json']:
                p = folder / name
                if p.exists():
                    for x in objects(json.loads(p.read_text())):
                        for field in ['url', 'application_url', 'employer_url']:
                            if isinstance(x.get(field), str):
                                recorded.add(key(x[field]))
    held = set()
    for pattern in ['*hold*.json', '*excluded*.json', '*exclusions*.json', '*blocker*.json', '*deferred*.json']:
        for p in (ROOT / 'job-search').glob(pattern):
            try:
                for x in objects(json.loads(p.read_text())):
                    for field in ['url', 'board_url', 'application_url', 'employer_url']:
                        if isinstance(x.get(field), str):
                            held.add(key(x[field]))
            except ValueError:
                continue
    kept, skipped, seen = [], [], set()
    for source in args.sources:
        for item in objects(json.loads(source.read_text())):
            url = item.get('url')
            title = item.get('title') or item.get('text', '').split('\n')[0]
            if not isinstance(url, str) or not isinstance(title, str) or not title:
                continue
            parsed = urlsplit(url)
            posting = '/job/' in parsed.path or (
                parsed.netloc == 'jobs.ashbyhq.com' and len(parsed.path.strip('/').split('/')) >= 2
            ) or (
                parsed.netloc == 'www.ycombinator.com' and re.match(r'^/companies/[^/]+/jobs/[^/]+', parsed.path)
            ) or (
                item.get('ats') == 'recruitee' and '/o/' in parsed.path
            ) or (
                parsed.netloc == 'www.arbeitnow.com' and re.match(r'^/jobs/companies/[^/]+/[^/]+', parsed.path)
            ) or (
                parsed.netloc == 'startup.jobs' and re.search(r'-\d+$', parsed.path)
            ) or parsed.netloc in {'apply.workable.com', 'job-boards.greenhouse.io', 'boards.greenhouse.io', 'jobs.lever.co'} or (
                parsed.netloc in {'app.welcometothejungle.com', 'thehub.io'} and '/jobs/' in parsed.path
            )
            if not posting:
                continue
            k = key(url)
            if k in seen:
                continue
            seen.add(k)
            listing_id = urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1]
            reason = None
            employer = str(item.get('company') or item.get('text', '').split('\n')[0]).strip()
            board = parsed.path.strip('/').split('/')[0] if parsed.netloc == 'jobs.ashbyhq.com' else ''
            location = str(item.get('location', item.get('country', '')))
            if re.search(r'\b(?:France|Paris|Lyon)\b', location, re.I):
                reason = 'France work location excluded; multi-location roles require a verified non-France destination'
            elif any(re.sub(r'[^a-z0-9]', '', value.casefold()) in blocked for value in [employer, board] if value):
                reason = 'Company is blacklisted by the user'
            elif item.get('status') == 'excluded' or item.get('exclusion_reason'):
                reason = item.get('exclusion_reason') or 'Previously excluded candidate'
            elif k in recorded or re.search(r'\b' + re.escape(listing_id) + r'\b', tracker):
                reason = 'Existing application; inspect record, do not retry'
            elif k in held:
                reason = 'Recorded hold or exclusion; inspect reason before reopening'
            elif re.search(r'\bback[\s-]*end\b', title, re.I):
                reason = 'Explicit backend title is blacklisted'
            elif staff_only(title):
                reason = 'Staff-only role is blacklisted; combined Senior/Staff remains eligible'
            row = dict(url=url, title=title, source=str(source))
            if reason:
                skipped.append(dict(row, reason=reason))
            else:
                kept.append(dict(row, status='Full posting, country and screening review still required'))
    args.output.write_text(json.dumps(dict(candidates=kept, skipped=skipped), indent=2) + '\n')
    print(f'{len(kept)} candidates requiring review; {len(skipped)} recorded or excluded URLs')

if __name__ == '__main__':
    main()

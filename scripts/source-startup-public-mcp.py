#!/usr/bin/env python3
"""Archive public Startup Jobs MCP search pages, without credentials or submissions."""
import argparse
import json
from pathlib import Path
import time

import urllib.request


class _Resp:
    def __init__(self, body): self._b = body
    def raise_for_status(self): pass
    def json(self): return json.loads(self._b)


def _post(url, headers, json_body, timeout):
    req = urllib.request.Request(url, data=json.dumps(json_body).encode(), headers=headers, method='POST')
    return _Resp(urllib.request.urlopen(req, timeout=timeout).read().decode())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--countries', nargs='+', required=True)
    parser.add_argument('--query', default='engineer')
    parser.add_argument('--pages', type=int, default=3)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    headers = {'Accept': 'application/json, text/event-stream', 'Content-Type': 'application/json'}
    coverage, candidates = [], {}
    if args.resume and args.output.exists():
        saved = json.loads(args.output.read_text())
        coverage = saved['coverage']
        candidates = {job['id']: job for job in saved['candidates']}
    request_id = 0
    for country in args.countries:
        cursor = None
        prior = [entry for entry in coverage if entry['country'] == country]
        if prior:
            cursor = prior[-1]['response'].get('next_cursor')
            if not cursor:
                continue
        start = max((entry['page'] for entry in prior), default=0) + 1
        for page in range(start, start + args.pages):
            request_id += 1
            params = {'q': args.query, 'country': country, 'limit': 50}
            if cursor:
                params['cursor'] = cursor
            response = _post('https://api.startup.jobs/mcp', headers, {
                'jsonrpc': '2.0', 'id': request_id, 'method': 'tools/call',
                'params': {'name': 'search_jobs', 'arguments': params},
            }, timeout=30)
            response.raise_for_status()
            envelope = response.json()
            if envelope.get('error') or envelope.get('result', {}).get('isError'):
                raise RuntimeError(envelope)
            data = json.loads(envelope['result']['content'][0]['text'])
            jobs = data.get('jobs', [])
            coverage.append({'country': country, 'page': page, 'count': len(jobs), 'response': data})
            for job in jobs:
                candidates[job['id']] = {**job, 'company_details': job.get('company'),
                    'company': job.get('company', {}).get('name', ''),
                    'source': 'Startup Jobs public MCP', 'screening': 'Full posting review required'}
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps({'source': 'https://startup.jobs/mcp',
                'limitation': 'Free public API covers last 14 days; older rendered queues remain eligible',
                'coverage': coverage, 'candidates': list(candidates.values())}, indent=2) + '\n')
            print(f'{country} page {page}: {len(jobs)} jobs; {len(candidates)} unique', flush=True)
            time.sleep(3.2)  # Respect the documented 20 requests per minute.
            cursor = data.get('next_cursor')
            if not cursor:
                break


if __name__ == '__main__':
    main()

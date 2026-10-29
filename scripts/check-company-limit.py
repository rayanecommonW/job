#!/usr/bin/env python3
"""Enforce the user's cumulative confirmed-company limit before a new form."""
import sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
companies=set()
for row in (root/'job-search/applications.md').read_text().splitlines():
    if not row.startswith('| 2026-'):continue
    cells=[s.strip() for s in row.strip('|').split('|')]
    if len(cells)>=9 and cells[4]=='submitted':companies.add(cells[1].casefold())
if len(companies)>=1000 and sys.argv[1].casefold() not in companies:
    raise SystemExit('Cumulative limit of 1,000 confirmed companies reached.')
print(f'{len(companies)} confirmed companies cumulatively; limit 1,000.')

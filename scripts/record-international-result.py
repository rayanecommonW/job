#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import date
root=Path(__file__).resolve().parent.parent
app=root/'job-search/applications'/sys.argv[1]
result=json.loads((app/'confirmation.json').read_text())
assert result['status']=='submitted'
p=root/'job-search/applications.md';rows=p.read_text().splitlines()
for i,row in enumerate(rows):
 if row.startswith('| '+sys.argv[1]+' |'):
  cells=row.split('|');cells[5]=' submitted ';cells[6]=' '+result['submitted_on']+' ';cells[9]=' Direct career-site success confirmed. [Confirmation](applications/'+sys.argv[1]+'/confirmation.json). ';rows[i]='|'.join(cells)
p.write_text('\n'.join(rows)+'\n')
v=json.loads((app/'verification.json').read_text());v.update(submitted=True,confirmation='confirmation.json');(app/'verification.json').write_text(json.dumps(v,indent=2)+'\n')
confirmed=[]
for p in (root/'job-search/applications').glob('*/confirmation.json'):
 d=json.loads(p.read_text())
 if d.get('round')=='international-2026-10-09' and d.get('status')=='submitted':confirmed.append(p)
companies={json.loads((p.parent/'metadata.json').read_text())['company'].casefold() for p in confirmed}
all_companies=set()
all_confirmed=0
for row in rows:
 if not row.startswith('| 2026-'):continue
 cells=[x.strip() for x in row.strip('|').split('|')]
 if len(cells)>=9 and cells[4]=='submitted':
  all_confirmed+=1
  all_companies.add(cells[1].casefold())
state=root/'job-search/international-state.json'
s=json.loads(state.read_text()) if state.exists() else {}
s.update(status='in progress',confirmed_applications=len(confirmed),confirmed_companies=len(companies),cumulative_confirmed_applications=all_confirmed,cumulative_confirmed_companies=len(all_companies),company_limit=1000,last_confirmed=sys.argv[1],updated_on=date.today().isoformat());state.write_text(json.dumps(s,indent=2)+'\n')
print('Direct campaign confirmed:',len(confirmed),'applications across',len(companies),'companies')

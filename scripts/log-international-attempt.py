#!/usr/bin/env python3
import json,sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
j=json.loads(Path(sys.argv[1]).read_text());result=j.pop('result',{});note=j.pop('note','Form requires review; not submitted.')
p=root/'job-search/discovery/attempts.json'
items=json.loads(p.read_text()) if p.exists() else []
items=[x for x in items if x['url']!=j['url']];items.append({**j,'result':result,'note':note});p.write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n')
tracker=root/'job-search/applications.md';s=tracker.read_text()
if '| '+j['id']+' |' not in s:
 def clean(x):return str(x).replace('|','/').replace('\n',' ')
 row='| '+' | '.join(map(clean,[j['id'],j['company'],j['title'],j['url'],'in progress','','','',note]))+' |\n'
 s=s.replace('\nUse `found`',row+'\nUse `found`');tracker.write_text(s)
state=root/'job-search/international-state.json';d=json.loads(state.read_text());d.update(last_attempted=j['url'],attempted_postings=len(items));state.write_text(json.dumps(d,indent=2)+'\n')

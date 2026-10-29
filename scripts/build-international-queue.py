#!/usr/bin/env python3
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
D=ROOT/'job-search/discovery'
jobs=json.loads((D/'jobs.json').read_text());seen=set();prior=[]
for a in (ROOT/'job-search/applications').glob('*/answers.json'):
 if not (a.parent/'confirmation.json').exists():continue
 try:
  d=json.loads(a.read_text());u=d.get('application_url','').split('?')[0].rstrip('/').removesuffix('/application').removesuffix('/apply');seen.add(u)
 except Exception:pass
for m in (ROOT/'job-search/applications').glob('*/metadata.json'):
 if (m.parent/'confirmation.json').exists():
  d=json.loads(m.read_text());prior.append((d.get('company','').casefold(),d.get('role','').casefold()))
def score(j):
 t=j['title'];body=j['posting'];s=0
 for p,w in [('founding',15),('full.?stack|product engineer',12),('front.?end|react|typescript',10),('back.?end',9),('applied AI|AI engineer|forward.?deployed',8),('software engineer',5)]:
  if re.search(p,t,re.I):s+=w
 if re.search('TypeScript|React|Next.js|Node.js|Python|Bun|Convex',body):s+=5
 if re.search('compil|kernel|GPU|CUDA|robotics|accelerator|control systems|quantitative',t,re.I):s-=20
 if j['region'] in ['Japan','Korea']:s+=4
 return s
queue=[];groups={};skipped=[]
for j in jobs:
 if j['url'].split('?')[0].rstrip('/') in seen or (j['company'].casefold(),j['title'].casefold()) in prior:continue
 if j['region'] in ['Japan','Korea'] and re.search(r'(?:fluent|proficient|business).{0,70}(?:Japanese|Korean)|(?:Japanese|Korean).{0,70}(?:required|requirement|fluency)',j['posting'],re.I):
  # Keep Japanese skills explicitly marked optional or nice-to-have for manual review.
  lines=[l for l in j['posting'].splitlines() if re.search('Japanese|Korean',l,re.I)]
  if any(re.search('required|requirement|must|proficient|fluent|business',l,re.I) and not re.search('nice|preferred|plus|optional',l,re.I) for l in lines):skipped.append({**j,'reason':'Required Japanese/Korean proficiency not established'});continue
 groups.setdefault(j['company'],[]).append(j)
for company,js in groups.items():
 js.sort(key=score,reverse=True)
 for n,j in enumerate(js):j['fit_score']=score(j);j['company_rank']=n
 queue+=js
queue.sort(key=lambda j:(j['company_rank'],-j['fit_score']))
(D/'application-queue.json').write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n');(D/'excluded-postings.json').write_text(json.dumps(skipped,ensure_ascii=False,indent=2)+'\n')
print('Deduplicated queue:',len(queue),'companies:',len(groups),'language exclusions:',len(skipped))

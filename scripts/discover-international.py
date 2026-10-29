#!/usr/bin/env python3
"""Read public company directories and ATS job feeds. Never submits forms."""
import concurrent.futures as cf
import hashlib, json, re, sys, time
from pathlib import Path
from datetime import date
from urllib.parse import urlparse
import requests, yaml
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parent.parent
DIR=ROOT/'job-search/discovery'
SOURCES=DIR/'sources'
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def key(v):return re.sub(r'[^a-z0-9]','',v.lower())
def seeds():
 companies={}
 def add(c):
  k=key(c['name'])
  if k not in companies:companies[k]={'id':k,'status':'discovered',**c}
  elif c.get('careers_url'):companies[k].update(c)
 for c in yaml.safe_load((SOURCES/'career-ops-portals.yml').read_text())['tracked_companies']:
  if c.get('enabled') is not False:add({**c,'source':'https://github.com/career-ops-hq/career-ops/blob/main/templates/portals.example.yml'})
 text=(SOURCES/'ft1000-2026-flourish.html').read_text()
 m=re.search(r'_Flourish_data = (.*?);\s*\n',text,re.S)
 if not m:raise ValueError('FT published table missing')
 data=json.JSONDecoder().raw_decode(re.sub(r'new Date\((-?\d+)\)',r'\1',m[1]))[0]
 ft=[]
 for r in data['rows']:
  r=r['columns']; link=re.match(r'\[(.*?)\]\((.*?)\)',r[1])
  if not link:continue
  c={'name':link[1],'website':link[2],'country':r[2],'sector':r[3],'ft_rank':r[0],'source':'https://www.ft.com/content/afd4a379-6332-47bb-bc65-04bd6eb24a19'};ft.append(c)
  if re.search(r'IT & Software|Fintech|Advertising|Education|Health',r[3],re.I):add(c)
 save(SOURCES/'ft1000-2026.json',ft)
 soup=BeautifulSoup((SOURCES/'japan-dev.html').read_text(),'html.parser')
 for a in soup.select('a[href]'):
  href=a.get('href','');name=a.get_text(' ',strip=True)
  if re.fullmatch(r'/companies/[a-z0-9-]+',href) and name and not re.search(r'Open Job|View|Visit',name):add({'name':re.sub(r'^NEW!\s*','',name),'country':'Japan','directory_url':'https://japan-dev.com'+href,'source':'https://japan-dev.com/companies'})
 # Official pages for Korea and additional international product companies.
 for name,country,url in [('Sendbird','South Korea','https://sendbird.com/careers'),('Moloco','South Korea','https://www.moloco.com/careers'),('Coupang','South Korea','https://www.coupang.jobs/en/'),('Toss','South Korea','https://toss.im/career'),('Kakao','South Korea','https://careers.kakao.com/'),('NAVER','South Korea','https://recruit.navercorp.com/'),('LINE','Japan','https://careers.linecorp.com/'),('SmartNews','Japan','https://about.smartnews.com/en/careers/'),('Mercari','Japan','https://careers.mercari.com/'),('Rakuten','Japan','https://global.rakuten.com/corp/careers/'),('Woven by Toyota','Japan','https://woven.toyota/en/careers/'),('PayPay','Japan','https://www.paypay.ne.jp/career/en/'),('Notion','US','https://jobs.ashbyhq.com/notion'),('Linear','US','https://jobs.ashbyhq.com/linear'),('Ramp','US','https://jobs.ashbyhq.com/ramp'),('Cursor','US','https://jobs.ashbyhq.com/cursor'),('OpenAI','US','https://jobs.ashbyhq.com/openai')]:add({'name':name,'country':country,'careers_url':url,'source':url,'source_note':'Official career-page seed; hiring and location verified during scan.'})
 old=json.loads((DIR/'companies.json').read_text()) if (DIR/'companies.json').exists() else []
 for c in old:
  if c['id'] in companies:companies[c['id']]={**companies[c['id']],**c}
  else:companies[c['id']]=c
 save(DIR/'companies.json',list(companies.values()));print('Company seeds:',len(companies),'FT full ranking:',len(ft))
CITY=re.compile(r'United States|\bUSA?\b|New York|San Francisco|San Mateo|Bay Area|Seattle|Boston|Los Angeles|Austin|Chicago|Washington|London|Berlin|Munich|München|Hamburg|Frankfurt|Dublin|Amsterdam|Rotterdam|Stockholm|Copenhagen|Oslo|Helsinki|Zurich|Zürich|Geneva|Genève|Lausanne|Basel|Vienna|Wien|Madrid|Barcelona|Lisbon|Lisboa|Porto\b|Milan|Milano|Rome|Roma|Brussels|Bruxelles|Luxembourg|Warsaw|Warszawa|Prague|Praha|Tallinn|Europe|EMEA|Tokyo|Japan|Osaka|Seoul|Korea|Toronto|Vancouver|Montreal|Canada',re.I)
TITLE=re.compile(r'software|full.?stack|front.?end|back.?end|founding engineer|product engineer|applied AI|AI engineer|AI product|machine learning engineer|forward.?deployed|solutions engineer|developer|développeur|engineering.*(?:AI|product)|(?:staff|principal) engineer|DevOps|site reliability|security engineer|cloud engineer',re.I)
EXCLUDE=re.compile(r'manager|director|VP |head of|intern|co.?op|apprentice|working student|electrical|mechanical|firmware|embedded|hardware|recruit|sales development|data analyst|analytics engineer|business intelligence',re.I)
def api_for(c):
 u=c.get('careers_url',''); api=c.get('api','')
 if 'boards-api.greenhouse.io' in api:return 'greenhouse',api
 if 'greenhouse.io/' in u:return 'greenhouse','https://boards-api.greenhouse.io/v1/boards/'+urlparse(u).path.strip('/').split('/')[0]+'/jobs'
 if 'ashbyhq.com/' in u:return 'ashby','https://api.ashbyhq.com/posting-api/job-board/'+u.split('ashbyhq.com/')[1].split('/')[0]
 if 'lever.co/' in u:return 'lever','https://api.lever.co/v0/postings/'+urlparse(u).path.strip('/').split('/')[0]+'?mode=json'
 return None,None
def scan_company(c):
 kind,api=api_for(c)
 if not api:return c,[]
 try:
  res=requests.get(api,timeout=22);res.raise_for_status();d=res.json(); rows=d if kind=='lever' else d.get('jobs',[]);out=[]
  for j in rows:
   if kind=='lever':title=j['text'];loc=j.get('categories',{}).get('location','');url=j['hostedUrl'];apply=j.get('applyUrl',url);body=j.get('descriptionPlain','')+'\n'+'\n'.join(x.get('text','')+'\n'+BeautifulSoup(x.get('content',''),'html.parser').get_text('\n') for x in j.get('lists',[]));body+='\n'+j.get('additionalPlain','')
   elif kind=='ashby':title=j['title'];loc=j.get('location','');url=j['jobUrl'];apply=j.get('applyUrl',url);body=j.get('descriptionPlain','') or BeautifulSoup(j.get('descriptionHtml',''),'html.parser').get_text('\n')
   else:title=j['title'];loc=j.get('location',{}).get('name','');url=j['absolute_url'];apply=url;body=j.get('content','')
   if not TITLE.search(title) or EXCLUDE.search(title) or not CITY.search(loc) or (re.search(r'Paris|France',loc,re.I) and not re.search(r'London|Berlin|US|Tokyo|Europe|EMEA',loc,re.I)):continue
   if not body and kind=='greenhouse':
    detail=requests.get(api+'/'+str(j['id']),timeout=15)
    if detail.ok:body=BeautifulSoup(detail.json().get('content',''),'html.parser').get_text('\n')
   if re.search(r'(?:cannot|unable to|do not|not able to|no|without) (?:offer |provide )?(?:visa )?sponsor|sponsorship (?:is )?not available|must (?:already )?be (?:legally )?authorized.*without.*sponsor',body,re.I) and re.search(r'US|United States|Japan|Korea|Canada|London|UK',loc,re.I):continue
   region='US' if re.search(r'United States|\bUS\b|New York|San Francisco|Bay Area|Seattle|Boston|Los Angeles|Austin|Chicago|San Mateo',loc,re.I) else 'Canada' if re.search(r'Canada|Toronto|Vancouver|Montreal',loc,re.I) else 'Japan' if re.search(r'Japan|Tokyo|Osaka',loc,re.I) else 'Korea' if re.search(r'Korea|Seoul',loc,re.I) else 'UK' if re.search(r'London|UK|United Kingdom',loc,re.I) else 'Suisse' if re.search(r'Zürich|Zurich|Geneva|Basel|Lausanne',loc,re.I) else 'EU'
   out.append({'company':c['name'],'company_id':c['id'],'title':title,'location':loc,'region':region,'url':url,'apply_url':apply,'provider':kind,'posting':body,'provider_id':str(j['id']),'captured_on':date.today().isoformat(),'status':'found'})
  c={**c,'status':'scanned','scan_on':date.today().isoformat(),'feed_count':len(rows),'matching_jobs':len(out),'api_url':api}
  return c,out
 except Exception as e:return {**c,'status':'scan_error','error':str(e)},[]
def scan():
 companies=json.loads((DIR/'companies.json').read_text());jobs=[];updated={}
 with cf.ThreadPoolExecutor(max_workers=8) as pool:
  for c,found in pool.map(scan_company,companies):updated[c['id']]=c;jobs+=found
 save(DIR/'companies.json',[updated[c['id']] for c in companies]);save(DIR/'jobs.json',jobs)
 print('Public ATS jobs in scope:',len(jobs),'companies with matches:',len({j['company_id'] for j in jobs}))
def mirror():
 companies=json.loads((DIR/'companies.json').read_text());jobs=json.loads((DIR/'jobs.json').read_text()) if (DIR/'jobs.json').exists() else []
 def cell(x):return str(x or '').replace('|','/').replace('\n',' ')
 text='# Company discovery\n\nUpdated '+date.today().isoformat()+'. Current campaign limit: 1,000 distinct companies. A discovered company is not an application. Roles are checked for location, software fit, salary and sponsorship before submission.\n\nSources: [career-ops portal catalog](https://github.com/career-ops-hq/career-ops/blob/main/templates/portals.example.yml), [FT1000 2026](https://www.ft.com/content/afd4a379-6332-47bb-bc65-04bd6eb24a19), [Japan Dev](https://japan-dev.com/companies), and official career pages. The complete 1,000-row FT ranking is archived under `job-search/discovery/sources/`; this table selects industries where software roles are plausible.\n\n| Company | Country / notes | Sector | Career page or directory | Status | Matching public-feed jobs | Source |\n| --- | --- | --- | --- | --- | --- | --- |\n'
 for c in companies:text+='| '+' | '.join(cell(x) for x in [c['name'],c.get('country',c.get('notes','')),c.get('sector','Technology / software'),c.get('careers_url',c.get('directory_url',c.get('website',''))),c['status'],c.get('matching_jobs',''),c['source']])+' |\n'
 (ROOT/'List.md').write_text(text)
 applications=[]
 for row in (ROOT/'job-search/applications.md').read_text().splitlines():
  if not row.startswith('| 2026-'):continue
  cells=[x.strip() for x in row.strip('|').split('|')]
  if len(cells)>=9:applications.append(dict(zip(['id','company','role','url','status','submitted_on','cv','follow_up','notes'],cells)))
 save(ROOT/'job-search/applications.json',applications)
 state=ROOT/'job-search/international-state.json'
 if state.exists():
  s=json.loads(state.read_text());s.update(discovered_companies=len(companies),feed_jobs_before_review=len(jobs),updated_on=date.today().isoformat());save(state,s)
 print('Mirrored companies and applications:',len(companies),len(applications))
if __name__=='__main__':
 for action in sys.argv[1:] or ['seeds','scan','mirror']:globals()[action]()

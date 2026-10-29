"""Save public YC job pages by European location, then review eligible postings."""
import concurrent.futures,json,re
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
locations='london berlin amsterdam paris madrid barcelona lisbon dublin stockholm copenhagen helsinki oslo tallinn zurich vienna munich warsaw prague brussels europe remote'.split()
urls=[f'https://www.ycombinator.com/jobs/location/{c}' for c in locations]+[f'https://www.ycombinator.com/jobs/role/software-engineer/{c}'for c in locations]
geo=re.compile(r'London|Berlin|Amsterdam|Madrid|Barcelona|Lisbon|Dublin|Stockholm|Copenhagen|Helsinki|Oslo|Tallinn|Zurich|Zürich|Vienna|Munich|Warsaw|Prague|Brussels|Europe|EMEA|United Kingdom|Germany|Netherlands|Sweden|Denmark|Portugal|Spain|Poland|Romania|Remote',re.I)
role=re.compile(r'engineer|developer|technical writer|developer relations|design engineer',re.I)
ban=re.compile(r'\bbackend\b|\bback-end\b|\bjava\b|\bQA\b|\btest(?:ing)?\b|support|principal|director|head of|hardware|mechanical|electrical|sales engineer',re.I)
def scan(u):
 audit={'url':u}
 try:
  r=requests.get(u,timeout=20);audit['status']=r.status_code;s=BeautifulSoup(r.text,'html.parser');audit['title']=s.title.get_text()if s.title else None
  jobs=[]
  for a in s.select('a[href*="/companies/"][href*="/jobs/"]'):
   title=a.get_text(' ',strip=True)
   if title=='Apply':continue
   card=a.parent.parent;txt=card.get_text(' ',strip=True);link=urljoin(u,a['href']);companylink=card.select_one('a[href*="/companies/"]:not([href*="/jobs/"])');company=companylink.get_text(' ',strip=True)if companylink else link.split('/companies/')[1].split('/')[0]
   jobs.append({'url':link,'title':title,'role':title,'company':company,'summary':txt,'source':u})
  audit['listing_count']=len(jobs)
  return audit,jobs
 except Exception as e:audit['error']=str(e);return audit,[]
with concurrent.futures.ThreadPoolExecutor(max_workers=10)as pool:r=list(pool.map(scan,urls))
allrows={j['url']:j for _,a in r for j in a}
candidates=[j for j in allrows.values()if role.search(j['title'])and not ban.search(j['title'])and geo.search(j['summary'])and not re.search(r'\bFrance\b|\bParis\b',j['summary'],re.I)and ('staff'not in j['title'].lower()or re.search(r'senior.*staff',j['title'],re.I))]
p=ROOT/'job-search/yc-europe-1586-2026-10-15-queue.json';p.write_text(json.dumps({'scope':'Public YC location and software-engineer pages. Invalid locations can return generic pages. Review actual job location and full posting.','coverage':[x for x,_ in r],'all_listings':list(allrows.values()),'candidates':candidates},indent=2)+'\n');print(json.dumps({'pages':len(r),'listings':sum(x.get('listing_count',0)for x,_ in r),'unique':len(allrows),'candidates':len(candidates),'output':str(p)}))

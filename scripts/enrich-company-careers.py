#!/usr/bin/env python3
"""Find published career-page links. HTTP discovery only, no application actions."""
import concurrent.futures as cf,json,re,sys
from pathlib import Path
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parent.parent
p=ROOT/'job-search/discovery/companies.json'
companies=json.loads(p.read_text())
def enrich(c):
 url=c.get('careers_url') or c.get('directory_url') or c.get('website')
 if not url:return c
 try:
  res=requests.get(url,timeout=16);soup=BeautifulSoup(res.text,'html.parser');links=[]
  if 'japan-dev.com/companies/' in url:
   slug=url.rstrip('/').split('/')[-1]
   c['directory_jobs']=list(dict.fromkeys(urljoin(url,a['href']) for a in soup.select('a[href]') if a['href'].startswith('/jobs/'+slug+'/')))
   official=[a['href'] for a in soup.select('a[href]') if a['href'].startswith('https://') and urlparse(a['href']).hostname and urlparse(a['href']).hostname.removeprefix('www.') in a.get_text(' ',strip=True) and not re.search('japan-dev|reddit|notion|twitter|linkedin|facebook|x.com',a['href'])]
   if not official:return {**c,'status':'directory_only','career_links':[]}
   c['website']=official[0]
   res=requests.get(official[0],timeout=16);soup=BeautifulSoup(res.text,'html.parser')
  for a in soup.select('a[href]'):
   href=urljoin(res.url,a['href']);label=a.get_text(' ',strip=True)
   if re.search(r'careers?|jobs|join.us|work.with.us|vacan|karriere|emploi|lavora|recruit|採用',href+' '+label,re.I) and href.startswith('https://') and not re.search('facebook|linkedin|twitter|reddit|notion|mailto:|japan-dev.com|tokyodev.com',href):links.append(href)
  ats=[u for u in links if re.search('jobs.ashbyhq.com|jobs(?:.eu)?.lever.co|job-boards(?:.eu)?.greenhouse.io|boards.greenhouse.io',u)]
  c={**c,'career_links':list(dict.fromkeys(links))[:20],'website_checked':res.status_code}
  if ats:c['careers_url']=ats[0];c['career_link_verified']=True
  elif not c.get('careers_url') and links:
   c['careers_url']=links[0];c['career_link_verified']=True
   r=requests.get(links[0],timeout=14);s=BeautifulSoup(r.text,'html.parser')
   ats=[urljoin(r.url,a['href']) for a in s.select('a[href]') if re.search('jobs.ashbyhq.com|jobs(?:.eu)?.lever.co|job-boards(?:.eu)?.greenhouse.io|boards.greenhouse.io',a['href'])]
   if ats:c['careers_url']=ats[0]
  return c
 except Exception as e:return {**c,'career_discovery_error':str(e)}
eligible=[c for c in companies if not c.get('api_url') and not c.get('website_checked') and c.get('status')!='directory_only']
selected=([c for c in eligible if c.get('country')=='South Korea']+
          [c for c in eligible if c.get('country')=='Japan']+
          [c for c in eligible if c.get('ft_rank')]+
          [c for c in eligible if 'remoteintech' in c.get('source','')])[:int(sys.argv[1] if len(sys.argv)>1 else 130)]
updated={}
with cf.ThreadPoolExecutor(max_workers=8) as pool:
 for c in pool.map(enrich,selected):updated[c['id']]=c
# Merge at the end to preserve status updates from other scripts.
current=json.loads(p.read_text())
p.write_text(json.dumps([{**c,**updated.get(c['id'],{})} for c in current],ensure_ascii=False,indent=2)+'\n')
print('Career pages checked:',len(updated),'ATS pages located:',sum(bool(re.search('ashbyhq|lever.co|greenhouse',c.get('careers_url',''))) for c in updated.values()))

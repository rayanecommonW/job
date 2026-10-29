import concurrent.futures,json,re
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
pages=[f'https://www.arbeitnow.com/jobs/{tag}?page={page}' for tag in ['frontend','full-stack','ai','software-engineer'] for page in range(1,24)]
def fetch(url):
 try:
  r=requests.get(url,timeout=20);s=BeautifulSoup(r.text,'html.parser');rows=[]
  for a in s.select('a[data-job-item-link]'):
   title=a.get_text(' ',strip=True)
   if not re.search('engineer|developer|entwickler',title,re.I) or re.search(r'back[ -]?end|java(?!script)|staff|test|QA|support|hardware|architect|manager',title,re.I):continue
   rows.append(dict(title=title,role=title,url=urljoin(r.url,a['href']),source=url))
  return dict(url=url,status=r.status_code,rows=len(rows),final_url=r.url),rows
 except Exception as e:return dict(url=url,error=str(e)),[]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as p:results=list(p.map(fetch,pages))
rows={r['url']:r for _,rs in results for r in rs}
output=ROOT/'job-search/arbeitnow-1591-2026-10-15-queue.json'
output.write_text(json.dumps(dict(coverage=[a for a,_ in results],candidates=list(rows.values())),indent=2)+'\n')
print(json.dumps(dict(pages=len(results),unique_candidates=len(rows),path=str(output))))

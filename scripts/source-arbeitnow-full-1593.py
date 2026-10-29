"""Archive full public postings and their ordinary employer redirects."""
import concurrent.futures,json,re
from pathlib import Path
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
rows=json.loads((ROOT/'job-search/arbeitnow-1591-2026-10-15-queue.json').read_text())['candidates']
def fetch(row):
    out=dict(row)
    try:
        r=requests.get(row['url'],timeout=20)
        s=BeautifulSoup(r.text,'html.parser')
        description=s.select_one('[itemprop=description]')
        company=s.select_one('[itemprop=hiringOrganization]')
        out.update(status_code=r.status_code,company=company.get_text(' ',strip=True) if company else '',posting=description.get_text('\n',strip=True) if description else '',location='Germany',country='Germany')
        link=s.select_one('#text_issues_with_applying a[href]')
        if link:
            target=requests.get(link['href'],timeout=20)
            out['employer_url']=target.url
        out['review_required']=True
    except Exception as e:out['error']=str(e)
    return out
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:full=list(pool.map(fetch,rows))
p=ROOT/'job-search/arbeitnow-full-1593-2026-10-15-queue.json'
p.write_text(json.dumps(dict(candidates=full),indent=2)+'\n')
print(json.dumps(dict(scanned=len(full),with_posting=sum(bool(r.get('posting')) for r in full),with_employer_url=sum(bool(r.get('employer_url')) for r in full))))

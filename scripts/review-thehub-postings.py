"""Save public JobPosting JSON-LD for the queued startup listings."""
import concurrent.futures,json,requests
from pathlib import Path
from bs4 import BeautifulSoup
src=Path('job-search/thehub-priority-1530-2026-10-15-queue.json');rows=json.loads(src.read_text())['candidates']
def fetch(row):
 try:
  r=requests.get(row['url'],timeout=22);r.raise_for_status();s=BeautifulSoup(r.text,'html.parser');j=next(json.loads(x.string) for x in s.select('script[type="application/ld+json"]') if x.string and 'JobPosting' in x.string);row.update(posting=BeautifulSoup(j.get('description',''),'html.parser').get_text(' ',strip=True),structured_posting=j)
 except Exception as e:row['review_error']=str(e)
 return row
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:reviewed=list(pool.map(fetch,rows[:55]))
out=src.with_name('thehub-reviewed-1530-2026-10-15-queue.json');out.write_text(json.dumps({'candidates':reviewed},indent=2)+'\n');print('Saved',len(reviewed),'public postings')

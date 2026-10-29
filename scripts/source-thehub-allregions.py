"""Archive every page of The Hub public engineer results."""
import concurrent.futures,json,re,requests
from bs4 import BeautifulSoup
from pathlib import Path

def fetch(spec):
 country,term,page=spec
 url=f'https://thehub.io/jobs?search={term}&countryCode={country}&page={page}'
 try:
  r=requests.get(url,timeout=25);r.raise_for_status();s=BeautifulSoup(r.text,'html.parser');rows=[]
  for card in s.select('.card__content:has(.card-job-find-list__link)'):
   parts=[x.get_text(' ',strip=True) for x in card.select('.bullet-inline-list span')];a=card.select_one('.card-job-find-list__link');title=card.select_one('.card-job-find-list__position').get_text(' ',strip=True)
   rows.append(dict(title=title,role=title,company=parts[0] if parts else '',location=parts[1] if len(parts)>1 else '',url='https://thehub.io'+a['href'],source_page=page,country_code=country,search_term=term))
  return dict(page=page,url=url,status=r.status_code,rows=len(rows),last_page=max([int(re.search(r'[?&]page=(\d+)',a['href']).group(1)) for a in s.select('a[href]') if re.search(r'[?&]page=(\d+)',a['href'])] or [1])),rows
 except Exception as e:return dict(page=page,url=url,error=str(e)),[]
specs=[(country,term,1) for country in ['DK','SE','NO','FI','EU','REMOTE'] for term in ['engineer','developer','founding']]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 results=list(pool.map(fetch,specs))
 more=[(country,term,page) for (country,term,_),(audit,rows) in zip(specs,results) for page in range(2,audit.get('last_page',1)+1)]
 results+=list(pool.map(fetch,more))
unique={r['url']:r for a,rows in results for r in rows};rows=list(unique.values());out=Path('job-search/thehub-allregions-1530-2026-10-15-queue.json');out.write_text(json.dumps({'candidates':rows,'coverage':[a for a,rs in results]},indent=2)+'\n');print(json.dumps({'pages':len(results),'raw_rows':sum(len(rs) for a,rs in results),'unique_rows':len(rows)}))

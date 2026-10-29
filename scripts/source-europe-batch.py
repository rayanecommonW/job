"""Read public employer boards and save a deduplicated Europe review queue."""
import concurrent.futures, json, re
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
SLUGS = '''supabase pennylane braintrust storyblok dust lovable cursor poolside langfuse langchain
langdock langflow deepset qdrant weaviate modal railway render vercel replit resend inngest
trigger replicate baseten tome hex granola incident.io plain cord intercom customerio
polar lago infisical twenty attio clay folk mintlify gitbook fern mastra stackone
composio arcade conductor orq.ai lemlist lindy relay.app sana sana-labs legora
parloa happyrobot tacto osapiens getomni omni lightdash evidence metabase motherduck
kestra windmill temporal restack diagrid hatchet electric-sql liveblocks tldraw
retool superblocks appsmith budibase nango merge kiln cryptio finom qonto alan
slite yseop bleen latticespace harmonic particles physicsx
'''.split()
blacklist = json.loads((ROOT / 'job-search/company-blacklist.json').read_text())
blocked_boards = {
    re.sub(r'[^a-z0-9]', '', value.casefold())
    for entry in blacklist
    for value in [entry['company'], entry.get('slug', '')]
    if value
}
SLUGS = [slug for slug in SLUGS
         if re.sub(r'[^a-z0-9]', '', slug.split('?')[0].casefold()) not in blocked_boards]
tracker = json.loads((ROOT/'job-search/applications.json').read_text())
prior_text = (ROOT/'job-search/applications.md').read_text()
hold_text = '\n'.join(p.read_text(errors='replace') for pattern in ['*hold*.json','*excluded*.json','*blocker*.json','*deferred*.json'] for p in (ROOT/'job-search').glob(pattern))
geo = re.compile(r'Europe|EMEA|France|Paris|Germany|Berlin|Munich|Netherlands|Amsterdam|Spain|Madrid|Barcelona|Portugal|Lisbon|Italy|Milan|Sweden|Stockholm|Finland|Helsinki|Denmark|Copenhagen|Poland|Warsaw|Austria|Vienna|Belgium|Brussels|Romania|Bucharest|Czech|Prague|Remote, Global|Worldwide|Switzerland|Zurich|London|United Kingdom', re.I)
role = re.compile(r'engineer|developer|technical writer|developer experience|developer relations',re.I)
exclude = re.compile(r'\bback[ -]?end\b|\bQA\b|\btest\b|support|security|reliability|sales engineer|solutions engineer|engineering manager',re.I)
def fetch(slug):
    try:
        r=requests.get('https://api.ashbyhq.com/posting-api/job-board/'+slug,timeout=18)
        if r.status_code!=200:return {'board':slug,'status':r.status_code},[]
        found=[]
        for j in r.json().get('jobs',[]):
            title=j.get('title',''); loc=str(j.get('location',''))+' '+str(j.get('secondaryLocations',[]));url=j.get('jobUrl','');pid=url.rstrip('/').split('/')[-1]
            if not role.search(title) or exclude.search(title) or ('staff' in title.lower() and 'senior' not in title.lower()):continue
            if not geo.search(loc):continue
            if pid in prior_text or pid in hold_text:continue
            found.append(dict(company=slug,title=title,role=title,location=loc,url=url,posting=j.get('descriptionPlain',''),published=j.get('publishedAt'),compensation=j.get('compensation'),prior_company_roles=[dict(role=a['role'],status=a['status']) for a in tracker if a.get('company','').casefold()==slug.casefold()]))
        return {'board':slug,'status':200,'candidates':len(found)},found
    except Exception as e:return {'board':slug,'error':str(e)},[]
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:results=list(pool.map(fetch,SLUGS))
rows=[x for _,items in results for x in items]
rows.sort(key=lambda x:(bool(x['prior_company_roles']),not bool(re.search('founding|product|agent|full.?stack|frontend|AI|developer experience',x['role'],re.I)),x['company']))
out=ROOT/'job-search/europe-sourced-1477-2026-10-15-queue.json'
out.write_text(json.dumps({'scope':'Europe, country quotas cancelled','candidates':rows,'boards':[b for b,_ in results]},indent=2)+'\n')
print(json.dumps({'path':str(out),'candidates':len(rows),'boards':len(results),'preview':[dict(company=r['company'],role=r['role'],location=r['location'],url=r['url'],prior=len(r['prior_company_roles'])) for r in rows[:65]]},indent=2))

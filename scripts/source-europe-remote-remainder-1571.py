import concurrent.futures,importlib.util,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('feeds',Path(__file__).with_name('source-europe-expanded.py'));feeds=importlib.util.module_from_spec(spec);spec.loader.exec_module(feeds)
feeds.GEO=re.compile('remote|distributed|global|anywhere',re.I)
boards=json.loads((ROOT/'job-search/europe-successful-feeds-1569.json').read_text())
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:results=list(pool.map(feeds.fetch,boards))
rows=[x for _,a in results for x in a]
p=ROOT/'job-search/europe-remote-remainder-1571-2026-10-15-queue.json';p.write_text(json.dumps({'scope':'Remote-only labels from previously discovered complete feeds. Full Europe eligibility review required.','candidates':rows,'coverage':[a for a,_ in results]},indent=2)+'\n')
print(json.dumps({'feeds':len(boards),'jobs':sum(a.get('complete_feed_jobs',0)for a,_ in results),'rows':len(rows),'output':str(p)}))

#!/usr/bin/env python3
"""Import public directory entries for discovery, without implying live hiring."""
import json,re,yaml
from pathlib import Path
root=Path(__file__).resolve().parent.parent
base=root/'job-search/discovery'
p=base/'companies.json'
companies=json.loads(p.read_text()); seen={c['id'] for c in companies}; added=[]
for f in sorted((base/'sources/remote-in-tech-source/src/companies').glob('*.md')):
    raw=f.read_text()
    if not raw.startswith('---'):continue
    c=yaml.safe_load(raw.split('---',2)[1])
    region=str(c.get('region',''))
    if not re.search('worldwide|Europe|EMEA|US|United States|Canada|Germany|UK|Japan|Korea',region,re.I):continue
    name=c.get('title'); career=c.get('careers_url'); website=c.get('website')
    if not name or not website:continue
    ident=re.sub('[^a-z0-9]','',name.lower())
    if ident in seen:continue
    row={'id':ident,'name':name,'country':region,'website':website,'source':'https://github.com/remoteintech/remote-jobs/blob/main/src/companies/'+f.name,'source_note':'Public remote-friendly directory. Current hiring, locations and visa support remain unverified.','status':'discovered'}
    if career:row['careers_url']=career
    companies.append(row);added.append(row);seen.add(ident)
p.write_text(json.dumps(companies,ensure_ascii=False,indent=2)+'\n')
(base/'sources/remote-in-tech-import.json').write_text(json.dumps(added,ensure_ascii=False,indent=2)+'\n')
print(f'Imported {len(added)} additional company records; total {len(companies)}.')

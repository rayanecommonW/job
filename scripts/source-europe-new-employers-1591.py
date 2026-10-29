"""Collect complete public ATS feeds for additional startup employers."""
import concurrent.futures
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("feeds", Path(__file__).with_name("source-europe-expanded.py"))
feeds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feeds)
slugs = 'lovio finstack tilta reev reev-com ecoligo entrio sentia sentia-ai tilores retrack retorio getvoila lettria re:cap recap recapi zenline zenline-ai finmatics finmatics-gmbh flowfact casavi facilio sensoneo smartvatix evreka sensolus scentronix picterra flyability wingtra embotech embion technis locatee coople bexio yokoy auxmoney anyfin miloan moss getmoss getpliant pliant upflow-ai cometca findr findr-ai searchland landtech plotbox planninghub featherless featherless-ai kilocode kilo-code aider avante openhands allhands all-hands-ai nebuly briaai bria-ai deepsight mindspeak unbody unbody-io tryleap leap-ai inferless baseten cerebrium inference-net inference-networks runpod primeintellect northflank koyeb koyeb-inc zeabur coolify unolog aiven-io upstash neon-tech turso motherduck xata convex-dev getconvex electric-sql electric-sqlite instantdb instant-database zero-rockset timescale questdb greptime greptimedb cratedb crunchydata tinybird-corp estuary estuary-flow glassflow glassflow-dev feldera arroyo decodable kurrent streamnative risingwave materialize redpanda-data graviton telemetrydeck openstatus hyperdx signoz better-stack dash0-com groundcover causely coroot ilert ilert-gmbh rootly firehydrant incidentio instatus squadcast sentry-io glitchtip simpleanalytics plausible plausible-analytics posthog-com june-so avo-app mixpanel amplitude-com statsig growthbook flagsmith unleash-getunleash flipt configcat bucket bucket-co featurevisor flagsmith-com devcycle launchdarkly harness-io gitstart gitclear gitkraken gitguardian-gmbh coana aikido-security aikido oxeye zenity saviynt permify cerbos permit-io osso descope clerk-dev stytch zitadel logto hanko hanko-io supertokens stack-auth workos frontegg authzed authz-authzed aembit onum streamkap estuary-tech memgraph kusho kusho-ai qodo-ai coframe browserbase steel-dev hyperbrowser anchorbrowser browser-use magnitude greptile-com dentsu-ai mercura complir rever solve-intelligence protex-ai deepnote wasmer zip'.split()

known = set()
for path in (ROOT / "job-search").glob("europe*-queue.json"):
    try:
        data = json.loads(path.read_text())
    except (ValueError, OSError):
        continue
    if isinstance(data, dict):
        for item in data.get("coverage", []):
            if isinstance(item, dict):
                known.add((item.get("ats"), item.get("board")))

boards = [(ats, slug) for ats in ("ashby", "greenhouse", "lever")
          for slug in dict.fromkeys(slugs) if (ats, slug) not in known]
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
    results = list(pool.map(feeds.fetch, boards))
rows = [row for _, items in results for row in items]
path = ROOT / "job-search/europe-new-employers-1591-2026-10-15-queue.json"
path.write_text(json.dumps({
    "scope": "Additional employer discovery. Full role/location/size review still required.",
    "candidates": rows,
    "coverage": [audit for audit, _ in results],
}, indent=2) + "\n")
print(json.dumps({"requested": len(boards),
                  "complete_feeds": sum(a.get("status") == 200 for a, _ in results),
                  "jobs_scanned": sum(a.get("complete_feed_jobs", 0) for a, _ in results),
                  "candidates": len(rows), "output": str(path)}))

"""Collect complete public ATS feeds for additional startup employers."""
import concurrent.futures
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("feeds", Path(__file__).with_name("source-europe-expanded.py"))
feeds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feeds)
slugs = """
langfuse langdock parloa peec peec-ai aisle pact pact-ai lawhive lawhive-ai
hyperbound 11x 11x-ai synthflow synthflow-ai stotles unmind spill spill-chat
blaxel blaxel-ai kapa kapa-ai polyapi n8n e2b e2b-dev browser-use browseruse
composio composio-dev portkey portkey-ai conductor conduct lottie-org nory
nory-ai voima meadow stacks stacks-ai stacks-finance moss getmoss pliant
getpliant payrails getpaid getpaidio tacto deepeye deepeye-medical dcycle
cobee buoy antler antler-portfolio flox floxdev flox-dev jetify devbox
zenml zenml-io zenmlio zenity labellerr baserow appsmith budibase windmill
windmill-labs tooljet supabase trigger trigger-dev inngest encore encoredev
encore-dev kestra orchestras conductorone omakase rosetta rosetta-ai
helsing-ai arx arx-robotics quantum-systems quantum-systems-gmbh ecoplan
robopegasus anybotics neura neura-robotics agilox gizelis robotics summit
sekoia filigran solace-ai qdrant vespa turbopuffer lancedb weaviate milvus
superlinked channable efficy sendcloud parcelperform parcel-perform byrd
getbyrd everstox hive hive-logistics cargoone cargo-one cargoboard sennder
forto shippeo shipup cosuno koppla flexxter smino bimguard evernest casavo
casafari huspy habito better-place finmatics finabro finn finnfleet vimcar
fleetio ryd ryd-one vialytics vialink newtonx cleverconnect matched
workmotion workflex workfully worksome jobbatical eversports airbank qwist
token token-io tokenio yapily volt volt-io fipto mondu bantoa iwoca knoma
upvest lemon-markets lemonmarkets lemon airolabs aire aire-logic
pasqal planqc iqm iqm-quantum-computers alice-bob aliceandbob quera riverlane
quix quixio quix-analytics hivemq streamnative redpanda tremor tremorvideo
matillion kestrix cube cube-dev cubejs tinybird motherduck duckdb-labs duckdb
theorg the-org omnia omnia-ai luqo rhesis rhesis-ai arize-ai literal literal-ai
merantix merantix-momentum pyne pyne-ai enso enso-ai rome rome-ai sentisense
qbiq qbiq-ai bimobject bimcollab rootglobal root-global beebop beebop-ai
tracify adtriba smint smint-io charp charp-ai telli telli-ai fluently
usefluently bluecall healthforce-doctorly doctorly doctari deeptalk
pleo-io lemfi lemonaid apron getapron april april-ai finster finster-ai
doctronic heidi-health tortus tortus-ai tortushealth aindo-ai keye
""".split()

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
path = ROOT / "job-search/europe-new-employers-1558-2026-10-15-queue.json"
path.write_text(json.dumps({
    "scope": "Additional employer discovery. Full role/location/size review still required.",
    "candidates": rows,
    "coverage": [audit for audit, _ in results],
}, indent=2) + "\n")
print(json.dumps({"requested": len(boards),
                  "complete_feeds": sum(a.get("status") == 200 for a, _ in results),
                  "jobs_scanned": sum(a.get("complete_feed_jobs", 0) for a, _ in results),
                  "candidates": len(rows), "output": str(path)}))

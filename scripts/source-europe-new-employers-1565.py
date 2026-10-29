"""Collect complete public ATS feeds for additional startup employers."""
import concurrent.futures
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("feeds", Path(__file__).with_name("source-europe-expanded.py"))
feeds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feeds)
slugs = """yokoy numbrs neon neon-free neon-switzerland neon-free-ch neon-money radicant findependent selma selma-finance truewealth wealtharc wealthpilot investsuite investengine plum withplum chip getchip moneybox moneyfarm fundcraft finom finmid bunch-capital getbunch airwallex rooser fresha treatwell zenoti booksy truelayer primer primer-api primerio paddle lemon-squeezy lemonsqueezy lemonway fintecture bridgerpay paydock gr4vy solidgate paytweak payhawk payhawkio getpopsure getsafe feather-insurance feather finlex insurely hedvig lassie petgood petli firstvet digitail vetstoria vetster vetera anicura luftborn airforestry airforestry-ab ecoplanet greenly climateview normative normativetech carbmee carbonsignal watershed sweep sweepnet sweep-ai plana plan-a-world plan-a carbonchain carbonesque goodcarbon carbonfuture climatefarmers agreena agritask fieldmate farmforce agranimo spacept spacept-ab liveeo satellitevu satvu okapi-orbits constellr orbitalexpress ororatech unio topi topi-gmbh equipme circulee everphone grover refurbed back-market swappie rebuy asgoodasnew mixmove shipmondo nshift instabee budbee parcelhero byways freightos cogoport cargoai cargofive cargoflux cargo2go freightify freightify-technologies shippio tractian tractian-europe cognite cognitionfactory collect-ai collectai billie billie-io mondu getmoss moss-finance getpliant pliant-finance finmatics finom-payments finteum treasury-spring treasuryspring conveo weightless hypoport getharley gethelios holofy numi numi-ai lindus-health cera cera-care birdie birdie-care lilli sensio napsleep napper sleepcycle hume hume-ai zencargo verity veritystudios momentum momentum-io gocertify vexcash finbee heavyfinance profitus estateguru rendin bidrento moderan obol obol-ai finout vantage vantage-sh cast-ai castai nops qoala secfix heydata heydata-eu caralegal lawpilots lawlift bryter lexroom lexroom-ai lexverify lawyerd lexly legalhero legal-os legalos genialai jarvis-legal avokaado cleverdocs contractbook pocketlaw oneflow getoneflow precisely preciselycontracts ontra juro plug-and-pay""".split()

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
path = ROOT / "job-search/europe-new-employers-1565-2026-10-15-queue.json"
path.write_text(json.dumps({
    "scope": "Additional employer discovery. Full role/location/size review still required.",
    "candidates": rows,
    "coverage": [audit for audit, _ in results],
}, indent=2) + "\n")
print(json.dumps({"requested": len(boards),
                  "complete_feeds": sum(a.get("status") == 200 for a, _ in results),
                  "jobs_scanned": sum(a.get("complete_feed_jobs", 0) for a, _ in results),
                  "candidates": len(rows), "output": str(path)}))

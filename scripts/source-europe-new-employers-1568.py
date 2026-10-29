"""Collect complete public ATS feeds for additional startup employers."""
import concurrent.futures
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("feeds", Path(__file__).with_name("source-europe-expanded.py"))
feeds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feeds)
slugs = """aikido aikidosecurity zenity olympix sema4 duo-ai reliable-ai verdn autonomi autogenai sifflet sqlmesh tobiko sqlc evidence evidence-dev lightcast trustlayer userled embarque trumpet sendtrumpet trumpet-software trumpet-app trumpet-ai amplemarket ample-market leadoo dealfront leadfeeder leadinfo leadiq usergems wrisk urbanjungle marshmallow-cover simplifai simplifai-ai boost-ai boostai boost-ai-as kindly kindly-ai kindly-as supersonik superlinked gradient gradientlabs gradient-labs root-signals rootsignals fluent fluent-ai fluento fathom-video fathom-ai jam-dev jam-dev-inc jamdotdev gladia happyrobot cartesia kokoro-ai roam roam-ai recall recall-ai recallai tl-dv tldv rewatch read-ai readme mintlify scalar speakeasy speakeasy-api ferris ferris-ai langfuse langwatch lunary honeyhive braintrust maxim maxim-ai evals maximhq baserow nocodb budibase retool tooljet jetadmin directus kestra windmill windmill-labs inngest trigger-dev trigger triggerdotdev inlang paraglide translucid tolgee locize phrase lokalise simplelocalize better-auth betterauth supertokens clerk stytch descope workos hanko zitadel infisical doppler bitwarden passbolt vaultwarden keila listmonk loops resend plunk useplunk novu courier knock knocklabs knocks knocksapp novuhq knock-app attio folk folk-app twenty twentycrm twenty-crm breakout trybreakout unthread eesel eesel-ai kapa kapa-ai kyp kyp-ai keencorp creo creo-ai traceloop patronus patronus-ai validio reembank chift unify unify-ai unifygtm joinunify claudia claudia-ai xapien xelix light light-inc light-finance finway finway-de candis candis-io paynest payflows payflow payflow-io pemo askpemo omnevo orderbird lottielab rive spline spline-design endless-tools uncut uncut-gems cal-com calcom dub-co dub-link topologic tidalflow latitude latitude-so latitude-ai zeropath zeropath-ai inkeep-ai getm3 m3ter metronome orb withorb lago getlago hypergrowth hotglue parquet datarade explorium treblle apideck merge merge-dev unifiedto unified-to integration-app integrationapp nango-dev nango-com""".split()

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
path = ROOT / "job-search/europe-new-employers-1568-2026-10-15-queue.json"
path.write_text(json.dumps({
    "scope": "Additional employer discovery. Full role/location/size review still required.",
    "candidates": rows,
    "coverage": [audit for audit, _ in results],
}, indent=2) + "\n")
print(json.dumps({"requested": len(boards),
                  "complete_feeds": sum(a.get("status") == 200 for a, _ in results),
                  "jobs_scanned": sum(a.get("complete_feed_jobs", 0) for a, _ in results),
                  "candidates": len(rows), "output": str(path)}))

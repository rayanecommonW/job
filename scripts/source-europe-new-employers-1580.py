"""Collect complete public ATS feeds for additional startup employers."""
import concurrent.futures
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("feeds", Path(__file__).with_name("source-europe-expanded.py"))
feeds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feeds)
slugs = """tessl tessl-ai poolside poolside-ai augment augmentcode augment-code faber-ai conductor conductor-ai factory factory-ai codegen codegen-sh coderabbit code-rabbit qodo codium codiumai tabnine codota sweep-ai greptile ellipsis ellipsis-dev devin cognition cognition-ai rovo devzero dev-zero Daytona daytona-io codesandbox gitpod ona ona-com gitbutler zed zed-industries replit stackblitz bolt-new boltnew lovable-dev base44 base-44 dyad tempo tempo-labs v0 v0-app flutterflow framer webflow penpot specify zeroheight supernova supernova-io storyblok storyblok-gmbh hygraph prismic contentful builder builder-io contentstack dato datocms sanity-io payload payloadcms strapi-io ghost-foundation directus-io deepset-ai haystack-ai deepset-labs chapsvision lighton lighton-ai kyutai primaa bioptimus owkin zymedi agomab aqemia-ai insilico-medicine insilico labgenius labgenius-ai basecamp-research cradlebio cradle-bio cradle epoch-biodesign multiomic-health relation-therapeutics relationtx relation isomorphic isomorphiclabs hpai eleven-therapeutics bit-bio bitbio cellvoyant scarlet scarlet-com scarlet-medical accuhealth heidihealth heidi-health tortus tortus-ai tandem-health nabla-copilot corti corti-ai abtrace deepc deepc-ai dental-monitoring dentalmonitoring ava-health ava ava-women femtasy clareandme clare-me nilo nilo-health nilohealth likeminded myndup unmind spill spill-chat oliva oliva-health moka mindler kry livi doktorse doctorly samedi doctena doctena-sa planity fresha mangomint phorest treatwell timma bokadirekt easypractice terveyystalo mehilainen petleo felmo petsapp vidivet purrmetrix firstvet-animal cozero greenpixie carbn karomia greenly-earth sweep-net ecologi ecology carbmee planetly persefoni carbominer enode reonic gridbeyond gridio gridcog greenflux monta ampeco virta ev-energy evenergy chargetrip chargecloud chargeflow ampcontrol ampcontrol-io aedifion vilisto dabbel metr metrbio metr-building thermondo octopus-energy zolar otovo 1komma5 1komma5grad enter-de variolytics ecoworks alcemy alcemy-tech alcemy-gmbh concrete4change volumental zoovu pixis pixis-ai neuroflash frase jasper-ai writesonic copy-ai rytr anyword textcortex-ai axdraft spellbook spellbook-legal robin-ai robinai leya leya-ai legora lawhive lawhive-ai amicable amicable-app amicable-io genie-ai harvey-ai harvey-law superlegal bolster-ai v7 v7labs v7-labs v7-go v7go robin avvoka vaayu vaayu-tech neatleaf ingrid instagrid instagrid-gmbh planqc qruise qm quantum-machines quantinuum pasqal quandela alice-bob aliceandbob quera iqm iqm-quantum meetiqm anyon-system silentwave semiqon riverlane phasecraft q-ctrl quantrol-ox quantrolox horizon-quantum quantinuum-quantum""".split()

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
path = ROOT / "job-search/europe-new-employers-1580-2026-10-15-queue.json"
path.write_text(json.dumps({
    "scope": "Additional employer discovery. Full role/location/size review still required.",
    "candidates": rows,
    "coverage": [audit for audit, _ in results],
}, indent=2) + "\n")
print(json.dumps({"requested": len(boards),
                  "complete_feeds": sum(a.get("status") == 200 for a, _ in results),
                  "jobs_scanned": sum(a.get("complete_feed_jobs", 0) for a, _ in results),
                  "candidates": len(rows), "output": str(path)}))

"""Collect complete public ATS feeds for additional startup employers."""
import concurrent.futures
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("feeds", Path(__file__).with_name("source-europe-expanded.py"))
feeds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feeds)
slugs = """aglide lamb-labs lamblabs reactwise princeps rex-inc mesmer complydo cogram airweave onechronos caribou wasmer dalus zeit-ai zeit sitefire hey-telo heytelo finto-de finto comena deepnote runway coloop noloco manufact""".split()

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
path = ROOT / "job-search/europe-new-employers-yc-1586-2026-10-15-queue.json"
path.write_text(json.dumps({
    "scope": "Additional employer discovery. Full role/location/size review still required.",
    "candidates": rows,
    "coverage": [audit for audit, _ in results],
}, indent=2) + "\n")
print(json.dumps({"requested": len(boards),
                  "complete_feeds": sum(a.get("status") == 200 for a, _ in results),
                  "jobs_scanned": sum(a.get("complete_feed_jobs", 0) for a, _ in results),
                  "candidates": len(rows), "output": str(path)}))

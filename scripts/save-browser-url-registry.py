#!/usr/bin/env python3
"""Rebuild the career URL registry from saved application records and queues."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEARCH = ROOT / "job-search"
rows = {}


def add(url, source, **details):
    if not isinstance(url, str) or not url.startswith(("https://", "http://")):
        return
    row = rows.setdefault(url, {"url": url, "sources": []})
    if source not in row["sources"]:
        row["sources"].append(source)
    for key, value in details.items():
        if value is not None:
            row[key] = value


for path in SEARCH.glob("*-queue.json"):
    data = json.loads(path.read_text())
    candidates = data.get("candidates", []) if isinstance(data, dict) else data
    if not isinstance(candidates, list):
        continue
    for row in candidates:
        add(row.get("href") or row.get("url"), str(path.relative_to(ROOT)),
            role=row.get("role") or row.get("title") or row.get("text"),
            company=row.get("company"), status=row.get("status"))

for path in (SEARCH / "wttj-documents").glob("*.json"):
    row = json.loads(path.read_text())
    add(row.get("url"), str(path.relative_to(ROOT)), application_id=row.get("id"),
        company=row.get("company"), role=row.get("role"))

for row in json.loads((SEARCH / "applications.json").read_text()):
    add(row.get("url"), "job-search/applications.json", application_id=row.get("id"),
        company=row.get("company"), role=row.get("role"), status=row.get("status"))

output = {
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "tab_policy": "Multiple tabs and browsers authorized. Use practical batches, archive URLs, and close resolved managed tabs. Protect unresolved submissions.",
    "maximum_campaign_browser_tabs": None,
    "default_campaign_browser_tabs": None,
    "urls": list(rows.values()),
}
path = SEARCH / "browser-url-registry.json"
path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
print(f"Saved {len(rows)} URLs to {path.relative_to(ROOT)}")

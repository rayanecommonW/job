#!/usr/bin/env python3
"""Mirror saved Built In discovery queues with confirmed and blocked statuses."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEARCH = ROOT / "job-search"
items = {}
for path in sorted(SEARCH.glob("jobboards-builtin*queue.json")):
    for item in json.loads(path.read_text()):
        if isinstance(item, dict) and item.get("href"):
            items.setdefault(item["href"], item)
confirmed = {}
for path in (SEARCH / "applications").glob("*/metadata.json"):
    receipt = path.parent / "confirmation.json"
    if receipt.exists() and json.loads(receipt.read_text()).get("status") == "submitted":
        meta = json.loads(path.read_text())
        confirmed[meta.get("url")] = meta.get("id", path.parent.name)
blocked = {item["url"]: item.get("reason", "Blocked") for item in json.loads((SEARCH / "jobboards-blockers.json").read_text())}
rows = []
for url, item in items.items():
    status = "confirmed" if url in confirmed else "blocked" if url in blocked else "queued or pending"
    rows.append({**item, "status": status, "application_id": confirmed.get(url), "blocker": blocked.get(url)})
(SEARCH / "builtin-queue-mirror.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
lines = ["# Built In listings", "", "Saved discovery URLs. Only site-confirmed submissions count as applications.", "", f"{len(rows)} distinct listings.", "", "| Company | Role | Status |", "| --- | --- | --- |"]
for item in rows:
    company = item.get("company") or item.get("card", "").split("\n")[0]
    role = item.get("text", "").replace("|", "/").replace("\n", " ")
    lines.append(f"| {company.replace('|', '/')} | [{role}]({item['href']}) | {item['status']} |")
(SEARCH / "builtin-List.md").write_text("\n".join(lines) + "\n")
print(f"Mirrored {len(rows)} listings; {sum(item['status'] == 'confirmed' for item in rows)} confirmed URLs.")

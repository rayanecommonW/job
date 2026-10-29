#!/usr/bin/env python3
"""Archive an explicit site receipt, then record it: save-receipt.py ID COUNTRY URL TEXT [TAB]."""
import fcntl, json, subprocess, sys
from datetime import date
from pathlib import Path
app_id, country, url, text = sys.argv[1:5]
tab = sys.argv[5] if len(sys.argv) > 5 else 'tab_b'
app = Path(__file__).resolve().parents[1] / 'job-search/applications' / app_id
assert (app / 'answers.json').exists(), 'Save answers before recording a receipt'
(app / 'confirmation.json').write_text(json.dumps(dict(text=text, url=url, status='submitted', submitted_on=date.today().isoformat(), country=country, in_scope=True), indent=2, ensure_ascii=False) + '\n')
with open('/tmp/career-receipt.lock', 'w') as lock:  # parallel agents share the trackers
    fcntl.flock(lock, fcntl.LOCK_EX)
    subprocess.run([sys.executable, str(Path(__file__).parent / 'record-current-receipt.py'), app_id, tab], check=True)

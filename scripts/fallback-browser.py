#!/usr/bin/env python3
"""Send a local task to the fallback browser when T3 reports no host."""
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

request = urllib.request.Request('http://127.0.0.1:18763', data=Path(sys.argv[1]).read_bytes(), headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(request, timeout=55) as response:
        print(response.read().decode())
except urllib.error.HTTPError as error:
    print(error.read().decode())
    raise SystemExit(1)

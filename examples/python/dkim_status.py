#!/usr/bin/env python3
# Check the DKIM verification status of a removal request.
# Usage: python3 dkim_status.py <event_id>

import json                                          # pretty-print the JSON response
import os                                            # IPRX_BASE
import sys                                           # the event_id argument
import urllib.error                                  # catch HTTP errors
import urllib.request                                # stdlib HTTP client

BASE = os.environ.get("IPRX_BASE", "https://iprx.org")  # set IPRX_BASE only if you use a different host
if len(sys.argv) < 2:                                # event_id is required
    raise SystemExit("usage: python3 dkim_status.py <event_id>")  # how to run it
EVENT_ID = sys.argv[1]                               # from the removal response
url = f"{BASE}/api/v1/removals/{EVENT_ID}/dkim-status"  # GET the status document
try:                                                 # send it
    with urllib.request.urlopen(url, timeout=30) as resp:
        print(json.dumps(json.load(resp), indent=2))  # dkim_status is pending, passed, or failed
except urllib.error.HTTPError as exc:                # 404 if the event_id is unknown
    print(exc.code)                                  # status
    print(exc.read().decode("utf-8", "replace"))     # body

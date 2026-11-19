#!/usr/bin/env python3
# Fetch event history for an IPv4 address or a 64-character hash_id.
# Usage: python3 history.py [ip_or_hash]
# Default is 192.0.2.1. Public views redact requestor contact details.

import json                                          # pretty-print the JSON response
import os                                            # read IPRX_BASE
import sys                                           # read the lookup key
import urllib.parse                                  # encode the key if it contains reserved characters
import urllib.request                                # stdlib HTTP client

BASE = os.environ.get("IPRX_BASE", "https://iprx.org")  # set IPRX_BASE only if you use a different host
KEY = sys.argv[1] if len(sys.argv) > 1 else "192.0.2.1"  # IP, hash_id, or event_id
url = f"{BASE}/api/v1/history/{urllib.parse.quote(KEY)}"  # GET /api/v1/history/{key}
with urllib.request.urlopen(url, timeout=30) as resp:  # GET the URL
    data = json.load(resp)                           # parse the JSON body
print(json.dumps(data, indent=2))                    # print a readable document

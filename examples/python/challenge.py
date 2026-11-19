#!/usr/bin/env python3
# Fetch a SHA-256 proof-of-work challenge used by nomination and removal POSTs.
# Usage: python3 challenge.py

import json                                          # pretty-print the JSON response
import os                                            # read IPRX_BASE
import urllib.request                                # stdlib HTTP client; no extra packages required

BASE = os.environ.get("IPRX_BASE", "https://iprx.org")  # set IPRX_BASE only if you use a different host
with urllib.request.urlopen(f"{BASE}/api/v1/challenge", timeout=30) as resp:  # GET /api/v1/challenge
    data = json.load(resp)                           # parse {challenge, bits, expires_in}
print(json.dumps(data, indent=2))                    # print a readable document

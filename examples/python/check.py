#!/usr/bin/env python3
# Check whether one IPv4 address is listed, and why.
# Usage: python3 check.py [ipv4]
# Default is 192.0.2.1 (RFC 5737 TEST-NET-1).
# The response includes nomination_progress, for example "3/5".

import json                                          # pretty-print the JSON response
import os                                            # read IPRX_BASE
import sys                                           # read the command-line IP argument
import urllib.request                                # stdlib HTTP client; no extra packages required

BASE = os.environ.get("IPRX_BASE", "https://iprx.org")  # set IPRX_BASE only if you use a different host
IP = sys.argv[1] if len(sys.argv) > 1 else "192.0.2.1"  # first argument, or TEST-NET-1
url = f"{BASE}/api/v1/check/{IP}"                    # path is /api/v1/check/{ip}
with urllib.request.urlopen(url, timeout=30) as resp:  # GET the URL
    data = json.load(resp)                           # parse the JSON body
print(json.dumps(data, indent=2))                    # print a readable document, including nomination_progress

#!/usr/bin/env python3
# Search public, redacted records by hostname, IP, hash_id, ASN, ISP, or country.
# Usage: python3 search.py [query]
# Default query is "nt-isp" (TOT Thailand PTR names).

import json                                          # pretty-print the JSON response
import os                                            # read IPRX_BASE
import sys                                           # read the query string
import urllib.parse                                  # encode the q parameter
import urllib.request                                # stdlib HTTP client

BASE = os.environ.get("IPRX_BASE", "https://iprx.org")  # set IPRX_BASE only if you use a different host
Q = sys.argv[1] if len(sys.argv) > 1 else "nt-isp"   # hostname substring or other public search term
url = f"{BASE}/api/v1/search?{urllib.parse.urlencode({'q': Q})}"  # GET /api/v1/search?q=
with urllib.request.urlopen(url, timeout=30) as resp:  # GET the URL
    data = json.load(resp)                           # parse the JSON body
print(json.dumps(data, indent=2))                    # print a readable document

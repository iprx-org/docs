#!/usr/bin/env python3
# Ask IPRX to prove a digest on Verae (original first-wins stamp, plus restamp history).
# Usage: python3 prove.py [sha256]
# If the prover is down you still get HTTP 200 with prove.ok=false.

import json                                          # request and response JSON
import os                                            # IPRX_BASE
import sys                                           # the digest argument
import urllib.error                                  # catch HTTP errors
import urllib.request                                # stdlib HTTP client

BASE = os.environ.get("IPRX_BASE", "https://iprx.org")  # set IPRX_BASE only if you use a different host
HASH = sys.argv[1] if len(sys.argv) > 1 else "2c7606c0d53d7a800192f11609c939e66826f2af9c93fc971b850a97d5937466"  # 192.0.2.1 add event
body = json.dumps({"digest": HASH}).encode()         # body may use digest or hash_id
req = urllib.request.Request(f"{BASE}/api/v1/prove", data=body, method="POST", headers={"Content-Type": "application/json", "Accept": "application/json"})  # build the POST
try:                                                 # send it
    with urllib.request.urlopen(req, timeout=30) as resp:  # may be 200 with prove.ok=false
        print(json.dumps(json.load(resp), indent=2))  # print the prove document
except urllib.error.HTTPError as exc:                # unexpected HTTP error
    print(exc.code)                                  # status
    print(exc.read().decode("utf-8", "replace"))     # body

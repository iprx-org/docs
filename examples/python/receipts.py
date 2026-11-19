#!/usr/bin/env python3
# Download one event receipt as JSON, HTML, and PDF, plus the whole-IP bundle.
# Usage: python3 receipts.py [hash_id_or_event_id] [ipv4] [outdir]
# Short URLs also work: https://iprx.org/r/{hash_id}.pdf

import os                                            # IPRX_BASE and the output folder
import sys                                           # command-line arguments
import urllib.request                                # stdlib HTTP client

BASE = os.environ.get("IPRX_BASE", "https://iprx.org")  # set IPRX_BASE only if you use a different host
KEY = sys.argv[1] if len(sys.argv) > 1 else "2c7606c0d53d7a800192f11609c939e66826f2af9c93fc971b850a97d5937466"  # 192.0.2.1 add event
IP = sys.argv[2] if len(sys.argv) > 2 else "192.0.2.1"  # address for the bundle
OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/iprx-receipts"  # where to save the files
os.makedirs(OUT, exist_ok=True)                      # create the folder if needed

def fetch(url, dest):                                # GET a URL to a local file
    print(f"GET {url} -> {dest}")                    # show what we are doing
    urllib.request.urlretrieve(url, dest)            # write the bytes

fetch(f"{BASE}/api/v1/receipts/{KEY}.json", f"{OUT}/receipt.json")  # canonical JSON
fetch(f"{BASE}/api/v1/receipts/{KEY}.html", f"{OUT}/receipt.html")  # printable HTML
fetch(f"{BASE}/api/v1/receipts/{KEY}.pdf", f"{OUT}/receipt.pdf")    # PDF
fetch(f"{BASE}/api/v1/receipts/ip/{IP}.json", f"{OUT}/bundle.json") # whole-IP bundle
for name in ("receipt.json", "receipt.html", "receipt.pdf", "bundle.json"):  # list sizes
    path = os.path.join(OUT, name)                   # local path
    print(f"{name}: {os.path.getsize(path)} bytes")  # confirm each file landed

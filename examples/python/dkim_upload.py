#!/usr/bin/env python3
# Upload a DKIM-signed .eml to prove domain control for a removal request.
# Usage: python3 dkim_upload.py <event_id> <message.eml>
# This script only uploads a local file; it does not send any email.
# The .eml must contain the one-time token from POST /api/v1/removals.

import json                                          # pretty-print the JSON response
import os                                            # IPRX_BASE
import sys                                           # command-line arguments
import urllib.error                                  # catch HTTP errors
import urllib.request                                # stdlib HTTP client

BASE = os.environ.get("IPRX_BASE", "https://iprx.org")  # set IPRX_BASE only if you use a different host
if len(sys.argv) < 3:                                # both arguments are required
    raise SystemExit("usage: python3 dkim_upload.py <event_id> <message.eml>")  # how to run it
EVENT_ID = sys.argv[1]                               # from the removal response, for example blv2-...
EML = sys.argv[2]                                    # path to a raw RFC822 .eml on disk
raw = open(EML, "rb").read()                         # read the local file bytes
if len(raw) < 20:                                    # too small to be a real message
    raise SystemExit("eml file is empty or too short")  # stop before we POST junk

boundary = "----iprx-dkim-boundary"                  # multipart boundary; change if you like
parts = []                                           # the body sections
parts.append(f"--{boundary}\r\n".encode())           # opening boundary
parts.append(b'Content-Disposition: form-data; name="eml"; filename="message.eml"\r\n')  # field name is eml
parts.append(b"Content-Type: message/rfc822\r\n\r\n")  # declare the part as a mail message
parts.append(raw)                                    # the raw .eml bytes
parts.append(f"\r\n--{boundary}--\r\n".encode())     # closing boundary
body = b"".join(parts)                               # one HTTP body
req = urllib.request.Request(                        # POST /api/v1/removals/{id}/dkim
    f"{BASE}/api/v1/removals/{EVENT_ID}/dkim",
    data=body,
    method="POST",
    headers={"Accept": "application/json", "Content-Type": f"multipart/form-data; boundary={boundary}"},
)
try:                                                 # send the upload
    with urllib.request.urlopen(req, timeout=45) as resp:
        print(resp.status)                           # 201 when the check is recorded
        print(json.dumps(json.load(resp), indent=2))  # result is stamped either way
except urllib.error.HTTPError as exc:                # 4xx / 5xx
    print(exc.code)                                  # status
    print(exc.read().decode("utf-8", "replace"))     # body

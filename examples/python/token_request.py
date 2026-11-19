#!/usr/bin/env python3
# Request a one-click email that issues an IPRX API token.
# Usage: IPRX_EMAIL=you@example.com python3 token_request.py [label]
# The email comes from veraetimestamp@gmail.com. Opening the link shows the token once.
# First-time requestors also create a billing-disabled Verae account and must accept the license.
# 501(c)(3) nonprofits and schools must upload documentation via POST /api/v1/accounts instead.
# This script does not print or store the token; it only asks the API to send the email.

import hashlib                                       # SHA-256 for the proof-of-work
import json                                          # request and response JSON
import os                                            # IPRX_BASE, IPRX_EMAIL, IPRX_ORG_SIZE
import sys                                           # optional label argument
import urllib.error                                  # catch HTTP 4xx/5xx
import urllib.request                                # stdlib HTTP client

BASE = os.environ.get("IPRX_BASE", "https://iprx.org")  # set IPRX_BASE only if you use a different host
EMAIL = os.environ.get("IPRX_EMAIL")                 # the address that should receive the link
if not EMAIL:                                        # the API will also reject a missing address
    raise SystemExit("set IPRX_EMAIL to the address that should receive the link")
LABEL = sys.argv[1] if len(sys.argv) > 1 else "script"  # optional label, for example "laptop"
ORG_SIZE = os.environ.get("IPRX_ORG_SIZE", "individual")  # one of the published org-size ids

def http_json(method, url, body=None):               # small GET/POST helper
    data = None if body is None else json.dumps(body).encode()  # encode a JSON body when present
    headers = {"Accept": "application/json"}         # ask for JSON
    if data is not None:
        headers["Content-Type"] = "application/json" # this endpoint expects JSON
    req = urllib.request.Request(url, data=data, method=method, headers=headers)  # build the request
    try:                                             # 2xx
        with urllib.request.urlopen(req, timeout=45) as resp:
            return resp.status, json.load(resp)      # parsed body
    except urllib.error.HTTPError as exc:            # 4xx / 5xx
        raw = exc.read()                             # error body
        try:
            parsed = json.loads(raw) if raw else {}  # JSON error
        except json.JSONDecodeError:
            parsed = raw.decode("utf-8", "replace")  # plain text error
        return exc.code, parsed                      # status plus body

def solve_pow(challenge, bits):                      # find a nonce with enough leading zero bits
    n = 0                                            # start at zero
    while True:                                      # 18 bits is usually under a million tries
        digest = hashlib.sha256(f"{challenge}:{n}".encode()).digest()  # the API hashes this exact string
        zeros = 0                                    # count leading zero bits
        for b in digest:                             # left to right
            if b == 0:
                zeros += 8                           # a zero byte is eight bits
                continue                             # keep counting
            zeros += 8 - b.bit_length()              # remaining bits in the first non-zero byte
            break                                    # stop at the first non-zero byte
        if zeros >= bits:                            # hard enough
            return str(n)                            # the nonce as a decimal string
        n += 1                                       # try the next nonce

status, ch = http_json("GET", f"{BASE}/api/v1/challenge")  # one-time challenge (honeypot + PoW)
if status != 200:                                    # cannot continue without it
    raise SystemExit(f"challenge failed: {status} {ch}")  # stop with the error
nonce = solve_pow(ch["challenge"], int(ch["bits"]))  # usually 18 bits
body = {                                             # TokenRequestIn
    "email": EMAIL,                                  # where to send the one-click link
    "label": LABEL,                                  # optional name for this token
    "org_size": ORG_SIZE,                            # required on first account setup
    "license_accepted": True,                        # required on first account setup
    "challenge": ch["challenge"],                    # opaque string from GET /challenge
    "pow_nonce": nonce,                              # the nonce we just found
    "company_url": "",                               # honeypot; must stay empty
}
status, resp = http_json("POST", f"{BASE}/api/v1/tokens/request", body)  # 202 if accepted for sending
print(status)                                        # HTTP status
print(json.dumps(resp, indent=2))                    # body; it never includes the token itself

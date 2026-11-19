#!/usr/bin/env python3
# Nominate one IPv4 address: fetch a challenge, solve the proof-of-work, POST /nominations.
# Usage: python3 nominate.py <ipv4> [reason]
# Documentation, private, and reserved addresses are rejected with HTTP 400.
# Leave company_url empty; that field is a honeypot.
# One email (plus the client IP the API sees) counts as one nominator toward the 5-nominator threshold.

import hashlib                                       # SHA-256 for the proof-of-work
import json                                          # request and response JSON
import os                                            # IPRX_BASE, IPRX_NAME, IPRX_EMAIL
import sys                                           # command-line arguments
import urllib.error                                  # catch HTTP 4xx/5xx
import urllib.request                                # stdlib HTTP client

BASE = os.environ.get("IPRX_BASE", "https://iprx.org")  # set IPRX_BASE only if you use a different host
IP = sys.argv[1] if len(sys.argv) > 1 else "192.0.2.10"  # default TEST-NET is rejected on purpose
REASON = sys.argv[2] if len(sys.argv) > 2 else "TEST documentation nomination from the IPRX examples; RFC 5737 TEST-NET."  # >= 8 chars
NAME = os.environ.get("IPRX_NAME", "IPRX examples TEST")  # your display name
EMAIL = os.environ.get("IPRX_EMAIL", "docs-test@example.com")  # used to count distinct nominators

def http_json(method, url, body=None):               # small GET/POST helper
    data = None if body is None else json.dumps(body).encode()  # encode a JSON body when present
    headers = {"Accept": "application/json"}         # ask for JSON
    if data is not None:
        headers["Content-Type"] = "application/json" # the nominations API expects JSON
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
    n = 0                                            # start at zero; any unique string works
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

status, ch = http_json("GET", f"{BASE}/api/v1/challenge")  # one-time challenge
if status != 200:                                    # cannot continue without it
    raise SystemExit(f"challenge failed: {status} {ch}")  # stop with the error
nonce = solve_pow(ch["challenge"], int(ch["bits"]))  # usually 18 bits
body = {                                             # NominationIn
    "ip": IP,                                        # address to nominate
    "reason": REASON,                                # why it should be listed
    "evidence": "TEST",                              # optional supporting text
    "name": NAME,                                    # who is nominating
    "email": EMAIL,                                  # used to count distinct nominators
    "org": "IPRX docs examples",                     # optional organisation
    "challenge": ch["challenge"],                    # opaque string from GET /challenge
    "pow_nonce": nonce,                              # the nonce we just found
    "company_url": "",                               # honeypot; must stay empty
}
status, resp = http_json("POST", f"{BASE}/api/v1/nominations", body)  # 201 on success, 400 for TEST-NET
print(status)                                        # HTTP status
print(json.dumps(resp, indent=2))                    # body (public views redact contact details)

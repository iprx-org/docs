#!/usr/bin/env python3
# Request removal of one IPv4 address: challenge, proof-of-work, POST /removals.
# Usage: python3 removal.py <ipv4> [reason]
# Success is 201 with status pending_dkim and a one-time token.
# The token is saved under ~/.iprx/<event_id>.token with mode 600; do not commit it.
# Next: put the token in a DKIM-signed .eml and run dkim_upload.py. This script does not send email.

import hashlib                                       # SHA-256 for the proof-of-work
import json                                          # request and response JSON
import os                                            # IPRX_BASE, IPRX_NAME, IPRX_EMAIL
import pathlib                                       # private token file path
import sys                                           # command-line arguments
import urllib.error                                  # catch HTTP 4xx/5xx
import urllib.request                                # stdlib HTTP client

BASE = os.environ.get("IPRX_BASE", "https://iprx.org")  # set IPRX_BASE only if you use a different host
IP = sys.argv[1] if len(sys.argv) > 1 else "192.0.2.1"  # address to request removal for
REASON = sys.argv[2] if len(sys.argv) > 2 else "TEST documentation removal request from the IPRX examples; not a real delist."  # >= 8 chars
NAME = os.environ.get("IPRX_NAME", "IPRX examples TEST")  # your display name
EMAIL = os.environ.get("IPRX_EMAIL", "docs-test@example.com")  # an address you control

def http_json(method, url, body=None):               # small GET/POST helper
    data = None if body is None else json.dumps(body).encode()  # encode a JSON body when present
    headers = {"Accept": "application/json"}         # ask for JSON
    if data is not None:
        headers["Content-Type"] = "application/json" # the removals API expects JSON
    req = urllib.request.Request(url, data=data, method=method, headers=headers)  # build the request
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return resp.status, json.load(resp)      # parsed body
    except urllib.error.HTTPError as exc:
        raw = exc.read()                             # error body
        try:
            parsed = json.loads(raw) if raw else {}  # JSON error
        except json.JSONDecodeError:
            parsed = raw.decode("utf-8", "replace")  # plain text error
        return exc.code, parsed

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
            return str(n)
        n += 1                                       # try the next nonce

status, ch = http_json("GET", f"{BASE}/api/v1/challenge")  # one-time challenge
if status != 200:                                    # cannot continue without it
    raise SystemExit(f"challenge failed: {status} {ch}")
nonce = solve_pow(ch["challenge"], int(ch["bits"]))  # usually 18 bits
body = {                                             # RemovalIn
    "ip": IP,                                        # address to request removal for
    "name": NAME,                                    # who is requesting
    "email": EMAIL,                                  # an address you control
    "reason": REASON,                                # why it should be delisted
    "org": "IPRX docs examples",                     # optional organisation
    "challenge": ch["challenge"],                    # opaque string from GET /challenge
    "pow_nonce": nonce,                              # the nonce we just found
    "company_url": "",                               # honeypot; must stay empty
}
status, resp = http_json("POST", f"{BASE}/api/v1/removals", body)  # 201 pending_dkim when healthy
print(status)                                        # HTTP status
print(json.dumps(resp, indent=2) if not isinstance(resp, str) else resp)  # body includes a token — keep it private
if isinstance(resp, dict) and resp.get("token") and resp.get("event_id"):  # save the token off-repo
    path = pathlib.Path.home() / ".iprx" / f"{resp['event_id']}.token"  # ~/.iprx/<event_id>.token
    path.parent.mkdir(mode=0o700, exist_ok=True)     # private directory
    path.write_text(resp["token"] + "\n")            # write the one-time token only
    path.chmod(0o600)                                # owner read/write only
    print(f"# token saved privately to {path} (mode 600); include it in your DKIM-signed .eml", file=sys.stderr)  # remind the user

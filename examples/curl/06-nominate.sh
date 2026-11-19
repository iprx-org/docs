#!/usr/bin/env bash
# Nominate one IPv4 address via POST /api/v1/nominations.
# Usage:
#   ./06-nominate.sh <ipv4> [reason]                    # anonymous: solves the proof-of-work
#   IPRX_TOKEN=iprx_… ./06-nominate.sh <ipv4> [reason]  # verified token: skips PoW, no rate limit
# Documentation, private, and reserved addresses are rejected with HTTP 400.
# Leave company_url empty; that field is a honeypot.
# A live POST of 192.0.2.10 on 19 Nov 2026 returned 400 with that reserved-address message.

set -euo pipefail                                    # exit on error, unset variable, or a failed pipe
BASE="${IPRX_BASE:-https://iprx.org}"      # set IPRX_BASE to use a different API host
IP="${1:-192.0.2.10}"                                # address to nominate; default is TEST-NET (will be rejected)
REASON="${2:-TEST documentation nomination from the IPRX examples; RFC 5737 TEST-NET.}"  # at least 8 characters
NAME="${IPRX_NAME:-IPRX examples TEST}"              # set IPRX_NAME to your display name
EMAIL="${IPRX_EMAIL:-docs-test@example.com}"         # set IPRX_EMAIL to your address; used to count distinct nominators
TOKEN="${IPRX_TOKEN:-}"                              # optional verified token; if set, skip the proof-of-work
AUTH=()                                              # curl header args, empty when anonymous
if [[ -n "${TOKEN}" ]]; then                         # verified-token path
  AUTH=(-H "Authorization: Bearer ${TOKEN}")        # format: Authorization: Bearer iprx_…
fi
if [[ -z "${TOKEN}" ]]; then                         # anonymous path still needs a challenge
  CH_JSON="$(curl -sS "${BASE}/api/v1/challenge")"   # fetch a fresh one-time challenge
  # Solve SHA-256(challenge + ":" + nonce) with at least `bits` leading zero bits (usually 18).
  NONCE="$(CH_JSON="$CH_JSON" python3 -c '
import hashlib, json, os
ch = json.loads(os.environ["CH_JSON"])
challenge, bits = ch["challenge"], int(ch["bits"])
n = 0
while True:
    digest = hashlib.sha256(f"{challenge}:{n}".encode()).digest()
    zeros = 0
    for b in digest:
        zeros = zeros + 8 if b == 0 else zeros + (8 - b.bit_length())
        if b != 0:
            break
    if zeros >= bits:
        print(n)
        break
    n += 1
')"
  CHALLENGE="$(CH_JSON="$CH_JSON" python3 -c 'import json,os; print(json.loads(os.environ["CH_JSON"])["challenge"])')"  # extract the opaque string
else
  CHALLENGE=""                                       # unused when a token is present
  NONCE=""                                           # unused when a token is present
fi
BODY="$(IP="$IP" REASON="$REASON" NAME="$NAME" EMAIL="$EMAIL" CHALLENGE="$CHALLENGE" NONCE="$NONCE" python3 -c '
import json, os
body = {
    "ip": os.environ["IP"],
    "reason": os.environ["REASON"],
    "evidence": "TEST",
    "name": os.environ["NAME"],
    "email": os.environ["EMAIL"],
    "org": "IPRX docs examples",
    "company_url": "",
}
if os.environ.get("CHALLENGE"):
    body["challenge"] = os.environ["CHALLENGE"]
    body["pow_nonce"] = os.environ["NONCE"]
print(json.dumps(body))
')"                                                   # NominationIn JSON; company_url must stay empty
curl -sS -X POST "${BASE}/api/v1/nominations" \
  -H "Content-Type: application/json" \
  "${AUTH[@]}" \
  -d "${BODY}"                                       # 201 on success, 400 for TEST-NET
echo                                                 # add a trailing newline

#!/usr/bin/env bash
# Request a one-click email that issues an IPRX API token.
# Usage: IPRX_EMAIL=you@example.com ./12-token-request.sh [label]
# The email comes from veraetimestamp@gmail.com. Opening the link shows the token once.
# First-time requestors also create a billing-disabled Verae account and must accept the license.
# 501(c)(3) nonprofits and schools must upload documentation via POST /api/v1/accounts instead.
# This script does not print or store the token; it only asks the API to send the email.

set -euo pipefail                                    # exit on error, unset variable, or a failed pipe
BASE="${IPRX_BASE:-https://iprx.org}"      # set IPRX_BASE to use a different API host
EMAIL="${IPRX_EMAIL:?set IPRX_EMAIL to the address that should receive the link}"  # required
LABEL="${1:-script}"                                 # optional label, for example "laptop" or "honeypot-1"
ORG_SIZE="${IPRX_ORG_SIZE:-individual}"              # one of: nonprofit_501c3, school, individual, or a revenue tier
CH_JSON="$(curl -sS "${BASE}/api/v1/challenge")"     # fetch a fresh one-time challenge (honeypot + PoW on this endpoint)
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
BODY="$(EMAIL="$EMAIL" LABEL="$LABEL" ORG_SIZE="$ORG_SIZE" CHALLENGE="$CHALLENGE" NONCE="$NONCE" python3 -c '
import json, os
print(json.dumps({
    "email": os.environ["EMAIL"],
    "label": os.environ["LABEL"],
    "org_size": os.environ["ORG_SIZE"],
    "license_accepted": True,
    "challenge": os.environ["CHALLENGE"],
    "pow_nonce": os.environ["NONCE"],
    "company_url": "",
}))
')"                                                   # TokenRequestIn; company_url is a honeypot and must stay empty
curl -sS -X POST "${BASE}/api/v1/tokens/request" \
  -H "Content-Type: application/json" \
  -d "${BODY}"                                       # 202 if the email was accepted for sending
echo                                                 # add a trailing newline

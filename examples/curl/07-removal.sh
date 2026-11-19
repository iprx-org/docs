#!/usr/bin/env bash
# Request removal of one IPv4 address: challenge, proof-of-work, POST /api/v1/removals.
# Usage: ./07-removal.sh <ipv4> [reason]
# A successful request returns 201 with status pending_dkim and a one-time token.
# The token is also written to a private local file (600); do not commit or share it.
# Next step: put that token in a DKIM-signed .eml and run ./10-dkim-upload.sh
# Removals are not applied automatically; an operator still decides after DKIM passes.

set -euo pipefail                                    # exit on error, unset variable, or a failed pipe
BASE="${IPRX_BASE:-https://iprx.org}"                # set IPRX_BASE only if you are talking to a different host
IP="${1:-192.0.2.1}"                                 # address to request removal for
REASON="${2:-TEST documentation removal request from the IPRX examples; not a real delist.}"  # at least 8 characters
NAME="${IPRX_NAME:-IPRX examples TEST}"              # set IPRX_NAME to your display name
EMAIL="${IPRX_EMAIL:-docs-test@example.com}"         # set IPRX_EMAIL to an address you control
CH_JSON="$(curl -sS "${BASE}/api/v1/challenge")"     # fetch a fresh one-time challenge
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
')"                                                   # nonce so SHA-256(challenge:nonce) has enough leading zero bits
CHALLENGE="$(CH_JSON="$CH_JSON" python3 -c 'import json,os; print(json.loads(os.environ["CH_JSON"])["challenge"])')"  # extract the opaque string
BODY="$(IP="$IP" REASON="$REASON" NAME="$NAME" EMAIL="$EMAIL" CHALLENGE="$CHALLENGE" NONCE="$NONCE" python3 -c '
import json, os
print(json.dumps({
    "ip": os.environ["IP"],
    "name": os.environ["NAME"],
    "email": os.environ["EMAIL"],
    "reason": os.environ["REASON"],
    "org": "IPRX docs examples",
    "challenge": os.environ["CHALLENGE"],
    "pow_nonce": os.environ["NONCE"],
    "company_url": "",
}))
')"                                                   # RemovalIn JSON; company_url must stay empty
RESP="$(curl -sS -X POST "${BASE}/api/v1/removals" \
  -H "Content-Type: application/json" \
  -d "${BODY}")"                                     # 201 pending_dkim when healthy
echo "${RESP}"                                       # print the JSON (includes a token — keep it private)
# Save the token next to the event_id with mode 600, under $HOME, never in the repo.
python3 -c '
import json, os, pathlib, sys
resp = json.loads(sys.argv[1])
token = resp.get("token")
event_id = resp.get("event_id") or "unknown"
if not token:
    raise SystemExit(0)
path = pathlib.Path.home() / ".iprx" / f"{event_id}.token"
path.parent.mkdir(mode=0o700, exist_ok=True)
path.write_text(token + "\n")
path.chmod(0o600)
print(f"# token saved privately to {path} (mode 600); include it in your DKIM-signed .eml", file=sys.stderr)
' "${RESP}"
echo                                                 # add a trailing newline

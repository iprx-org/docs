#!/usr/bin/env bash
# Ask IPRX to prove a digest on Verae (original first-wins stamp, plus restamp history).
# Usage: ./09-prove.sh [sha256]
# The body may use "digest" or "hash_id". Prove returns only the original stamp.
# If the prover is temporarily down you will still get HTTP 200 with prove.ok=false.

set -euo pipefail                                    # exit on error, unset variable, or a failed pipe
BASE="${IPRX_BASE:-https://iprx.org}"                # set IPRX_BASE only if you are talking to a different host
HASH="${1:-2c7606c0d53d7a800192f11609c939e66826f2af9c93fc971b850a97d5937466}"  # default: 192.0.2.1 add event
curl -sS -X POST "${BASE}/api/v1/prove" \
  -H "Content-Type: application/json" \
  -d "{\"digest\":\"${HASH}\"}"                      # body may use digest or hash_id
echo                                                 # add a trailing newline

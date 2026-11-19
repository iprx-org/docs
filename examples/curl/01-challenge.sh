#!/usr/bin/env bash
# Fetch a SHA-256 proof-of-work challenge used by nomination and removal POSTs.
# Usage: ./01-challenge.sh
# The challenge expires in expires_in seconds (usually 600) and can be used once.

set -euo pipefail                                    # exit on error, unset variable, or a failed pipe
BASE="${IPRX_BASE:-https://iprx.org}"      # set IPRX_BASE to use a different API host
curl -sS "${BASE}/api/v1/challenge"                  # -sS: silent progress, but still show HTTP errors
echo                                                 # add a trailing newline so the JSON is easy to read

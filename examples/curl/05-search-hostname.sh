#!/usr/bin/env bash
# Search public, redacted records by hostname substring, IP, hash_id, ASN, ISP, or country.
# Usage: ./05-search-hostname.sh [query]
# The default query "nt-isp" matches TOT Public Company Limited PTR names in Thailand.

set -euo pipefail                                    # exit on error, unset variable, or a failed pipe
BASE="${IPRX_BASE:-https://iprx.org}"      # set IPRX_BASE to use a different API host
Q="${1:-nt-isp}"                                     # first argument, or a hostname substring
curl -sS -G "${BASE}/api/v1/search" --data-urlencode "q=${Q}"  # --data-urlencode makes punctuation in the query safe
echo                                                 # add a trailing newline

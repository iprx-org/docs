#!/usr/bin/env bash
# Query the conventional DNSBL test entry 127.0.0.2, which should always be listed.
# Usage: ./dnsbl-test-entry.sh [resolver]
# Expected: A 127.0.0.2 and TXT "DNSBL test entry".

set -euo pipefail                                    # exit on error, unset variable, or a failed pipe
RESOLVER="${1:-}"                                    # optional DNS resolver, for example 1.1.1.1
NAME="2.0.0.127.bl.georgelambert.org"                # 127.0.0.2, reversed, under the IPRX zone
DIG=(dig +short)                                     # +short prints only the rdata
if [[ -n "${RESOLVER}" ]]; then                      # the user asked for a specific resolver
  DIG+=(@"${RESOLVER}")                              # dig @1.1.1.1 ...
fi
echo "A   ${NAME}"                                   # show the name we are about to query
"${DIG[@]}" A "${NAME}" || true                      # expect 127.0.0.2
echo "TXT ${NAME}"                                   # the reason text
"${DIG[@]}" TXT "${NAME}" || true                    # expect "DNSBL test entry"

#!/usr/bin/env bash
# Look up one IPv4 address on the live IPRX DNSBL at bl.georgelambert.org.
# Usage: ./dnsbl-check.sh [ipv4] [resolver]
# Reverse the four octets, then query A and TXT under the zone.
# A listed address returns A 127.0.0.2. NXDOMAIN (or no A record) means it is not listed.
# 192.0.2.1 is NOT in the live DNSBL (it is only in the API as a documentation example).
# 43.99.86.230 IS listed: A 127.0.0.2 and TXT "honeypot hits=125157 last=2026-10-17".
# 127.0.0.2 is the conventional test entry: A 127.0.0.2 and TXT "DNSBL test entry".
# If your network intercepts DNS, query a public resolver: ./dnsbl-check.sh 43.99.86.230 1.1.1.1
# You need the dig command (bind9-dnsutils on Debian/Ubuntu, bind-utils on RHEL/Fedora).

set -euo pipefail                                    # exit on error, unset variable, or a failed pipe
IP="${1:-43.99.86.230}"                              # first argument, or a known listed address
RESOLVER="${2:-}"                                    # optional DNS resolver, for example 1.1.1.1
ZONE="bl.georgelambert.org"                          # the live DNSBL zone; change only if you run a mirror
IFS=. read -r A B C D <<< "${IP}"                    # A.B.C.D -> four octets
REV="${D}.${C}.${B}.${A}.${ZONE}"                    # DNSBL name is reversed octets plus the zone
DIG=(dig +short)                                     # +short prints only the rdata
if [[ -n "${RESOLVER}" ]]; then                      # the user asked for a specific resolver
  DIG+=(@"${RESOLVER}")                              # dig @1.1.1.1 ...
fi
echo "A   ${REV}"                                    # show the name we are about to query
"${DIG[@]}" A "${REV}" || true                       # an NXDOMAIN exits non-zero with +short on some builds
echo "TXT ${REV}"                                    # the TXT record carries a short reason when present
"${DIG[@]}" TXT "${REV}" || true                     # no TXT is normal for an unlisted address

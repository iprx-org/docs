#!/usr/bin/env bash
# Check whether one IPv4 address is listed, and why.
# Usage: ./02-check.sh [ipv4]
# Default is 192.0.2.1 (RFC 5737 TEST-NET-1), which the API lists as a documentation example.

set -euo pipefail                                    # exit on error, unset variable, or a failed pipe
BASE="${IPRX_BASE:-https://iprx.org}"      # set IPRX_BASE to use a different API host
IP="${1:-192.0.2.1}"                                 # first argument, or the TEST-NET-1 documentation address
curl -sS "${BASE}/api/v1/check/${IP}"                # GET /api/v1/check/{ip}
echo                                                 # add a trailing newline

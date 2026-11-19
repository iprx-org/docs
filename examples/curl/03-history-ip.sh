#!/usr/bin/env bash
# Fetch the event history for one IPv4 address, including Verae receipts.
# Usage: ./03-history-ip.sh [ipv4]
# Pass include_restamps=false if you only want the original first-wins stamp on each event.

set -euo pipefail                                    # exit on error, unset variable, or a failed pipe
BASE="${IPRX_BASE:-https://iprx.org}"      # set IPRX_BASE to use a different API host
IP="${1:-192.0.2.1}"                                 # first argument, or the TEST-NET-1 documentation address
curl -sS "${BASE}/api/v1/history/${IP}"              # GET /api/v1/history/{ip}
echo                                                 # add a trailing newline

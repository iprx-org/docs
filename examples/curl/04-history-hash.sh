#!/usr/bin/env bash
# Fetch history for one event by its 64-character hash_id (SHA-256 of the stamped payload).
# Usage: ./04-history-hash.sh [hash_id]
# You can also pass an event_id such as blv1-f4efb616fc62597c.

set -euo pipefail                                    # exit on error, unset variable, or a failed pipe
BASE="${IPRX_BASE:-https://iprx.org}"      # set IPRX_BASE to use a different API host
HASH="${1:-2c7606c0d53d7a800192f11609c939e66826f2af9c93fc971b850a97d5937466}"  # default: the 192.0.2.1 add event
curl -sS "${BASE}/api/v1/history/${HASH}"            # GET /api/v1/history/{hash_id}
echo                                                 # add a trailing newline

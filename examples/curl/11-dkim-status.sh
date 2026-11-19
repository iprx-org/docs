#!/usr/bin/env bash
# Check the DKIM verification status of a removal request.
# Usage: ./11-dkim-status.sh <event_id>
# Returns dkim_status (pending, passed, failed) and any recorded domain/selector.

set -euo pipefail                                    # exit on error, unset variable, or a failed pipe
BASE="${IPRX_BASE:-https://iprx.org}"                # set IPRX_BASE only if you are talking to a different host
EVENT_ID="${1:?pass a removal event_id, for example blv2-0123456789abcdef}"  # from the removal response
curl -sS "${BASE}/api/v1/removals/${EVENT_ID}/dkim-status"  # GET the status document
echo                                                 # add a trailing newline

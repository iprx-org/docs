#!/usr/bin/env bash
# Upload a DKIM-signed .eml to prove domain control for a removal request.
# Usage: ./10-dkim-upload.sh <event_id> <message.eml>
# The .eml must be a raw RFC822 message, DKIM-signed by the PTR host's registrable
# domain or the RDAP/WHOIS org/abuse-contact domain, and must contain the one-time
# token from POST /api/v1/removals in the subject or body.
# This script only uploads a local file; it does not send any email.
# A failed check is recorded and stamped; the request does not advance until a check passes.
# After a pass, the request still waits for an operator decision.

set -euo pipefail                                    # exit on error, unset variable, or a failed pipe
BASE="${IPRX_BASE:-https://iprx.org}"                # set IPRX_BASE only if you are talking to a different host
EVENT_ID="${1:?pass a removal event_id, for example blv2-0123456789abcdef}"  # from the removal response
EML="${2:?pass a path to a raw RFC822 .eml file}"    # local file; we never send mail for you
test -s "${EML}"                                     # the file must exist and not be empty
curl -sS -X POST "${BASE}/api/v1/removals/${EVENT_ID}/dkim" \
  -H "Accept: application/json" \
  -F "eml=@${EML};type=message/rfc822"               # multipart field name is eml
echo                                                 # add a trailing newline

#!/usr/bin/env bash
# Download one event receipt as JSON, HTML, and PDF, plus the whole-IP receipt bundle.
# Usage: ./08-receipts.sh [hash_id_or_event_id] [ipv4]
# Equivalent forms: /api/v1/receipts/{id}.json, ?format=json, or an Accept header.
# Short URLs also work: https://iprx.org/r/{hash_id}.pdf

set -euo pipefail                                    # exit on error, unset variable, or a failed pipe
BASE="${IPRX_BASE:-https://iprx.org}"                # set IPRX_BASE only if you are talking to a different host
KEY="${1:-2c7606c0d53d7a800192f11609c939e66826f2af9c93fc971b850a97d5937466}"  # default: 192.0.2.1 add event
IP="${2:-192.0.2.1}"                                 # address whose whole-IP bundle we also fetch
mkdir -p /tmp/iprx-receipts                          # create a local folder for the three formats
curl -sS "${BASE}/api/v1/receipts/${KEY}.json" -o /tmp/iprx-receipts/receipt.json   # canonical JSON (has canonical_sha256)
curl -sS "${BASE}/api/v1/receipts/${KEY}.html" -o /tmp/iprx-receipts/receipt.html   # printable HTML with a verify QR code
curl -sS "${BASE}/api/v1/receipts/${KEY}.pdf"  -o /tmp/iprx-receipts/receipt.pdf    # the same content as a PDF
curl -sS "${BASE}/api/v1/receipts/ip/${IP}.json" -o /tmp/iprx-receipts/bundle.json  # all events for that IP
ls -l /tmp/iprx-receipts                             # show the downloaded files and their sizes

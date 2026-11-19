#!/usr/bin/env bash
# Nominate every public IPv4 address in a local block file via the IPRX API.
# Usage:
#   ./submit-blockfile.sh --dry-run ../samples/fail2ban.log
#   ./submit-blockfile.sh --limit 3 --email you@example.org --name "Your Name" bans.txt
#
# This bash entry point runs the documented Python submitter so every supported
# format is parsed the same way: fail2ban status/banned/log, plain IP and CIDR
# lists, CSV with ip,reason, ipset save, iptables-save, nftables sets, CrowdSec
# `cscli decisions list -o json`, hosts.deny, Apache/nginx deny rules, and
# Spamhaus DROP-style `ip ; comment` lines.
#
# Flags (passed through unchanged):
#   --dry-run                 parse and print, do not call the API
#   --limit N                 nominate at most N eligible addresses
#   --reason TEXT             default reason when the file has none
#   --email / --name / --org  your identity (required for a live submit)
#   --token TOKEN             verified API token (or set IPRX_TOKEN); skips PoW, no rate limit
#   --delay SECONDS           pause between live posts (default 1 without a token, 0 with a token)
#   --output FILE             append per-IP results JSONL (event_id, receipt_url)
#   --format auto|...         force a parser; auto is the default
#   --max-cidr-size 256       refuse to expand a prefix larger than this
#   --submit-documentation    TEST ONLY: also POST RFC 5737 TEST-NET addresses
#                             (the API rejects them with HTTP 400)
#   --base URL                default https://iprx.org
#
# Private, reserved, loopback, and documentation addresses are skipped.
# Duplicates are dropped. Anonymous posts are capped at 10 nominations per hour
# and must solve a proof-of-work; the script honours HTTP 429. With --token or
# IPRX_TOKEN there is no nomination rate limit and the proof-of-work is skipped.
# One submitter email counts as one nominator toward the 5-distinct-nominator
# listing threshold, no matter how many IPs are in the file.

set -euo pipefail                                    # exit on error, unset variable, or a failed pipe
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" # directory of this script, so we can find ../python
PY="${HERE}/../python/submit_blockfile.py"           # the reference submitter (every line is commented)
if [[ ! -f "${PY}" ]]; then                          # the tree is incomplete
  echo "cannot find ${PY}" >&2                       # tell the user where we looked
  exit 1                                             # stop
fi
exec python3 "${PY}" "$@"                            # replace this process; all flags are documented above

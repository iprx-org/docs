# IPRX request examples

This directory holds small, copy-and-run examples for the live [IPRX](https://iprx.org) API and the DNSBL at `bl.georgelambert.org`. Every script has a comment on every line so you can see what each command does and how to change it. Each language folder also has a `requests.jsonl` file: one JSON object per line, describing one request.

The public API origin used here is **https://iprx.org**. The same API is also served at https://blocklist.iprx.org. Set `IPRX_BASE` if you need to point the scripts somewhere else.

A longer explanation of why the scripts are documented this way, how the JSONL layout works, and how to verify each file's Verae receipt is in [scripts.md](../scripts.md).

## Languages

| Folder | How to run | What it covers |
| --- | --- | --- |
| [curl/](curl/) | `./02-check.sh 192.0.2.1` | bash + curl for every public endpoint, plus the bulk submitter |
| [python/](python/) | `python3 check.py 192.0.2.1` | the same endpoints, plus the reference bulk submitter |
| [javascript/](javascript/) | `node check.mjs 192.0.2.1` | Node 18+ (`fetch` is built in) |
| [go/](go/) | `go run check.go 192.0.2.1` | standard library only (except the bulk wrapper, which calls Python) |
| [dig/](dig/) | `./dnsbl-check.sh 43.99.86.230` | DNSBL A and TXT lookups |
| [rust/](rust/) | `cargo run -- 192.0.2.1` | optional extra (`ureq`) |
| [powershell/](powershell/) | `pwsh Check.ps1` | optional extra |

## Endpoints covered

| Action | Method | Path | Notes |
| --- | --- | --- | --- |
| Proof-of-work challenge | `GET` | `/api/v1/challenge` | required before a nomination or removal POST |
| Check an IPv4 address | `GET` | `/api/v1/check/{ip}` | includes `nomination_progress` (for example `3/5`) |
| History by IP | `GET` | `/api/v1/history/{ip}` | public views redact requestor contact |
| History by hash_id | `GET` | `/api/v1/history/{hash_id}` | 64-character SHA-256 of the stamped payload |
| Search by hostname (public) | `GET` | `/api/v1/search?q=` | also matches IP, hash_id, ASN, ISP, country |
| Request an API token | `POST` | `/api/v1/tokens/request` | emails a one-click link; first-time users accept the license and pick an org size |
| Nominate an address | `POST` | `/api/v1/nominations` | challenge + proof-of-work, or `Authorization: Bearer <token>` |
| Request a removal | `POST` | `/api/v1/removals` | returns `pending_dkim` and a one-time token |
| Upload a DKIM-signed .eml | `POST` | `/api/v1/removals/{event_id}/dkim` | uploads a **local** file; the examples never send email |
| DKIM status | `GET` | `/api/v1/removals/{event_id}/dkim-status` | `pending`, `passed`, or `failed` |
| Download a receipt | `GET` | `/api/v1/receipts/{id}.json\|html\|pdf` | also `https://iprx.org/r/{hash_id}.pdf` |
| Whole-IP receipt bundle | `GET` | `/api/v1/receipts/ip/{ip}.json\|html\|pdf` | every event for that address |
| Prove a digest | `POST` | `/api/v1/prove` | original first-wins stamp; restamp history is attached |
| DNSBL lookup | DNS | `{rev}.bl.georgelambert.org` A / TXT | listed addresses return `A 127.0.0.2` |

Interactive OpenAPI: [https://iprx.org/docs](https://iprx.org/docs).

## Proof-of-work, tokens, honeypot, and the 5-nominator rule

Request a token with `./curl/12-token-request.sh` or `python3 python/token_request.py` (set `IPRX_EMAIL`). A one-click email is sent; opening the link shows the token once. The same email can hold several labeled tokens. Send `Authorization: Bearer <token>` (or set `IPRX_TOKEN` / `--token` on the scripts) to skip the proof-of-work. Verified-token nominations have **no rate limit**. Anonymous web submissions still have a honeypot, a SHA-256 proof-of-work, and a cap of 10 nominations and 10 removal requests per hour per client.

Before an anonymous `POST /api/v1/nominations` or `POST /api/v1/removals`, fetch a challenge and find a `pow_nonce` so that SHA-256 of `challenge` + `:` + `pow_nonce` has at least `bits` leading zero bits (usually 18). Challenges expire and cannot be reused. Leave `company_url` empty; any non-empty value is rejected.

An address is listed automatically only after **5 distinct verified nominators**. Distinctness is counted by verified email and by the client IP the API sees. Several tokens on one email still count as one nominator. A bulk file from one person still counts as **one nominator** for each IP in the file, not one nominator per line. Removals are never automatic: DKIM must pass, and an operator still decides.

## Bulk submitters

Point a submitter at a local block file:

```bash
python3 python/submit_blockfile.py --dry-run samples/fail2ban.log
./curl/submit-blockfile.sh --dry-run samples/fail2ban.log
node javascript/submit_blockfile.mjs --dry-run samples/fail2ban.log
go run go/submit_blockfile.go --dry-run ../samples/fail2ban.log   # run from go/
# live, with a verified token (skips the proof-of-work, no nomination rate limit):
IPRX_TOKEN=iprx_… python3 python/submit_blockfile.py --email you@example.org --name "Your Name" bans.txt
```

The Python script is the reference parser (every line is commented). The bash, JavaScript, and Go entry points run that same script so the formats stay in lockstep.

Supported formats, with samples in [samples/](samples/):

- `fail2ban-client status <jail>` text, `fail2ban-client banned` JSON, and `Ban x.x.x.x` log lines
- plain IPv4 lists and CIDR lists (prefixes larger than `/24` are skipped unless you raise `--max-cidr-size`)
- CSV with `ip,reason`
- `ipset save`, `iptables-save`, nftables set dumps
- CrowdSec `cscli decisions list -o json`
- `/etc/hosts.deny` / DenyHosts
- Apache `Require not ip` / `Deny from` and nginx `deny` directives
- Spamhaus DROP-style `ip ; comment` lines

The submitters skip private, reserved, loopback, and documentation (RFC 5737 TEST-NET) addresses, and they de-duplicate. `--dry-run` only prints what would be sent. `--limit` caps a live run. Results are appended as JSONL (`event_id`, `receipt_url`). `--submit-documentation` is a test-only flag that will POST TEST-NET addresses so you can see the API's HTTP 400; leave it off for real use.

With a verified token the bulk submitter does not need a challenge per IP and is not capped at 10/hour. Anonymous runs still pace themselves and honour HTTP 429.

## DKIM for removal requests

A removal request is recorded and stamped, then waits in `pending_dkim`. The response includes a one-time token. Put that token in the subject or body of a message that is DKIM-signed by the PTR host's registrable domain, or by the RDAP/WHOIS organisation or abuse-contact domain. Save the delivered message as a raw `.eml` and upload it with `10-dkim-upload.sh` (or the Python / JavaScript / Go equivalent). The examples only upload a local file; **they never send email**.

The token is written to `~/.iprx/<event_id>.token` with mode 600. Do not commit it. [samples/removal-proof.eml](samples/removal-proof.eml) is a template only — it is not signed.

A failed DKIM check is recorded and stamped; the request does not advance until a check passes. After a pass, an operator still decides.

## Sample IPs used in the examples

- `192.0.2.1` / `192.0.2.10` — RFC 5737 TEST-NET-1. The API lists `192.0.2.1` as a documentation example (`nomination_progress` `0/5`). It is **not** in the live DNSBL. Nominating TEST-NET addresses returns HTTP 400.
- `43.99.86.230` — a live listed honeypot address (`nomination_progress` `0/5`, DNSBL `A 127.0.0.2`).
- hash_id `2c7606c0d53d7a800192f11609c939e66826f2af9c93fc971b850a97d5937466` — the `192.0.2.1` add event.
- Search query `nt-isp` — TOT Public Company Limited PTR names in Thailand (15 matches when these examples were tested).

The [samples/](samples/) block files use only TEST-NET and a few private addresses, so a dry-run shows them being skipped.

## Receipts for these files

Every file in this directory (and [scripts.md](../scripts.md) plus the updated docs [README.md](../README.md)) has a Verae-timestamped receipt:

- JSON: [receipts/](receipts/)`<path>.receipt.json`
- PDF: [receipts/](receipts/)`<path>.receipt.pdf`
- Manifest: [receipts/MANIFEST.json](receipts/MANIFEST.json) (also stamped)

To verify a file:

1. Compute its SHA-256 (`sha256sum path` or `shasum -a 256 path`).
2. Compare that digest to the `sha256` field in the matching receipt JSON.
3. Check the receipt's Merkle proof against the block root on Verae.
4. Confirm the GitHub raw file (after it is published) has the same digest.

See [Nothing Up Our Sleeves](../nothing-up-our-sleeves.md) and [scripts.md](../scripts.md#how-to-verify-a-files-receipt).

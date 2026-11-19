# IPRX API

The blocklist API is live at:

- [https://blocklist.iprx.org/api/v1/](https://blocklist.iprx.org/api/v1/)
- [https://iprx.org/api/v1/](https://iprx.org/api/v1/) (the same API)

Interactive OpenAPI documentation: [https://blocklist.iprx.org/docs](https://blocklist.iprx.org/docs) (also at [https://iprx.org/docs](https://iprx.org/docs)).

The public site — About, Check, Nominate, Remove, History, and API tokens — is the homepage at [https://iprx.org/](https://iprx.org/). The same application also runs at [https://blocklist.iprx.org/](https://blocklist.iprx.org/).

Nominations and removal requests are stamped on Verae. An address is listed automatically after 5 distinct **verified** nominations (unique verified email and unique source IP). Removals still need a passing DKIM check and then admin approval. Public responses never include a requestor's email or other contact details. Private, reserved, and documentation addresses are rejected for listing. Rate limits apply. Public forms and the unauthenticated nomination/removal API use a honeypot field plus a SHA-256 proof-of-work. A one-click confirmation email is sent when you request an API token, ask to manage tokens, or nominate without a token. Scripts that send `Authorization: Bearer <token>` skip the proof-of-work.

## Endpoints

| Method | Path | Status | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/challenge` | Live | Issue a SHA-256 proof-of-work challenge for submissions |
| `POST` | `/api/v1/nominations` | Live | Nominate an IPv4 address for listing |
| `GET` | `/api/v1/nominations/confirm/{magic}` | Live | Confirm a nomination from a one-click email link |
| `POST` | `/api/v1/removals` | Live | Request removal of a listed address |
| `POST` | `/api/v1/tokens/request` | Live | Email a one-click link that issues an API token |
| `GET` | `/api/v1/tokens/confirm/{magic}` | Live | Verify the email and return the API token (JSON or HTML) |
| `POST` | `/api/v1/tokens/manage` | Live | Email a one-click link to the “my tokens” page |
| `GET` | `/api/v1/tokens/manage/{magic}` | Live | List tokens for that email (magic link; no email shown) |
| `GET` | `/api/v1/tokens` | Live | List tokens for the authenticated email (`Authorization: Bearer`) |
| `POST` | `/api/v1/tokens` | Live | Issue another token for the same email (`Bearer` or manage magic) |
| `DELETE` | `/api/v1/tokens/{token_id}` | Live | Revoke a token (`Bearer` or manage magic) |
| `GET` | `/api/v1/check/{ip}` | Live | Current listing status for one IPv4 address |
| `GET` | `/api/v1/history/{ip\|hash_id}` | Live | Event history for an address or a `hash_id` |
| `GET` | `/api/v1/search?q=` | Live | Redacted search by IP, `hash_id`, hostname, ASN, ISP, or country |
| `POST` | `/api/v1/prove` | Live | Prove a digest (original stamp) and attach restamp history |
| `GET` | `/api/v1/receipts/{event_id\|hash_id}.json\|.html\|.pdf` | Live | Download one receipt as JSON, HTML, or PDF |
| `GET` | `/api/v1/receipts/ip/{ip}.json\|.html\|.pdf` | Live | Download the whole-IP history bundle in the same formats |

`{ip}` is a dotted IPv4 address. `{hash_id}` is the 64-character lowercase hex SHA-256 of the stamped event payload (with or without a `sha256:` prefix). `{event_id}` looks like `blv2-` or `blv1-` followed by the first 16 hex characters of that digest. See [records and receipts](records-and-receipts.md).

Short verify URLs (used in receipt QR codes) are also live:

- `https://iprx.org/r/{hash_id}.html` (or `.json` / `.pdf`)
- `https://iprx.org/r/ip/{ip}.html` (or `.json` / `.pdf`) for a whole-IP bundle

Downloadable blocklist feeds and stamped GitHub manifests are still [planned](file-formats.md#planned). They will be published only after the lists are confirmed reliable.

## Proof-of-work and the honeypot field

Before `POST /api/v1/nominations` or `POST /api/v1/removals`, fetch a challenge:

```bash
curl -sS https://blocklist.iprx.org/api/v1/challenge
```

```json
{
  "challenge": "opaque-challenge-string",
  "bits": 18,
  "expires_in": 600
}
```

Include that `challenge` and a `pow_nonce` in the submission body. Choose a nonce so that the SHA-256 of `challenge` + `:` + `pow_nonce` has at least `bits` leading zero bits. Challenges expire after `expires_in` seconds and cannot be reused.

Leave `company_url` empty or omit it. That field is a honeypot; any non-empty value is rejected.

The web forms at [Nominate](https://blocklist.iprx.org/nominate) and [Remove](https://blocklist.iprx.org/remove) do this automatically.

## API tokens and email confirmation

Request a token:

```bash
# 1. Get a proof-of-work challenge
curl -sS https://iprx.org/api/v1/challenge
# 2. Solve it (SHA-256 of challenge + ":" + nonce has `bits` leading zero bits)
# 3. Ask for a one-click email
curl -sS -X POST https://iprx.org/api/v1/tokens/request \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","label":"fail2ban-server","challenge":"...","pow_nonce":"...","company_url":""}'
```

The response is `202` and does not include the link. The email is sent from `veraetimestamp@gmail.com`, subject `IPRX: confirm your email`. The link expires in 30 minutes. Opening it verifies the address and issues an API token, shown on an HTML page with a copy button.

JSON for the same confirmation (the token is in the body, shown only this once):

```
GET /t/confirm/{magic}
GET /t/confirm/{magic}.json
GET /api/v1/tokens/confirm/{magic}
GET /api/v1/tokens/confirm/{magic}.json
```

Use `Accept: application/json` or `?format=json` if there is no `.json` suffix. Typical JSON:

```json
{
  "status": "issued",
  "token": "iprx_…",
  "token_id": "tok-…",
  "prefix": "iprx_XXXXXXXX…",
  "label": "fail2ban-server",
  "authorization": "Bearer iprx_…",
  "issue_event_id": "blv2-…",
  "verification_event_id": "blv2-…"
}
```

Use the token:

```bash
curl -sS -X POST https://iprx.org/api/v1/nominations \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer iprx_…' \
  -d '{"ip":"203.0.113.10","reason":"Why this address should be listed.","email":"you@example.com"}'
```

A Bearer token skips the proof-of-work. A per-token rate limit applies (default 60 requests per hour). The email on the token is the verified identity; several tokens on the same email still count as one nominator toward the 5-person rule.

List, issue another, and revoke (auth by any unrevoked token for that email):

```bash
curl -sS https://iprx.org/api/v1/tokens -H 'Authorization: Bearer iprx_…'
curl -sS -X POST https://iprx.org/api/v1/tokens -H 'Authorization: Bearer iprx_…' \
  -H 'Content-Type: application/json' -d '{"label":"second server"}'
curl -sS -X DELETE https://iprx.org/api/v1/tokens/tok-… -H 'Authorization: Bearer iprx_…'
```

`POST /api/v1/tokens/manage` (honeypot + proof-of-work, same shape as `/tokens/request`) emails a fresh magic link to `GET /t/manage/{magic}` (also `GET /api/v1/tokens/manage/{magic}`). That page lists prefixes and labels only — not the email, and not the secret. The manage link works until it expires (30 minutes) and can also be sent as `X-IPRX-Magic` to `GET`/`POST`/`DELETE /api/v1/tokens`.

Token issue and email verification are stamped on Verae as `token_issue` and `email_verified` events. The stamped payload contains `email_hash` and `token_hash` only — never the email or the token in plaintext. Public history redacts email addresses.

## Nominate an address — `POST /api/v1/nominations`

Submit a request to list an IPv4 address. The request is recorded, hashed, and stamped. If you send `Authorization: Bearer <token>`, the nomination is already verified and its status is `pending` (or `listed` if this was the fifth distinct verified nominator). Without a token, status is `pending_verification` and a one-click confirmation email is sent; the nomination does not count toward the 5-person rule until the link is opened (`GET /t/nominate/{magic}` or `GET /api/v1/nominations/confirm/{magic}`). Success is `201`.

```json
{
  "ip": "192.0.2.1",
  "reason": "Human-readable explanation of why this address should be listed.",
  "evidence": "Optional supporting detail",
  "name": "Display Name",
  "email": "you@example.com",
  "org": "Optional organization",
  "challenge": "from GET /api/v1/challenge",
  "pow_nonce": "proof-of-work nonce",
  "company_url": ""
}
```

`ip`, `reason`, and `email` are required. `challenge` and `pow_nonce` are required unless you send `Authorization: Bearer <token>`. `reason` must be at least 8 characters. The documentation address `192.0.2.1` in this example would be rejected; private, reserved, and documentation addresses cannot be nominated.

Expected success response (contact details omitted):

```json
{
  "status": "pending",
  "event_id": "blv2-0123456789abcdef",
  "hash_id": "64-hex-sha256-of-the-canonical-event",
  "ip": "203.0.113.10",
  "message": "Nomination recorded and stamped. Distinct verified nominations: 1/5.",
  "receipt": {
    "batch_id": null
  }
}
```

`receipt` fields are filled after the digest is sealed on chain.

## Request a removal — `POST /api/v1/removals`

Submit a request to delist an IPv4 address. Same DKIM-then-admin-approval rule, honeypot field, and proof-of-work (the proof-of-work is skipped when `Authorization: Bearer <token>` is present). Use this path rather than a plain email for delisting; see [SECURITY.md](SECURITY.md). Success is `201`.

```json
{
  "ip": "192.0.2.1",
  "name": "Display Name",
  "email": "you@example.com",
  "reason": "Human-readable explanation of why this address should be removed.",
  "org": "Optional organization",
  "challenge": "from GET /api/v1/challenge",
  "pow_nonce": "proof-of-work nonce",
  "company_url": ""
}
```

`ip`, `name`, `email`, and `reason` are required. `challenge` and `pow_nonce` are required unless you send a Bearer token. Expected success response is a removal request with status `pending_dkim` and a one-time DKIM token.

An approved decision is later applied to the DNSBL (within the 5-minute rebuild) and, once feeds are published, to the next membership-changing feed build. Delist rows are sticky; new honeypot activity after a removal is reported, not auto-relisted.

## Check an address — `GET /api/v1/check/{ip}`

Returns the current status of one IPv4 address. The same check is on the [Check](https://blocklist.iprx.org/check) page.

```bash
curl -sS https://blocklist.iprx.org/api/v1/check/192.0.2.1
# or: curl -sS https://iprx.org/api/v1/check/192.0.2.1
```

```json
{
  "ip": "192.0.2.1",
  "listed": true,
  "status": "listed",
  "reason_summary": "RFC 5737 TEST-NET-1 address injected only into the local simulation feed.",
  "reason_code": "TEST_DOCUMENTATION",
  "event_time": "2026-11-19T02:36:58Z",
  "hash_id": "64-hex-sha256",
  "asn": null,
  "isp_org": null,
  "country": null,
  "prefix": null,
  "ptr_status": "no_ptr",
  "dnsbl": "1.2.0.192.bl.georgelambert.org"
}
```

`status` is `listed`, `delisted`, or `not_listed` (never seen). Missing PTR or ISP fields are `null`, or `ptr_status` is one of `no_ptr`, `lookup_failed`, `confirmed`, or `unconfirmed` — names are never guessed. This endpoint does not return requestor contact details. You can also query the [DNSBL](usage.md#dns-blocklist).

## History — `GET /api/v1/history/{ip|hash_id}`

Returns the timeline of events for an IP, or the event (and its restamp history, if any) for a `hash_id`. Pass `include_restamps=true` (the default) to attach restamp history to each event. The [History](https://blocklist.iprx.org/history) page offers the same lookup.

```bash
curl -sS https://blocklist.iprx.org/api/v1/history/192.0.2.1
curl -sS https://blocklist.iprx.org/api/v1/history/0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

Each event includes `action`, `status`, `reason_code`, `reason`, `event_time`, `hash_id`, `event_id`, network snapshot when present, and a receipt (`batch_id`, `block_hash`, `root`, `original_ts`, `restamp`, `verify_url`, `proof_ok`). Requestor email and other contact fields are omitted from the public response.

The original first-wins stamp is always listed first and is never replaced. Later `restamp` entries appear as additional items. See [records and receipts](records-and-receipts.md).

`GET /api/v1/search?q=` is a redacted search over the same records. The query may be an IP, a `hash_id` (full or prefix), a hostname substring, an ASN, an ISP or organization name, or a country code. Add `format=csv` for a CSV download. To download a receipt file, use [the receipt endpoints](#download-a-receipt).

## Prove a digest — `POST /api/v1/prove`

Looks up the original Verae stamp for a digest and attaches any restamp history. The prove result is the first-wins stamp only; restamps are a separate timeline.

```bash
curl -sS -X POST https://blocklist.iprx.org/api/v1/prove \
  -H 'Content-Type: application/json' \
  -d '{"digest":"64-hex-sha256"}'
```

The body may use `digest` or `hash_id`. You can also prove a digest directly on Verae, as in [usage](usage.md#verify-a-verae-receipt).

## Download a receipt

Receipts are downloadable as:

- **JSON** — the canonical receipt document, including `canonical_sha256`
- **HTML** — a printable page
- **PDF** — the same content as a document

```
GET /api/v1/receipts/{event_id|hash_id}.json
GET /api/v1/receipts/{event_id|hash_id}.html
GET /api/v1/receipts/{event_id|hash_id}.pdf
```

You can also ask for a format with `?format=` or an `Accept` header. All three ways are equivalent:

```bash
# Suffix (preferred)
curl -sS https://blocklist.iprx.org/api/v1/receipts/blv2-0123456789abcdef.json
curl -sS https://blocklist.iprx.org/api/v1/receipts/blv2-0123456789abcdef.html
curl -sS https://blocklist.iprx.org/api/v1/receipts/blv2-0123456789abcdef.pdf -o receipt.pdf

# Query parameter
curl -sS "https://blocklist.iprx.org/api/v1/receipts/blv2-0123456789abcdef?format=json"

# Accept header
curl -sS -H "Accept: application/json" https://blocklist.iprx.org/api/v1/receipts/blv2-0123456789abcdef

# Short URL
curl -sS https://iprx.org/r/HASH_ID.html
curl -sS https://iprx.org/r/HASH_ID.json
curl -sS https://iprx.org/r/HASH_ID.pdf -o receipt.pdf
```

If more than one selector is present, the suffix wins, then `format=`, then `Accept`. The default when none is given is JSON (`Content-Type: application/json`). HTML is `text/html; charset=utf-8`. PDF is `application/pdf`.

The JSON body is a canonical receipt document (`format` `iprx.org/receipt/v1`): UTF-8, sorted keys, no extra whitespace. It includes `canonical_sha256`, which is the SHA-256 of that same JSON **without** the `canonical_sha256` field itself. The event's stamped digest remains `hash_id` (see [records and receipts](records-and-receipts.md#hash_id)).

The document also includes the IP, hostnames/PTR, ASN/ISP, action, reason, event time, `event_id`, `previous_event_id`, the Verae stamp (job/batch, block number and hash, merkle root, certificate id, merkle siblings when present), original-vs-restamp sequence, a verify URL, and a QR code on the HTML and PDF pointing at `https://iprx.org/r/{hash_id}`. Public downloads omit requestor contact details. Missing fields are `null` or shown as “unknown”.

## Download an IP receipt bundle

The full history of one IP — original first-wins event, later adds/removes, and every restamp — is also downloadable in all three formats.

```
GET /api/v1/receipts/ip/{ip}.json
GET /api/v1/receipts/ip/{ip}.html
GET /api/v1/receipts/ip/{ip}.pdf
```

`?format=` and `Accept` work the same way as for a single receipt. Short URLs: `https://iprx.org/r/ip/{ip}.html` (or `.json` / `.pdf`).

```bash
curl -sS https://blocklist.iprx.org/api/v1/receipts/ip/192.0.2.1.json
curl -sS https://blocklist.iprx.org/api/v1/receipts/ip/192.0.2.1.html
curl -sS https://blocklist.iprx.org/api/v1/receipts/ip/192.0.2.1.pdf -o history.pdf
```

The JSON bundle has `format` `iprx.org/receipt-bundle/v1`, an `ip`, an `event_count`, a `receipts` array, and `canonical_sha256` of that document without the `canonical_sha256` field. HTML and PDF are printable timelines of the same records, again without requestor contact details, with a verify QR.

The [Check](https://blocklist.iprx.org/check) and [History](https://blocklist.iprx.org/history) pages also offer JSON, HTML, and PDF download buttons.

## Errors

Expect standard HTTP status codes: `400` for a bad IP, missing or invalid proof-of-work, a honeypot trip, or a reserved address that cannot be nominated; `404` for an unknown id; `422` for a schema validation error; and `429` for a rate limit. Error bodies are JSON, typically `{"detail": "…"}`.

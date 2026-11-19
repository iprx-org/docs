# Records and receipts

Every IPRX listing change is stored as a structured event, hashed, and (once stamped) given a receipt on [Verae's chain](verae.md). The chain stores only the hash, not the event body. This page is the schema those events use. It is taken from the IPRX event-record code (`format` `iprx.org/block-event/v2`). A standalone `EVENT_RECORDS.md` file does not exist yet; this document is the public description.

## Actions and status

Actions: `add`, `remove`, `restamp`, `nominate`, `removal_request`, `decision`.

Default `status` values:

| Action | Default status |
| --- | --- |
| `nominate`, `removal_request` | `pending` |
| `add` | `listed` |
| `remove` | `delisted` |
| `decision` | the decision value, or `decided` |
| `restamp` | `recorded` |

Nominations and removal requests stay pending until an operator decides. Nothing auto-lists or auto-delists.

## Event document (v2)

```json
{
  "format": "iprx.org/block-event/v2",
  "event_id": "blv2-0123456789abcdef",
  "ip": "192.0.2.1",
  "cidr": null,
  "hostnames": ["mail.example.com"],
  "action": "add",
  "status": "listed",
  "reason_code": "HONEYPOT_HIT",
  "reason": "Listed after 2 observed hits on honeypot or ban logs; first_seen=… last_seen=….",
  "source": "honeypot",
  "actor": null,
  "event_time": "2026-11-19T02:36:59Z",
  "previous_event_id": null,
  "detail": {},
  "network": {},
  "requestor": {}
}
```

`event_time` is UTC, `YYYY-MM-DDTHH:MM:SSZ`. `previous_event_id` links a later event (a removal, restamp, or decision) to the earlier one for that IP. `detail` holds request- and decision-specific fields (`request_id`, `requestor_name`, `decision`, `decided_by`, `justification`, and similar). Missing source data is left null or omitted; it is never invented. A hostname that could not be looked up is not guessed.

Older backfilled events use `format` `bl.georgelambert.org/block-event/v1` and `event_id` `blv1-` plus 16 hex characters. Those events keep the digest they were already stamped with. They are not restamped. PTR and ASN data added later for a v1 event live under `enrichment` and are **not** part of that `hash_id`.

JSONL is the source of truth for the event log. A search index is derived from it.

## Why something was added or removed

Every `add` and `remove` carries:

- `reason_code` — for honeypot listings, `HONEYPOT_HIT`; for optional coarse `/24`s in the feed, `DENSE_PREFIX`; other codes may appear on nominations and decisions
- `reason` — human text (hit counts, source, first/last seen, or the requestor's explanation)
- `source` and optional `actor`
- `event_time`
- optional `requestor` (name, email, org) on nominations and removal requests
- a `network` snapshot when the lookup has been done

Public pages and public API responses omit requestor contact details. Operators see them on the pending queue.

## Network snapshot (PTR / ASN / ISP)

Lookups use reverse DNS and ISP/registry data. The `network` object on a new v2 event (included in that event's hash when present) has this shape:

| Field | Meaning |
| --- | --- |
| `hostnames` / `ptr` | PTR names, if any |
| `ptr_status` | `confirmed`, `unconfirmed`, `no_ptr`, or `lookup_failed` |
| `ptr_forward_confirmed` | Whether a forward lookup of the PTR returned the same IP |
| `asn` | Autonomous system number, or null |
| `as_name` | AS name, or null |
| `isp_org` | ISP or organization name, or null |
| `country` | Country code, or null |
| `prefix` | Announced or registered prefix, or null |
| `registry`, `allocated` | Registry fields when known |
| `lookup_time` | When the lookup was done |
| `lookup_source` | `+`-joined sources, or `unknown` |

`ptr_status` `no_ptr` means the reverse lookup returned no hostname. Names are never synthesized.

## hash_id

`hash_id` is the SHA-256 (lowercase hex) of the **canonical stamped payload**. That digest is what is submitted to Verae. A `record_hash` field of the form `sha256:<hex>` is stored next to it and is not itself hashed.

Canonical form:

- UTF-8 JSON
- `sort_keys=True`
- `separators=(",", ":")` (no extra whitespace)
- `ensure_ascii=False`

Fields always **omitted** from the hashed payload: `hash_id`, `record_hash`, `receipt`, `receipts`, `enrichment`, `index`.

For backfilled v1 events, `hash_id` is the already-stamped digest of the original v1 body (`receipts` and `record_hash` omitted). PTR/ASN added later do not change that digest.

If `event_id` is not supplied, it is assigned as `blv2-` (or `blv1-`) plus the first 16 hex characters of `hash_id`.

## First-wins and restamp history

Verae keeps the **original timestamp**. Submitting the same digest again without `restamp` does not create a new certificate; the original is returned as already existing.

A `restamp=true` submission adds a **new** history entry (time, certificate, block, batch, merkle root). The original first-wins record is left unchanged. An IP can be restamped more than once; each restamp is a separate row.

A proof request that only looks up the original digest will show the first-wins stamp, not the later restamps. Full history comes from the IPRX event log (and the chain's restamp history). The [history API](api.md#history--get-apiv1historyiphash_id) and the [history page](https://blocklist.iprx.org/history) are built to show that complete timeline.

## Receipts

A receipt is the confirmation that `hash_id` was included in a merklized batch on Verae's chain. Typical fields:

| Field | Meaning |
| --- | --- |
| `job_id` | Submit job, when present |
| `batch_id` / `receipt_id` | Batch identifier |
| `block_number` | Block height when known; may be absent |
| `block_hash` | Block hash |
| `root` | Merkle root of the batch |
| `certificate` | Certificate id when present; not invented if absent |
| `sealer` | Sealer name when present |
| `proof_ok` | The prove call returned `ok` |
| `original_ts` | First-wins timestamp |
| `restamp` | Whether this receipt is a restamp |
| `created_at`, `submitted_at`, `confirmed_at`, `proved_at` | Times when known |
| `chain` | `verae-substrate` |
| `verify_url` | `https://explorer.verae.ai/time?receipt=…&sha256=…` |

### Downloadable receipts

You can download a receipt, and a full IP-history bundle, in three formats from [blocklist.iprx.org](https://blocklist.iprx.org/) and [iprx.org](https://iprx.org/):

| Format | What you get |
| --- | --- |
| **JSON** | Canonical receipt JSON, including `canonical_sha256` |
| **HTML** | A printable page of the same facts |
| **PDF** | The same content as a document |

```
GET /api/v1/receipts/{event_id|hash_id}.json|.html|.pdf
GET /api/v1/receipts/ip/{ip}.json|.html|.pdf
```

Short URLs: `https://iprx.org/r/{hash_id}.html` (or `.json` / `.pdf`), and `https://iprx.org/r/ip/{ip}.html` for a bundle. Suffixes, `?format=`, and `Accept: application/json`, `text/html`, or `application/pdf` select the same formats. The JSON file is canonical and includes `canonical_sha256`, the SHA-256 of that JSON without the `canonical_sha256` field itself. HTML and PDF are printable and include a QR code for `https://iprx.org/r/{hash_id}`. Details are in [the API](api.md#download-a-receipt). Public files omit requestor contact details.

You can also verify a digest directly:

```bash
curl -sS -X POST https://api.verae.ai/v1/prove \
  -H 'Content-Type: application/json' \
  -d '{"digest":"HASH_ID"}'
```

A valid proof has `ok: true` and a Merkle path that recomputes to `root` on `block_hash`. Open the `verify_url` to see the same result in the explorer.

## How to verify by hand

1. Start from the event JSON (or the `canonical_event` in a downloaded receipt).
2. Drop the omitted fields listed under [hash_id](#hash_id).
3. Serialize with sorted keys and no extra whitespace, UTF-8.
4. SHA-256 that byte string. The hex digest must equal `hash_id` (and the file's `sha256` if you downloaded a receipt).
5. Prove that digest on Verae (`POST https://api.verae.ai/v1/prove` or the explorer URL).
6. For a restamped hash, treat the original receipt and each restamp receipt as separate proofs. The original `original_ts` must not change.

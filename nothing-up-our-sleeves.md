# Nothing Up Our Sleeves

IPRX is built so you never have to take our word for anything. Every timestamp, every record, and every published file can be checked independently against the [Verae](https://verae.ai) chain.

## Objectives

1. **Provable timestamps.** Every listing, removal, nomination, removal request, and operator decision is hashed and anchored on Verae. The first stamp for a record is permanent, so nobody can backdate it later. A restamp adds to the history and never overwrites the original.
2. **Provable data.** Each record carries its reason, its evidence summary, and (where available) PTR, ASN, and ISP details. The record's SHA-256 digest is what goes on chain. Hash the record yourself, then compare it to the receipt and the block's Merkle root.
3. **Provable GitHub uploads.** Each published release of the block files ships with a manifest that lists the SHA-256 of every file and a change summary. That manifest is stamped as a single batch on Verae before it is pushed. The commit message carries the manifest hash and its Verae receipt ID, so a file in this organization can be traced to the exact moment it was sealed.
4. **No silent edits.** Nothing is listed or removed automatically, and nothing is changed off the record. Every decision appears in the public history for that IP or IP hash. Requestors' contact details are redacted from the public view.
5. **Receipts for everyone.** Any receipt can be downloaded as JSON, HTML, or PDF from the web app or the API. You can verify it without trusting IPRX's servers.

## How to verify

1. Download the file, or fetch the record from the history API.
2. Compute its SHA-256 and compare that to the value in the manifest or the receipt.
3. Check the receipt's Merkle proof against the block root on Verae.
4. Confirm that the block's timestamp comes before the GitHub commit or the DNSBL change.

## Status (November 2026)

| Objective | Status |
| --- | --- |
| Per-record Verae stamps with first-wins and restamp history | Live, and verified on a test chain |
| DNSBL at `bl.georgelambert.org` | Live |
| Public history, check, nomination, and removal pages | Live at [blocklist.iprx.org](https://blocklist.iprx.org/) ([About](https://blocklist.iprx.org/about), [Check](https://blocklist.iprx.org/check), [Nominate](https://blocklist.iprx.org/nominate), [Remove](https://blocklist.iprx.org/remove), [History](https://blocklist.iprx.org/history)) |
| JSON/HTML/PDF receipt downloads | Live: [`GET /api/v1/receipts/{id}.json\|html\|pdf`](https://blocklist.iprx.org/docs) and [https://iprx.org/r/{hash_id}.html](https://iprx.org/r/{hash_id}.html) |
| Stamped manifests for GitHub block-file releases | Coming soon. Block files will be published only after the lists are confirmed reliable |

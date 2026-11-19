# Verae's Full Timestamped Tracking Blockchain

[Verae](https://verae.ai) is Verae's own blockchain. It is spelled V-E-R-A-E and pronounced *VEER-ay*. The design is patent pending. IPRX does not use a third-party chain (Bitcoin, Ethereum, OpenTimestamps, or similar) to timestamp its records.

The public site is [https://verae.ai](https://verae.ai) (it resolves and serves the product pages). The explorer is [https://explorer.verae.ai](https://explorer.verae.ai). Digests are submitted and proved at [https://api.verae.ai](https://api.verae.ai).

## What goes on chain

**Only hashes.** You hash a file or a structured event locally. The digest is sent to Verae; the bytes stay with you. For IPRX, that digest is the event's [`hash_id`](records-and-receipts.md#hash_id) or the SHA-256 of a feed `manifest.json`.

A packer batches many digests, builds a Merkle tree, and commits the **root** in a block. The receipt names a `batch_id`, `block_hash`, merkle `root`, and an optional sealer. Anyone can later ask for a Merkle proof that a given digest is under that root.

## First-wins and restamps

The first time a digest is sealed, that timestamp is permanent. Submitting the same digest again without restamp is a no-op: the original is returned as already existing.

A restamp is explicit. It adds a new certificate and a new history row (time, batch, block, merkle root) **next to** the original. The original record is not overwritten. A prove call for the original digest still returns the first-wins stamp; the restamp history is a separate timeline. IPRX uses that for later evidence about the same IP — a new reason, a new network snapshot, or a later review — without losing the first listing time.

## Sharded packers

Live stamping uses several packers in parallel, each responsible for a shard of the digest space, talking over core NATS (not JetStream). Clients send a pack of digests to the shard that owns them. Completions come back when the batch is sealed on chain. IPRX's production path is this packer model; a smaller HTTP `/v1/stamp` API exists for modest volumes.

## Measured performance

These numbers are from instrumented tests in November 2026 on a six-shard layout, with blocks on a ~200 ms interval. They are the measured results, not theoretical peaks.

A first run stamped the then-current blocklist (13,688 unique digests) over NATS in **2.095 seconds**, about **6,533 stamps/s**. Median time to accept a pack was **38 ms**. Median time to confirm on chain was **219 ms** (about **220 ms**). The same work through the HTTP stamp API was much slower: about **159 stamps/s** in a fast stamp-only phase, and a median confirm of **1,340 ms** for batches of 250.

First-wins held in that run: 100 already-stamped digests submitted without restamp came back as existing, with no new seal. Five digests submitted with restamp were accepted and sealed as new certificates.

A larger run then submitted **5,000,000** unique digests:

| Phase | Digests | Time | Rate |
| --- | ---: | ---: | ---: |
| Accept (main pack) | 5,000,000 | 13.128 s | **380,397 /s** (about 380,000 /s) |
| Submit through last seal | 5,000,000 | 153.68 s | **32,535 sealed /s** (about 32,500 /s) |

All 5,000,000 were accepted. The limiter was sealing and committing on chain, not the NATS ingest path. After the queue drained, a proof of one digest from each of the six shards succeeded. Blocks were produced on a **~200 ms** interval (about five blocks per second). When the pending queue was empty, confirm times clustered around **~220 ms**.

Those figures are why a service like IPRX can attach a checkable receipt to every listing change without waiting on a public third-party chain.

## Building a real-time tracking and proof service

IPRX is a short pipeline on top of that primitive:

1. **Event** — record what happened (add, remove, nomination, decision) and why, with optional PTR/ASN detail.
2. **Digest** — hash the canonical event. The body never goes on chain.
3. **Stamp** — send the digest to a packer; wait for the batch root to land in a block.
4. **Receipt** — store `batch_id`, `block_hash`, `root`, and times next to the event.
5. **Public verification** — anyone can re-hash the event, prove the digest, and fetch the same receipt as JSON, HTML, or PDF from the [download API](api.md#download-a-receipt).

Because the chain only has to store roots of batches, not the records themselves, standing up a new tracking service is mostly: define an event schema, hash it, stamp it, and show the receipt. IPRX — DNSBL, feeds, nomination form, and history — is one such service.

The same pattern fits other Verae products and use cases, including:

- **Verae DataTrax** — timestamped tracking for ERP and business records
- **DataCubes** — packaged, provable data collections
- **DataFax** — transmitted documents with a verifiable time and integrity receipt

More about the platform: [https://verae.ai](https://verae.ai).

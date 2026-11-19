# IPRX documentation

Public documentation for [IPRX](https://iprx.org), a worldwide IPv4 blocklist built from honeypot data, with optional downloadable feeds and Verae-timestamped receipts.

The DNS blocklist at `bl.georgelambert.org` is live. The public site — About, Check, Nominate, Remove, and History — is at [https://blocklist.iprx.org/](https://blocklist.iprx.org/). The API is live at [https://blocklist.iprx.org/api/v1/](https://blocklist.iprx.org/api/v1/) and [https://iprx.org/api/v1/](https://iprx.org/api/v1/), with OpenAPI at [https://blocklist.iprx.org/docs](https://blocklist.iprx.org/docs). Receipts are available as JSON, HTML, and PDF. Downloadable block files are **not published yet**; they will be released only after the lists are confirmed reliable.

## Contents

| Document | What it covers |
| --- | --- |
| [File formats](file-formats.md) | Every feed format the generator produces, plus items still planned |
| [Update frequency](update-frequency.md) | How often the DNSBL and feeds refresh, and how versions are named |
| [Usage](usage.md) | DNSBL queries, mail and firewall snippets, Bloom readers, checksums, receipt checks |
| [API](api.md) | Live nominations, removal requests, IP checks, history, and receipt downloads as JSON, HTML, or PDF |
| [Examples](examples/README.md) | Copy-and-run curl, Python, JavaScript, Go, and dig requests, with a comment on every line and a JSONL catalog |
| [Scripts](scripts.md) | Why every example line is documented, how the JSONL format is laid out, and how to verify each file's Verae receipt |
| [Records and receipts](records-and-receipts.md) | Event schema, `hash_id`, first-wins + restamp history, how to verify |
| [Verae](verae.md) | Verae’s timestamped tracking blockchain, measured performance, and why IPRX was quick to build |
| [Nothing Up Our Sleeves](nothing-up-our-sleeves.md) | Our commitments to provable timestamps, data, and GitHub uploads, and how to verify them |
| [Contributing](CONTRIBUTING.md) | How to suggest documentation changes |
| [Security](SECURITY.md) | How to report a vulnerability or request a delisting |
| [License](LICENSE) | Documentation is [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |

## Nothing Up Our Sleeves

Every timestamp, record, and published file in IPRX is meant to be provable, not trusted:

- **Timestamps.** Every listing, removal, request, and decision is anchored on Verae. The first stamp is permanent, and restamps only add history.
- **Data.** Each record's SHA-256 is on chain, so you can hash the record yourself and check it against the receipt.
- **GitHub uploads.** Each block-file release ships a manifest of file hashes. That manifest is stamped on Verae before it is pushed, and its receipt ID goes in the commit message.

Read the objectives and verification steps in [Nothing Up Our Sleeves](nothing-up-our-sleeves.md).

Organization profile: [github.com/iprx-org](https://github.com/iprx-org).

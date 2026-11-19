# How (and why) the IPRX examples are documented

The examples live in [examples/](examples/). This page explains the conventions they follow, why every line is commented, how the JSONL catalog is laid out, and how to verify each file against its Verae receipt.

The runnable scripts themselves, plus format-specific notes, are described in [examples/README.md](examples/README.md).

## Why every line is documented

IPRX is built so you do not have to take our word for anything. That is the same idea as [Nothing Up Our Sleeves](nothing-up-our-sleeves.md): timestamps, data, and published files should be independently checkable.

The example scripts are part of that promise:

- **No hidden flags.** A comment on every line says what the line does and how you can change it (the host, the IP, the reason, the output path, and so on).
- **No hidden credentials.** The scripts use only the public API. Tokens from a removal request are stored under `~/.iprx/` with mode 600 and are never written into this repository.
- **No hidden side effects.** Bulk submitters default to skipping documentation and private addresses. `--dry-run` prints what would be sent and does not call the write API. DKIM examples upload a local `.eml`; they never send email.
- **The bytes you see are the bytes we stamped.** After this directory was finished, each file was hashed and anchored on Verae. The matching JSON and PDF receipts, and a stamped manifest, are in [examples/receipts/](examples/receipts/).

If a script or a JSONL line is later edited, the original Verae timestamp still wins and a restamp adds history. Recompute the SHA-256 and compare it to the receipt; if they disagree, the file changed after it was stamped.

## How the JSONL catalog is laid out

Each language folder has a `requests.jsonl` file. It is UTF-8 text with **one JSON object per line** (no wrapping array). Blank lines are not used. You can read it with `jq -s . requests.jsonl`, or line by line with `jq . requests.jsonl`.

Each object has these fields:

| Field | Meaning |
| --- | --- |
| `id` | Stable identifier, for example `curl-check` or `python-nominate` |
| `title` | Short name of the request |
| `purpose` | What it is for, in one or two sentences |
| `method` | `GET`, `POST`, or `DNS` |
| `url` | The URL template, with `{ip}` / `{hash_id}` placeholders |
| `headers` | Request headers, if any |
| `body` | JSON body, or `null` for a GET |
| `command` | The exact command or snippet to run |
| `line_docs` | An array of strings, one explanation per line of the script or command |
| `expected_response` | A representative body, recorded against the live service where possible |
| `notes` | Rate limits, redaction, live test results, and how to change the example |

`expected_response` is abbreviated when the live body is large, or when it would otherwise include operator-only paths or a one-time token. Tokens are never stored in these files.

## How to run the examples

From a clone of this repository:

```bash
cd examples/curl
./02-check.sh 192.0.2.1
./05-search-hostname.sh nt-isp
./08-receipts.sh
```

```bash
cd examples/python
python3 check.py 43.99.86.230
python3 submit_blockfile.py --dry-run ../samples/fail2ban.log
```

The default API origin is `https://iprx.org`. Override it with `IPRX_BASE` if you need to. For nominations and removals, set `IPRX_NAME` and `IPRX_EMAIL`. The live API rejects private, reserved, and RFC 5737 documentation addresses for nominations (HTTP 400). Removal requests on those addresses are accepted as `pending_dkim` and still need a DKIM-signed `.eml` plus an operator decision.

The API allows 10 nominations per hour per client. The bulk submitter waits between posts and retries once on HTTP 429. One submitter still counts as one nominator toward the 5-distinct-nominator listing rule.

A batch nomination endpoint would make fail2ban-style imports kinder on that rate limit. It is not in this release.

## How to verify a file's receipt

Every file under `examples/`, plus this page and the docs [README.md](README.md), has:

- `examples/receipts/<path>.receipt.json` — the canonical receipt
- `examples/receipts/<path>.receipt.pdf` — the same fields as a printable document

The manifest `examples/receipts/MANIFEST.json` lists every file, its SHA-256, its size, and the path of its receipt. The manifest itself is stamped; its receipt sits next to it.

To check one file:

1. `sha256sum examples/python/check.py` (or `shasum -a 256` on macOS).
2. Open `examples/receipts/examples/python/check.py.receipt.json` and compare the `sha256` field. They must match exactly.
3. The receipt also has the stamp time in UTC and in America/New_York, the block hash, the Merkle root, the proof, and a `verify_url`.
4. Confirm the proof against the block root on Verae. The original stamp is permanent; a restamp only adds history.
5. After the file is on GitHub, fetch the raw URL and hash those bytes too. They must match the receipt.

If you are reading a GitHub raw file and the hash does not match, the file was changed after it was stamped — or you are not looking at the revision the manifest describes.

## What is not in these examples

- Admin endpoints, admin paths, and credentials
- Internal hostnames, private server addresses, and operator-only lookup sources
- Blocklist feed files (those will be published only after the lists are confirmed reliable)
- One-time removal tokens

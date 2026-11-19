# Update frequency

This page describes how often IPRX data changes, and how feed versions are named.

## DNS blocklist (live)

The DNS zone at `bl.georgelambert.org` is rebuilt **every 5 minutes**. The zone file is rewritten only when membership actually changes. After a rewrite, nameservers typically pick up the new zone within about a minute.

A listed name currently uses a 60-second DNS TTL, so a removal can take a few minutes to disappear from caches after the zone updates.

Approved removals are sticky: once an address is delisted, later honeypot activity is reported to operators and is **not** put back on the list automatically. Re-listing after a new attack is a manual decision.

## Downloadable feed (not published yet)

The feed generator is run **on demand** today. A scheduled rebuild in the same 5-15 minute range, published to a public download location, is [planned](file-formats.md#planned) for when the lists are confirmed reliable and a download URL is announced on [iprx.org](https://iprx.org).

A rebuild with unchanged membership rewrites identical list bytes and leaves `manifest.json`, `CHANGELOG.md`, and `COMMIT_MESSAGE.txt` untouched, so a Git tree would have no diff. Only a membership change (exact IPs or coarse CIDRs), or the initial build, produces a new list version.

When a public Git publish starts, the practical default is: rebuild alongside the DNSBL timer, and commit only when membership changes (or squash to a daily commit if the history would be too noisy). That cadence is not live yet.

## Version and manifest names

| Name | How it is formed |
| --- | --- |
| `format_version` | Integer `1` for the current layout and file schemas. |
| `list_version` | `v1-YYYYMMDDTHHMMSSZ` from the UTC time of that membership-changing build. Example: `v1-20261119T024059Z`. A no-op rebuild keeps the previous value. |
| `generated_at` | The same instant as `YYYY-MM-DDTHH:MM:SSZ` inside `manifest.json`. |
| Changelog section | `## v1-YYYYMMDDTHHMMSSZ — YYYY-MM-DDTHH:MM:SSZ` |
| `manifest.sha256` | Always named `manifest.sha256`, and always covers the current `manifest.json`. |
| `manifest.receipt.json` | [Planned](file-formats.md#planned). Same basename as the manifest, written after that manifest's SHA-256 is stamped on Verae. |

Integrity of a published tree is the SHA-256 of each file in `manifest.json`, plus the SHA-256 of the manifest in `manifest.sha256`. See [usage](usage.md#verify-manifest-checksums). Detached signatures of the files themselves are planned for the first public Git publish.

## Stamping cadence

- Stamp the feed manifest on each membership-changing build (planned for publish time).
- Stamp each verified nomination, each removal request, and each operator decision.
- Individual add/remove events can be stamped in a batch of that run's diffs, rather than re-stamping the entire historical list every time.

The DNSBL itself does not embed Verae receipts in DNS answers. Receipts are a separate record you look up on [blocklist.iprx.org](https://blocklist.iprx.org/) or [iprx.org/r/{hash_id}](https://iprx.org/r/{hash_id}.html), or verify on [Verae](https://verae.ai).

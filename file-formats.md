# Feed file formats

This page describes **format version 1** of the IPRX downloadable feed, as produced by the feed generator. The tree is git-friendly: one directory per format, deterministic list files (no per-build timestamps in the lists themselves), and a root `manifest.json`.

**The feed is not published yet.** These specifications are for integrators who want to prepare clients, and for the first public release once the lists are confirmed reliable. Until then, treat any local or preview copies as unpublished.

A Bloom filter can report “maybe listed” for an address that is not on the exact list. Use the text or CSV lists when you need certainty. Optional coarse `/24` CIDRs also block unlisted addresses in the same network; they are kept in separate sets so you can ignore them.

## Layout

```
feed/
  README.md
  CHANGELOG.md
  COMMIT_MESSAGE.txt
  manifest.json
  manifest.sha256
  manifest.receipt.json   # planned: added after the manifest digest is stamped on Verae
  txt/blocklist.txt
  csv/blocklist.csv
  ipset/blocklist.ipset
  nft/blocklist.nft
  fail2ban/blocklist.fail2ban
  bloom/blocklist.bloom
  bloom/BLOOM_FORMAT.md
  onepacket/onepacket.bin
```

| Path | Content type | What it is |
| --- | --- | --- |
| `txt/blocklist.txt` | `text/plain` | Exact IPv4 addresses plus optional coarse `/24` CIDRs |
| `csv/blocklist.csv` | `text/csv` | Same entries with reason, hit counts, and first/last seen |
| `ipset/blocklist.ipset` | `text/plain` | `ipset restore` script (`bl-exact` and optional `bl-coarse`) |
| `nft/blocklist.nft` | `text/plain` | nftables table `inet bl_georgelambert` |
| `fail2ban/blocklist.fail2ban` | `text/plain` | One exact IP per line; `#` starts a comment |
| `bloom/blocklist.bloom` | `application/octet-stream` | BF4B v1 Bloom filter of exact IPs only |
| `onepacket/onepacket.bin` | `application/octet-stream` | Exact packed prefixes in ≤548 bytes |
| `manifest.json` | `application/json` | Versions, counts, per-file SHA-256, size, entry count |
| `manifest.sha256` | `text/plain` | SHA-256 of `manifest.json` in `sha256sum` format |
| `CHANGELOG.md` | `text/markdown` | Appended only when membership changes |
| `COMMIT_MESSAGE.txt` | `text/plain` | Suggested commit message for a later Git publish |

There is **no JSON or JSONL blocklist feed** in format version 1. A JSON/JSONL membership export is [planned](#planned). Event records used for receipts are a separate JSONL format; see [records and receipts](records-and-receipts.md).

Encoding for all text files is UTF-8, newline-terminated. List membership is sorted by IPv4 numeric order. A rebuild with the same membership rewrites identical list bytes and does not change `manifest.json` or append the changelog.

## Plain text (`txt/blocklist.txt`)

Comment lines start with `#`. The header records `format_version` and membership counts. Version and `generated_at` live in `manifest.json`, not in this file.

1. Optional coarse CIDRs, one per line (`a.b.c.0/24`).
2. A comment section `# Exact IPv4 addresses`.
3. Exact host addresses, one per line (no `/32` suffix).

A `/24` is included only when that network has **at least 2 listed IPs and 1,000 combined hits**. Those ranges also block unlisted addresses in the same `/24`. For an exact-only list, skip any line containing `/`.

## CSV with metadata (`csv/blocklist.csv`)

Header row, then one row per CIDR (first) and one row per exact IP. Columns:

| Column | CIDR row | Exact IP row |
| --- | --- | --- |
| `ip_or_cidr` | Network, e.g. `192.0.2.0/24` | Host address |
| `prefix_len` | `24` | `32` |
| `type` | `cidr` | `ip` |
| `hits` | Combined hits in the `/24` | Hits for that address |
| `listed_ips` | Number of listed IPs in the `/24` | `1` |
| `first_seen` | Earliest `first_seen` among members | First seen (may be empty) |
| `last_seen` | Latest `last_seen` among members | Last seen (may be empty) |
| `source` | `|`-joined unique sources | Source string (may be `|`-joined) |
| `reason_code` | `DENSE_PREFIX` | `HONEYPOT_HIT` (or a more specific code if present) |
| `reason` | Human text, including IP and hit counts and a collateral warning | Human text including hit count, source, and first/last seen |
| `action` | `listed` | `listed` |

Times in `first_seen` / `last_seen` are copied from the honeypot source CSV and may use a space between date and time rather than `T`.

## ipset (`ipset/blocklist.ipset`)

An `ipset restore` script. The default set is exact IPs only. Coarse `/24`s go in a second optional set.

```
create bl-exact hash:ip family inet hashsize 16384 maxelem 65536 -exist
create bl-coarse hash:net family inet hashsize 1024 maxelem 4096 -exist
flush bl-exact
flush bl-coarse
add bl-exact 192.0.2.1 -exist
add bl-coarse 198.51.100.0/24 -exist
```

`entry_count` in the manifest is the number of exact IPs (not including coarse members).

## nftables (`nft/blocklist.nft`)

Defines table `inet bl_georgelambert` with two sets, both `type ipv4_addr` and `flags interval`:

- `honeypot_exact` — exact IPs, no collateral
- `honeypot_coarse` — optional `/24`s

Elements are written 20 per line. Apply with `nft -f nft/blocklist.nft`. The file begins with `flush set` for those two sets, then the `table` block. On a machine that has never loaded the table, skip or ignore the two `flush set` lines for the first apply; later refreshes can use the file as generated.

Manifest `entry_count` is again the exact-IP count.

## fail2ban (`fail2ban/blocklist.fail2ban`)

Comment header, then one exact IPv4 address per line. Lines starting with `#` are comments. Coarse CIDRs are **not** included. See [usage](usage.md#fail2ban).

## Bloom filter (`bloom/blocklist.bloom`)

Format name **BF4B** (Bloom Filter for IPv4, Binary), version **1**. Only individual IPv4 addresses are stored; CIDRs are not. Full reader specification: `bloom/BLOOM_FORMAT.md` in a published feed (summarized here from the same spec).

### Header (little-endian, 24 bytes)

| Offset | Size | Type | Field |
| ---: | ---: | --- | --- |
| 0 | 4 | bytes | Magic `0x42 0x46 0x34 0x42` (`BF4B`) |
| 4 | 1 | uint8 | Version `1` |
| 5 | 2 | uint16 | `k` — number of hash functions |
| 7 | 1 | uint8 | Reserved; must be `0` |
| 8 | 8 | uint64 | `m_bits` — bit-array length in bits (multiple of 8) |
| 16 | 8 | uint64 | `n_inserted` — number of IPs inserted (informational) |
| 24 | `m_bits/8` | bytes | Bit array |

Total size is `24 + m_bits/8` bytes. There is no checksum trailer. Readers must reject any other magic, version, or reserved byte.

C layout:

```c
/* packed, little-endian */
struct bf4b_header {
    char     magic[4];     /* "BF4B" */
    uint8_t  version;      /* 1 */
    uint16_t k;
    uint8_t  reserved;     /* 0 */
    uint64_t m_bits;
    uint64_t n_inserted;
};
```

### Bit array

Bit index `i` (0 ≤ `i` < `m_bits`) is in byte `i >> 3`, bit `(i & 7)` (bit 0 is the least-significant bit). `m_bits` is always a multiple of 8.

### Membership test

For IPv4 address `A.B.C.D`:

1. `key` = the 4 bytes `{A, B, C, D}` (network / big-endian order).
2. `digest = BLAKE2s(key, digest_size=16)` — this is **BLAKE2s-128**, not the first 16 bytes of BLAKE2s-256. The parameter-block digest size must be 16.
3. `h1 = uint64_be(digest[0..7])`
4. `h2 = uint64_be(digest[8..15]) | 1` (force odd and non-zero so the stride covers the table)
5. For `i` in `0 .. k-1`: `idx = (h1 + i * h2) mod m_bits`. If bit `idx` is 0, the address is **not** in the set.
6. If every bit is 1, the address **may** be in the set (possible false positive).

False negatives never occur for inserted addresses. Languages with wrapping 64-bit integers must not compute `(h1 + i * h2) mod m` with a 64-bit multiply. Use `((h1 mod m) + i * (h2 mod m)) mod m` instead.

### Sizing used by the generator

For expected capacity `n` and target false-positive rate `p`:

- `m = ceil(n * ln(p) / ln(2)^2)` bits, rounded up to a multiple of 8
- `k = max(1, round((m / n) * ln(2)))`

Published filters use **`p = 0.001`** (0.1%) and **`n = 10 × unique_ips`** at build time (`growth = 10`). A November 2026 build of 13,688 exact IPs produced `m_bits = 1,968,008`, `k = 10`, file size 246,025 bytes.

Look up a host address, not a prefix.

## One-packet compact format (`onepacket/onepacket.bin`)

An **exact** (zero false-positive) set of IPv4 prefixes sized to fit in a 548-byte ICMP payload. A prefix of length `P` blocks exactly `2^(32-P)` addresses. The current recommended pack promotes a `/24` when it has at least 2 listed IPs and 1,000 combined hits, then fills leftover space with the highest-hit uncovered `/32`s. A November 2026 build was 546 bytes: 41 `/24`s plus 128 `/32`s (169 prefixes).

### Binary layout

All multi-byte integers in section headers are little-endian except the packed prefix keys, which are big-endian.

```
magic        4 bytes   "OPK1"
version      uint8     1
n_sections   uint8
For each section:
  plen       uint8     prefix length in bits (1..32)
  enc        uint8     0 = raw truncated keys, 1 = Golomb-Rice
  count      uint16    number of prefixes
  rice_r     uint8     only if enc == 1
  data_len   uint16    only if enc == 1
  data       raw:  count * ceil(plen/8) bytes, big-endian packed keys
                   (the high `plen` bits), sorted
             rice: bit stream; first key is `plen` bits, each later key
                   is a Rice-coded (delta-1) with parameter rice_r
                   (q in unary, a 0 stop bit, then an r-bit remainder)
```

An address matches if any stored prefix covers it. This file is a compact *subset* of the full list (high-hit clusters plus top leftover hosts), not a complete membership set.

## Manifest, changelog, and checksums

### `manifest.json`

Pretty-printed JSON, keys sorted, trailing newline. Fields:

| Field | Meaning |
| --- | --- |
| `format_version` | Integer `1` |
| `list_version` | `v1-YYYYMMDDTHHMMSSZ` from the UTC build time, e.g. `v1-20261119T024059Z`. Unchanged if a rebuild finds identical membership. |
| `generated_at` | UTC timestamp `YYYY-MM-DDTHH:MM:SSZ` |
| `source` | Source CSV basename |
| `additions` | Optional additions file basename, or `null` |
| `delist` | Delist file basename |
| `counts` | `exact_ips`, `cidrs`, `delisted_applied`, `new_activity_after_delist` |
| `changes` | `added_ips`, `removed_ips`, `added_cidrs`, `removed_cidrs`, `membership_changed`, `initial` |
| `delisted` | Applied delist rows (may be empty) |
| `new_activity_after_delist_rows` | Delisted addresses that showed later honeypot activity (reported, not auto-relisted) |
| `bloom` | `format` (`BF4B`), `version` (`1`), `target_fp` (`0.001`), `growth` (`10.0`), `spec` (`bloom/BLOOM_FORMAT.md`) |
| `files` | Array of `{name, content_type, size, sha256, entry_count}` |

`files` includes the list artifacts plus `bloom/BLOOM_FORMAT.md` and `README.md`. SHA-256 digests are lowercase hex of the file bytes.

### `manifest.sha256`

One `sha256sum` line for the manifest itself:

```
<64-hex-sha256>  manifest.json
```

(two spaces between digest and filename, trailing newline). See [usage](usage.md#verify-manifest-checksums).

### `CHANGELOG.md`

Starts with `# Changelog`. A new section is prepended only when membership changes (or on the initial build / a layout-only repack). Section title:

```
## v1-YYYYMMDDTHHMMSSZ — YYYY-MM-DDTHH:MM:SSZ
```

The body lists `+added/-removed` counts for exact IPs and coarse CIDRs, up to 40 names in each list, any delist rows applied, and the manifest SHA-256. A no-op rebuild does not append a section and does not rewrite the manifest.

### `COMMIT_MESSAGE.txt`

A suggested Git commit body for a later publish: title line with the list version and add/remove counts, a short summary, the manifest SHA-256, and a placeholder for the Verae receipt. Not itself a consumer format.

## Planned

Items mentioned for completeness that the generator does **not** produce today:

| Item | Status |
| --- | --- |
| JSON / JSONL membership feed | **Planned.** Event JSONL exists for receipts, not as a downloadable blocklist. |
| `manifest.receipt.json` | **Planned** next to the manifest after the manifest digest is stamped on Verae. The manifest already has a SHA-256; the receipt will prove that digest on chain. |
| Detached signatures (GPG or similar) of feed files | **Planned** for the first public Git publish (signed commits). Today the integrity check is SHA-256 in `manifest.json` and `manifest.sha256`. |
| DNSBL CIDR / wildcard range listings | The DNS generator can represent ranges, but they are **not enabled** in the live zone. Coarse `/24`s exist only in the (unpublished) feed, in optional sets. |
| Published HTTPS feed tree | **Planned.** No public download URL is live. |

Checksums are implemented; cryptographic signatures of the feed files are not.

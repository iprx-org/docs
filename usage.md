# Usage

How to query the live DNS blocklist, how you will load each feed format once the lists are published, and how to check checksums and Verae receipts.

The DNSBL at `bl.georgelambert.org` is live. **Downloadable block files are not published yet.** In the snippets below, replace `./feed` with the feed directory you will download from the URL announced on [iprx.org](https://iprx.org).

## DNS blocklist

Reverse the four octets of an IPv4 address, then look up that name under `bl.georgelambert.org`.

```bash
# Always-listed test entry
dig +short A 2.0.0.127.bl.georgelambert.org
# 127.0.0.2

dig +short TXT 2.0.0.127.bl.georgelambert.org
# "honeypot hits=N last=YYYY-MM-DD"

# Helper
lookup() {
  ip=$1
  rev=$(printf '%s\n' "$ip" | awk -F. '{print $4"."$3"."$2"."$1}')
  dig +short A "${rev}.bl.georgelambert.org"
}
lookup 192.0.2.1
```

A listed address answers `A 127.0.0.2` and a TXT record of the form `honeypot hits=N last=YYYY-MM-DD`. An address that is not listed returns NXDOMAIN (an empty answer and status `NXDOMAIN`).

CIDR range listings are not enabled in the live DNS zone. Optional coarse `/24`s exist only in the unpublished feed, in separate sets.

The updater never lists private (RFC1918), loopback (except the `127.0.0.2` test name), multicast, unspecified, or the operator's own public network. Approved removals also stay off the list until an operator changes that decision.

### Postfix

```
smtpd_recipient_restrictions =
    permit_mynetworks,
    permit_sasl_authenticated,
    reject_unauth_destination,
    reject_rbl_clients bl.georgelambert.org,
    permit
```

`reject_rbl_clients` treats an `A 127.0.0.2` answer as a hit.

### Exim

```
deny  message = listed by IPRX DNSBL
      dnslists = bl.georgelambert.org
```

### rspamd

In `local.d/rbl.conf`:

```
rbls {
  iprx {
    symbol = "RBL_IPRX";
    rbl = "bl.georgelambert.org";
    ipv4 = true;
    ipv6 = false;
    returncodes {
      "RBL_IPRX" = "127.0.0.2";
    }
  }
}
```

Adjust the symbol score in your local metrics to match your mail policy.

## ipset and iptables

Once you have `ipset/blocklist.ipset`:

```bash
ipset restore < ./feed/ipset/blocklist.ipset

# Exact addresses only (no collateral)
iptables -I INPUT -m set --match-set bl-exact src -j DROP

# Optional coarse /24s — these also block unlisted hosts in the same network
# iptables -I INPUT -m set --match-set bl-coarse src -j DROP
```

Refresh by running `ipset restore` again; the script uses `-exist`, `create`, and `flush`, so it is safe to re-apply. There is no separate iptables-restore file; load the sets with ipset, then match them in iptables as above.

## nftables

```bash
# First load on a host that does not yet have table inet bl_georgelambert:
# temporarily comment or remove the two leading "flush set" lines, then:
nft -f ./feed/nft/blocklist.nft

# Later refreshes can use the file as generated
nft -f ./feed/nft/blocklist.nft
```

Wire the sets into a policy, for example:

```
table inet filter {
    chain input {
        type filter hook input priority 0;
        ip saddr @honeypot_exact drop
        # optional: ip saddr @honeypot_coarse drop
    }
}
```

nftables set references are resolved in the same table or via a fully qualified name such as `ip saddr inet bl_georgelambert honeypot_exact drop`, depending on your ruleset layout. Keep exact and coarse matches separate so coarse collateral is a conscious choice.

## fail2ban

`fail2ban/blocklist.fail2ban` is one IP per line (comments start with `#`). It does not include coarse CIDRs. A typical pattern is to load it into the ipset from the feed, then match that set from fail2ban or nftables/iptables, rather than listing tens of thousands of addresses in `jail.local`.

```bash
# Example: keep an ipset in sync with the exact list, then match it in nft/iptables
ipset restore < ./feed/ipset/blocklist.ipset
```

You can also poll the DNSBL for a single connecting address:

```bash
dnsbl_listed() {
  local ip=$1 rev
  rev=$(printf '%s\n' "$ip" | awk -F. '{print $4"."$3"."$2"."$1}')
  dig +time=2 +tries=1 +short A "${rev}.bl.georgelambert.org" \
    | grep -qx '127.0.0.2'
}
```

## Bloom filter

A hit means “maybe listed” (target false-positive rate 0.1% at 10× the unique-IP capacity). A miss means the exact address is definitely not in the filter. CIDRs are not stored; look up the host address. For certainty, use `txt/blocklist.txt` or `csv/blocklist.csv`.

### Python

```python
#!/usr/bin/env python3
"""Check one IPv4 address against a BF4B v1 filter."""
import hashlib, ipaddress, struct, sys

HEADER = struct.Struct("<4sBHBQQ")  # magic, ver, k, reserved, m_bits, n_inserted

def load(path):
    data = open(path, "rb").read()
    magic, version, k, reserved, m_bits, n_inserted = HEADER.unpack_from(data)
    if magic != b"BF4B" or version != 1 or reserved != 0:
        raise ValueError("not a BF4B v1 file")
    bits = memoryview(data)[24:]
    return k, m_bits, bits

def contains(ip, k, m_bits, bits):
    key = int(ipaddress.IPv4Address(ip)).to_bytes(4, "big")
    digest = hashlib.blake2s(key, digest_size=16).digest()  # BLAKE2s-128
    h1 = int.from_bytes(digest[:8], "big")
    h2 = int.from_bytes(digest[8:], "big") | 1
    for i in range(k):
        idx = (h1 + i * h2) % m_bits
        if not (bits[idx >> 3] & (1 << (idx & 7))):
            return False
    return True

k, m, bits = load(sys.argv[2] if len(sys.argv) > 2 else "blocklist.bloom")
print("true" if contains(sys.argv[1], k, m, bits) else "false")
```

In languages with wrapping 64-bit integers, compute the index as `((h1 % m) + i * (h2 % m)) % m`.

### Go

```go
package main

import (
	"encoding/binary"
	"fmt"
	"net"
	"os"
	// Use a BLAKE2s-128 implementation (digest size 16), not truncated BLAKE2s-256.
)

func contains(ip string, k int, m uint64, bits []byte, blake2s128 func([]byte) []byte) (bool, error) {
	addr := net.ParseIP(ip).To4()
	if addr == nil {
		return false, fmt.Errorf("bad IPv4: %s", ip)
	}
	digest := blake2s128(addr)
	h1 := binary.BigEndian.Uint64(digest[0:8])
	h2 := binary.BigEndian.Uint64(digest[8:16]) | 1
	h1m, h2m := h1%m, h2%m
	for i := 0; i < k; i++ {
		idx := (h1m + uint64(i)*h2m) % m
		if bits[idx>>3]&(1<<(idx&7)) == 0 {
			return false, nil
		}
	}
	return true, nil
}

func main() {
	fmt.Fprintln(os.Stderr, "see the BF4B header layout in file-formats.md")
}
```

Load the 24-byte little-endian header (`BF4B`, version 1, `k`, reserved 0, `m_bits`, `n_inserted`) and require `len(file) == 24+m_bits/8`. A complete Go sketch belongs with the feed under `bloom/BLOOM_FORMAT.md` when the feed is published.

## Verify manifest checksums

```bash
cd ./feed
# 1. The manifest's own digest
sha256sum -c manifest.sha256

# 2. Every file listed in the manifest
python3 - <<'PY'
import hashlib, json, pathlib, sys
man = json.loads(pathlib.Path("manifest.json").read_text())
ok = True
for f in man["files"]:
    data = pathlib.Path(f["name"]).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != f["sha256"] or len(data) != f["size"]:
        print("FAIL", f["name"]); ok = False
    else:
        print("OK  ", f["name"])
sys.exit(0 if ok else 1)
PY
```

`manifest.sha256` is a single `sha256sum` line: `<64-hex>  manifest.json`. After a membership-changing publish, also compare the digest to the Verae receipt in `manifest.receipt.json` when that file is present ([planned](file-formats.md#planned)).

## Verify a Verae receipt

A receipt proves that a SHA-256 digest was included in a merklized batch on Verae's chain. You never upload the original file or event — only the digest.

1. Confirm the `hash_id` (see [records and receipts](records-and-receipts.md#hash_id)). For a feed manifest, that is the SHA-256 of `manifest.json`.
2. Ask Verae's public prove API:

```bash
DIGEST=the_64_hex_sha256
curl -sS -X POST https://api.verae.ai/v1/prove \
  -H 'Content-Type: application/json' \
  -d "{\"digest\":\"$DIGEST\"}"
```

A successful proof includes `ok: true`, a `batch_id`, `block_hash`, merkle `root`, and sibling hashes. You can also open:

`https://explorer.verae.ai/time?receipt=BATCH_OR_RECEIPT_ID&sha256=DIGEST`

IPRX also offers printable and machine-readable receipt files (JSON, HTML, and PDF) from [the API](api.md#download-a-receipt), for example `GET https://blocklist.iprx.org/api/v1/receipts/{event_id|hash_id}.json` (also `.html` / `.pdf`) and the short URL `https://iprx.org/r/{hash_id}.html`. The JSON is canonical and includes `canonical_sha256`. You can still use `/v1/prove` and the explorer URL above to check a digest directly.

Public [check](https://blocklist.iprx.org/check) and [history](https://blocklist.iprx.org/history) pages show the same proof without exposing a requestor's contact details.

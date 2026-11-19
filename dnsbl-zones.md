# IPRX DNS blocklist zones

IPRX runs its own family of DNS blocklists under **iprx.org**, in the
style of well-known DNSBLs (a combined zone plus per-category zones, a
policy/PBL-style zone, a community zone, an allowlist, and domain/URI
lists). The data is **only** IPRX's: honeypot hits, verified community
nominations, and admin decisions. Third-party lists are not mirrored.

Lookups use the usual reversed-octet query and return `127.0.0.x` for a
hit, or NXDOMAIN if the address is not listed. The TXT record on a hit
is a link to that event's receipt, `https://iprx.org/r/{hash_id}`,
which is also available as JSON, HTML, and PDF.

The authoritative nameserver for these zones is **ns-bl.iprx.org**
(`70.88.205.140`). The older `bl.georgelambert.org` zone stays up as a
legacy alias of the combined list (it still answers `127.0.0.2` from
the original servers).

Query volume is served from an in-memory hash (not a giant zone file),
so listings can be added or removed incrementally and the list can
grow to millions of addresses. See [License](license.md) for fair-use
and dataset terms; DNSBL *queries* for mail and abuse filtering are
the intended use of these zones. Redistribution of the dataset itself
is covered by the license and the yearly pricing tiers.

## Zones and return codes

Query `A` (and optionally `TXT`) for
`<reversed-octets>.<zone>`. A listed address may return more than one
A record in the aggregate zone, one per category, the way a combined
"ZEN-style" list does.

| Zone | Return code | Meaning |
| --- | --- | --- |
| `all.bl.iprx.org` | one `127.0.0.x` per category below | Combined (ZEN-style) list |
| `attack.bl.iprx.org` | `127.0.0.2` | Honeypot hits / scanners |
| `brute.bl.iprx.org` | `127.0.0.3` | SSH / RDP / auth brute force |
| `spam.bl.iprx.org` | `127.0.0.4` | Spam sources |
| `web.bl.iprx.org` | `127.0.0.5` | Web exploit / scanner |
| `bot.bl.iprx.org` | `127.0.0.6` | Botnet / C2 |
| `proxy.bl.iprx.org` | `127.0.0.7` | Open proxies / anonymizers |
| `policy.bl.iprx.org` | `127.0.0.10` | Dynamic or residential ranges (opt-in, PBL-style) |
| `nominated.bl.iprx.org` | `127.0.0.11` | Listed by 5 distinct verified nominators |
| `allow.wl.iprx.org` | `127.0.0.2` | Allowlist (including delistings with DKIM proof) |
| `dbl.iprx.org` | `127.0.0.2` | Domain blocklist (hostnames in evidence, not PTR names) |
| `uri.iprx.org` | `127.0.0.2` | URI / hostname blocklist |

RFC 5782 test points, present in every IP zone:

- `127.0.0.2` is listed (`2.0.0.127.<zone>` returns a `127.0.0.x` A record).
- `127.0.0.1` is not listed (`1.0.0.127.<zone>` is NXDOMAIN).

Domain zones: `TEST.dbl.iprx.org` and `TEST.uri.iprx.org` are listed;
`INVALID.dbl.iprx.org` and `INVALID.uri.iprx.org` are not.

`policy.bl.iprx.org` is opt-in only. An address is never placed there
just because its reverse DNS looks dynamic.

## Query examples

```bash
# Standard test entry (always listed)
dig +short A 2.0.0.127.all.bl.iprx.org @ns-bl.iprx.org
# 127.0.0.2 (and the other category codes)

# An address is not listed
dig +short A 1.0.0.127.all.bl.iprx.org @ns-bl.iprx.org
# (empty, status NXDOMAIN)

# Real lookup: reverse the octets
ip=203.0.113.80
rev=$(printf '%s\n' "$ip" | awk -F. '{print $4"."$3"."$2"."$1}')
dig +short A  ${rev}.all.bl.iprx.org @ns-bl.iprx.org
dig +short TXT ${rev}.all.bl.iprx.org @ns-bl.iprx.org
```

## Using the lists

Replace `all.bl.iprx.org` with a more specific zone if you only want
one category. Check the allowlist only if you have chosen to honour
IPRX delistings.

### Postfix (postscreen)

```
postscreen_dnsbl_sites =
    all.bl.iprx.org=127.0.0.[2..11]
postscreen_dnsbl_threshold = 1
```

### SpamAssassin

```
header  IPRX_DNSBL  eval:check_rbl('iprx', 'all.bl.iprx.org.')
describe IPRX_DNSBL Listed on IPRX all.bl.iprx.org
score    IPRX_DNSBL 2.0
```

### Exim

```
deny  message = listed on IPRX
      dnslists = all.bl.iprx.org
```

### rspamd

```
# local.d/rbl.conf
rbls {
  iprx {
    symbol = "RBL_IPRX";
    rbl = "all.bl.iprx.org";
    ipv4 = true;
    returncodes { IPRX_HIT = "127.0.0.2-127.0.0.11"; }
  }
}
```

### fail2ban (query before accepting a client)

```bash
rev=$(printf '%s\n' "$IP" | awk -F. '{print $4"."$3"."$2"."$1}')
if dig +time=2 +tries=1 +short A "${rev}.all.bl.iprx.org" @ns-bl.iprx.org \
    | grep -q '^127\.0\.0\.'; then
  echo listed
fi
```

### nginx (deny if listed; typically via a small auth script or `ngx_http_dns_module`)

Have the access script do the same reversed-octet `A` lookup against
`all.bl.iprx.org` and return 403 when the answer is in `127.0.0.0/24`.

## Fair use

Use of the DNSBL zones for filtering mail, ssh, or other abuse is
welcome. Bulk downloading, scraping, or republishing the listed set is
a use of the IPRX dataset and is covered by the
[license](license.md) and [pricing](pricing.md): $0 for certified
501(c)(3) nonprofits (with documentation), schools, and private
individuals; yearly tiers for companies or branches by revenue; a
14-day trial after a Verae account is set up. IPRX makes no warranty
that a listing or a removal request is correct. Receipts on Verae are
the proof of *when* an event was recorded, not an independent
investigation of the underlying conduct.


## How the list is served

These zones are **not** giant RFC 1035 zone files. A dedicated process
(`iprxdns`) on `ns-bl.iprx.org` keeps every listing in an in-memory
hash, keyed by IPv4 address or domain name. Additions and removals are
appended to a journal and applied in O(1); a snapshot is only rewritten
when the journal is compacted. The SOA serial follows the journal, not
a full rebuild of the listed set.

A local single-thread check against the current 13,688 addresses
produced about 34,000 UDP queries per second, limited by the Python
client. The server loaded that set in about 22 ms. The design target is
hundreds of thousands of queries per second on this host (SO_REUSEPORT,
more workers) and millions of entries, without rewriting a zone file on
each update. Async stamping and other heavy work can be offloaded to
microVMs; the DNS answer path stays in-process on the nameserver.

## Nameserver records

If you run your own resolver you only need to query
`ns-bl.iprx.org` (or recurse as usual once the delegations are in
place). The records on `iprx.org` are:

```
ns-bl.iprx.org.          IN A   70.88.205.140
bl.iprx.org.             IN NS  ns-bl.iprx.org.
dbl.iprx.org.            IN NS  ns-bl.iprx.org.
uri.iprx.org.            IN NS  ns-bl.iprx.org.
wl.iprx.org.             IN NS  ns-bl.iprx.org.
```

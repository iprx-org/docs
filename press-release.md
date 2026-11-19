# IPRX.ORG Launches a Worldwide Open IPv4 Blocklist With Verae-Chain Timestamped, Provable Records

**NEW HAMPSHIRE — Nov. 19, 2026**

IPRX ([https://iprx.org](https://iprx.org)) today launched a worldwide open IPv4 blocklist. Every listing and every removal is written as a record, hashed, and timestamped on the Verae chain, so the reason an address was added or taken off can be checked independently. Receipts are available as JSON, HTML, and PDF.

> "Right now, the internet needs protection. Verae provides the proof and the history at internet scale, along with the security protections the internet needs."
>
> — George Lambert, CTO, Chief Architect and Co-Founder, Verae

## A DNSBL zone family on ns-bl.iprx.org

The blocklist is served as DNS from `ns-bl.iprx.org` (`70.88.205.140`). Operators can query a combined zone and separate category zones, in the style of a traditional combined “ZEN” list:

- `all.bl.iprx.org` — combined list
- `attack.bl.iprx.org` (`127.0.0.2`) — honeypot hits / scanners
- `brute.bl.iprx.org` (`127.0.0.3`) — SSH / RDP / auth brute force
- `spam.bl.iprx.org` (`127.0.0.4`) — spam sources
- `web.bl.iprx.org` (`127.0.0.5`) — web exploit / scanner
- `bot.bl.iprx.org` (`127.0.0.6`) — botnet / C2
- `proxy.bl.iprx.org` (`127.0.0.7`) — open proxies / anonymizers
- `policy.bl.iprx.org` (`127.0.0.10`) — dynamic / residential (opt-in)
- `nominated.bl.iprx.org` (`127.0.0.11`) — community listings after five verified nominations
- `allow.wl.iprx.org` — allowlist / DKIM-proven, approved removals
- `dbl.iprx.org` — malicious domains (never a PTR hostname)
- `uri.iprx.org` — malicious URI hosts (never a PTR hostname)

The older `bl.georgelambert.org` zone remains available as an alias of the combined list. A listed address may appear in more than one category. The TXT record on a hit is a receipt link.

The zones use IPRX’s own data: honeypot observations, verified nominations, and operator decisions. Third-party lists are not imported.

## Five verified nominators, then a stamped listing

A public nomination is recorded and counts only after the nominator confirms their email, or submits with an API token issued the same way. Distinctness is by verified email and source IP, so several tokens on one email still count as one nominator. Once five different verified people nominate the same address, IPRX lists it automatically into `nominated.bl.iprx.org`. That listing event is written to the database and stamped on Verae, and it links the five nomination records. An administrator can still list or reject at any time. Private, reserved, and documentation addresses are rejected.

## Removals require DKIM, then a person

A removal request moves to the administrator queue only after the requestor proves control of a domain tied to the IP — the PTR hostname’s registrable domain, or the network owner’s or abuse-contact domain. The requestor uploads a DKIM-signed email that contains a one-time token. IPRX checks the signature and that the signing domain matches. A failed check is recorded and stamped, but the request does not advance. Administrator approval is still required. An approved, DKIM-proven removal is stamped and may be added to the allowlist.

## Nothing Up Our Sleeves

IPRX is built so operators do not have to take the project’s word for a listing or a removal. The [Nothing Up Our Sleeves](https://github.com/iprx-org/docs/blob/main/nothing-up-our-sleeves.md) policy is, in short:

- **Provable timestamps** on the Verae chain. The first stamp for a record is permanent; a restamp adds history and never overwrites the original.
- **Provable data.** Hash the record yourself and compare that digest to the receipt and the block’s Merkle root.
- **Provable GitHub uploads.** A published file’s SHA-256 is what the receipt attests; the two must match.
- **No silent edits.** Every add, remove, and category change is stamped with a block number in the chain and in the database.
- **Receipts for everyone**, as JSON, HTML, or PDF, which can be checked without trusting IPRX’s servers.

## License, free use, and annual pricing

Use of the dataset requires a Verae account, opened with billing disabled. Certified 501(c)(3) nonprofits (with documentation), schools (with documentation), and private individuals are priced at $0 per year. Paid tiers for companies or branches are billed annually, under New Hampshire law, on a scale from $250 for organizations under $500,000 in annual revenue up to $25,000,000 for companies or branches with $1 billion or more in income. Paid-tier companies or branches receive a 14-day trial once a Verae account is set up. Separate companies with multiple divisions have 30 days to enter into an agreement with the Verae.com sales department.

The draft terms are published at [https://iprx.org/pricing](https://iprx.org/pricing) and [https://iprx.org/license](https://iprx.org/license). The license is a draft pending legal review.

Downloadable blocklist feeds (plain text, CSV, and Bloom filters) are coming soon. They will be published only after the lists are confirmed reliable. Documentation, example clients, and bulk submitters for fail2ban and similar block files are on GitHub at [https://github.com/iprx-org](https://github.com/iprx-org) and [https://github.com/iprx-org/docs](https://github.com/iprx-org/docs).

## Media contact

veraetimestamp@gmail.com  
[Verae.com](https://verae.com)  
[https://iprx.org/press](https://iprx.org/press)

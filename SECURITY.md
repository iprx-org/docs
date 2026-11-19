# Security

## Delisting and listing disputes

To request that an address be removed from the IPRX list, use the [removal form](https://blocklist.iprx.org/remove) or the API (`POST /api/v1/removals` on [blocklist.iprx.org](https://blocklist.iprx.org/api/v1/removals) or [iprx.org](https://iprx.org/api/v1/removals), [documented here](api.md#request-a-removal--post-apiv1removals)). That is the supported path.

Do not send delist requests to a personal email address, and do not open a GitHub issue that includes customer contact details or a large list of addresses.

Each request is recorded, hashed, and stamped, then waits for an operator decision. Nothing is removed automatically.

## Vulnerability reports

If you believe you have found a security issue in IPRX, the documentation, or a related public service, please use [GitHub private vulnerability reporting](https://github.com/iprx-org/docs/security/advisories/new) on this repository.

Please do not file a public issue for an unpatched vulnerability. Include enough detail to reproduce the problem, and allow time for a fix before any public disclosure.

## What we publish on chain

Verae receipts contain a SHA-256 digest, a batch id, and block metadata. Event bodies, requestor email addresses, and other contact details are not written to the chain. Public API and receipt downloads omit requestor contact fields.

#!/usr/bin/env node
// Search public, redacted records by hostname, IP, hash_id, ASN, ISP, or country.
// Usage: node search.mjs [query]

const BASE = process.env.IPRX_BASE || "https://iprx.org"; // set IPRX_BASE only if you use a different host
const Q = process.argv[2] || "nt-isp";                    // hostname substring or other public search term
const url = `${BASE}/api/v1/search?${new URLSearchParams({ q: Q })}`; // GET /api/v1/search?q=
const resp = await fetch(url);                            // GET the URL
if (!resp.ok) throw new Error(`HTTP ${resp.status} ${await resp.text()}`); // show the error body
console.log(JSON.stringify(await resp.json(), null, 2));  // print a readable document

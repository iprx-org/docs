#!/usr/bin/env node
// Fetch event history for an IPv4 address or a 64-character hash_id.
// Usage: node history.mjs [ip_or_hash]

const BASE = process.env.IPRX_BASE || "https://iprx.org"; // set IPRX_BASE only if you use a different host
const KEY = process.argv[2] || "192.0.2.1";               // IP, hash_id, or event_id
const url = `${BASE}/api/v1/history/${encodeURIComponent(KEY)}`; // GET /api/v1/history/{key}
const resp = await fetch(url);                            // GET the URL
if (!resp.ok) throw new Error(`HTTP ${resp.status} ${await resp.text()}`); // show the error body
console.log(JSON.stringify(await resp.json(), null, 2));  // print a readable document

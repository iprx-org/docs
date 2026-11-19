#!/usr/bin/env node
// Fetch a SHA-256 proof-of-work challenge used by nomination and removal POSTs.
// Usage: node challenge.mjs
// Requires Node 18+ (built-in fetch).

const BASE = process.env.IPRX_BASE || "https://iprx.org"; // set IPRX_BASE only if you use a different host
const resp = await fetch(`${BASE}/api/v1/challenge`);     // GET /api/v1/challenge
if (!resp.ok) throw new Error(`HTTP ${resp.status} ${await resp.text()}`); // stop on a failed challenge
console.log(JSON.stringify(await resp.json(), null, 2));  // print {challenge, bits, expires_in}

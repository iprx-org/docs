#!/usr/bin/env node
// Check whether one IPv4 address is listed, and why.
// Usage: node check.mjs [ipv4]
// The response includes nomination_progress, for example "3/5".

const BASE = process.env.IPRX_BASE || "https://iprx.org"; // set IPRX_BASE only if you use a different host
const IP = process.argv[2] || "192.0.2.1";                // first argument, or TEST-NET-1
const resp = await fetch(`${BASE}/api/v1/check/${IP}`);   // GET /api/v1/check/{ip}
if (!resp.ok) throw new Error(`HTTP ${resp.status} ${await resp.text()}`); // show the error body
console.log(JSON.stringify(await resp.json(), null, 2));  // print a readable document

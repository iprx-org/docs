#!/usr/bin/env node
// Ask IPRX to prove a digest on Verae (original first-wins stamp, plus restamp history).
// Usage: node prove.mjs [sha256]

const BASE = process.env.IPRX_BASE || "https://iprx.org"; // set IPRX_BASE only if you use a different host
const HASH = process.argv[2] || "2c7606c0d53d7a800192f11609c939e66826f2af9c93fc971b850a97d5937466"; // 192.0.2.1 add event
const resp = await fetch(`${BASE}/api/v1/prove`, {        // POST
  method: "POST",                                         // prove is a POST
  headers: { "Content-Type": "application/json", Accept: "application/json" }, // JSON in and out
  body: JSON.stringify({ digest: HASH }),                 // body may use digest or hash_id
});
console.log(JSON.stringify(await resp.json(), null, 2));  // may be prove.ok=false if the prover is down

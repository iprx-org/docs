#!/usr/bin/env node
// Nominate one IPv4 address: fetch a challenge, solve the proof-of-work, POST /nominations.
// Usage: node nominate.mjs <ipv4> [reason]
// Documentation, private, and reserved addresses are rejected with HTTP 400.

import { createHash } from "node:crypto";             // SHA-256 for the proof-of-work

const BASE = process.env.IPRX_BASE || "https://iprx.org"; // set IPRX_BASE only if you use a different host
const IP = process.argv[2] || "192.0.2.10";               // default TEST-NET is rejected on purpose
const REASON = process.argv[3] || "TEST documentation nomination from the IPRX examples; RFC 5737 TEST-NET."; // >= 8 chars
const NAME = process.env.IPRX_NAME || "IPRX examples TEST"; // your display name
const EMAIL = process.env.IPRX_EMAIL || "docs-test@example.com"; // used to count distinct nominators

function leadingZeroBits(buf) {                       // count leading zero bits in a hash
  let zeros = 0;                                      // running total
  for (const b of buf) {                              // left to right
    if (b === 0) { zeros += 8; continue; }            // a zero byte is eight bits
    zeros += 8 - Math.floor(Math.log2(b) + 1);        // bits before the first 1 in this byte
    break;                                            // stop at the first non-zero byte
  }
  return zeros;                                       // number of leading zeros
}

function solvePow(challenge, bits) {                  // find a nonce with enough leading zero bits
  let n = 0;                                          // start at zero
  for (;;) {                                          // 18 bits is usually under a million tries
    const digest = createHash("sha256").update(`${challenge}:${n}`).digest(); // the API hashes this exact string
    if (leadingZeroBits(digest) >= bits) return String(n); // hard enough
    n += 1;                                           // try the next nonce
  }
}

const chResp = await fetch(`${BASE}/api/v1/challenge`); // one-time challenge
const ch = await chResp.json();                       // {challenge, bits, expires_in}
if (!chResp.ok) throw new Error(`challenge failed: ${chResp.status}`); // cannot continue
const nonce = solvePow(ch.challenge, ch.bits || 18);  // usually 18 bits
const body = {                                        // NominationIn
  ip: IP,                                             // address to nominate
  reason: REASON,                                     // why it should be listed
  evidence: "TEST",                                   // optional supporting text
  name: NAME,                                         // who is nominating
  email: EMAIL,                                       // used to count distinct nominators
  org: "IPRX docs examples",                          // optional organisation
  challenge: ch.challenge,                            // opaque string from GET /challenge
  pow_nonce: nonce,                                   // the nonce we just found
  company_url: "",                                    // honeypot; must stay empty
};
const resp = await fetch(`${BASE}/api/v1/nominations`, {
  method: "POST",                                     // create a nomination
  headers: { "Content-Type": "application/json", Accept: "application/json" }, // JSON in and out
  body: JSON.stringify(body),                         // NominationIn
});
console.log(resp.status);                             // 201 on success, 400 for TEST-NET
console.log(JSON.stringify(await resp.json(), null, 2)); // body

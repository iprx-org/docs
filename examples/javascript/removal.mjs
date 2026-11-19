#!/usr/bin/env node
// Request removal of one IPv4 address: challenge, proof-of-work, POST /removals.
// Usage: node removal.mjs <ipv4> [reason]
// Success is 201 with status pending_dkim and a one-time token.
// The token is saved under ~/.iprx/<event_id>.token with mode 600; do not commit it.
// This script does not send email.

import { createHash } from "node:crypto";             // SHA-256 for the proof-of-work
import { mkdir, writeFile, chmod } from "node:fs/promises"; // private token file
import { homedir } from "node:os";                    // ~/.iprx
import { join } from "node:path";                     // build the token path

const BASE = process.env.IPRX_BASE || "https://iprx.org"; // set IPRX_BASE only if you use a different host
const IP = process.argv[2] || "192.0.2.1";                // address to request removal for
const REASON = process.argv[3] || "TEST documentation removal request from the IPRX examples; not a real delist."; // >= 8 chars
const NAME = process.env.IPRX_NAME || "IPRX examples TEST"; // your display name
const EMAIL = process.env.IPRX_EMAIL || "docs-test@example.com"; // an address you control

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
const body = {                                        // RemovalIn
  ip: IP,                                             // address to request removal for
  name: NAME,                                         // who is requesting
  email: EMAIL,                                       // an address you control
  reason: REASON,                                     // why it should be delisted
  org: "IPRX docs examples",                          // optional organisation
  challenge: ch.challenge,                            // opaque string from GET /challenge
  pow_nonce: nonce,                                   // the nonce we just found
  company_url: "",                                    // honeypot; must stay empty
};
const resp = await fetch(`${BASE}/api/v1/removals`, {
  method: "POST",                                     // create a removal request
  headers: { "Content-Type": "application/json", Accept: "application/json" }, // JSON in and out
  body: JSON.stringify(body),                         // RemovalIn
});
const text = await resp.text();                       // may be JSON or plain text
console.log(resp.status);                             // 201 pending_dkim when healthy
let parsed;                                           // the response object, if JSON
try { parsed = JSON.parse(text); console.log(JSON.stringify(parsed, null, 2)); } // pretty JSON
catch { console.log(text); }                          // plain text error
if (parsed && parsed.token && parsed.event_id) {      // save the token off-repo
  const dir = join(homedir(), ".iprx");               // private directory
  await mkdir(dir, { recursive: true, mode: 0o700 }); // create it if needed
  const path = join(dir, `${parsed.event_id}.token`); // ~/.iprx/<event_id>.token
  await writeFile(path, `${parsed.token}\n`, { mode: 0o600 }); // owner read/write only
  await chmod(path, 0o600);                           // be explicit about the mode
  console.error(`# token saved privately to ${path} (mode 600); include it in your DKIM-signed .eml`); // remind the user
}

#!/usr/bin/env node
// Upload a DKIM-signed .eml to prove domain control for a removal request.
// Usage: node dkim_upload.mjs <event_id> <message.eml>
// This script only uploads a local file; it does not send any email.

import { readFile } from "node:fs/promises";          // read the local .eml

const BASE = process.env.IPRX_BASE || "https://iprx.org"; // set IPRX_BASE only if you use a different host
const EVENT_ID = process.argv[2];                     // from the removal response
const EML = process.argv[3];                          // path to a raw RFC822 .eml on disk
if (!EVENT_ID || !EML) {                              // both arguments are required
  throw new Error("usage: node dkim_upload.mjs <event_id> <message.eml>"); // how to run it
}
const raw = await readFile(EML);                      // local file bytes
if (raw.length < 20) throw new Error("eml file is empty or too short"); // stop before we POST junk
const form = new FormData();                          // multipart/form-data
form.append("eml", new Blob([raw], { type: "message/rfc822" }), "message.eml"); // field name is eml
const resp = await fetch(`${BASE}/api/v1/removals/${EVENT_ID}/dkim`, {
  method: "POST",                                     // upload the proof
  headers: { Accept: "application/json" },            // ask for JSON (let fetch set the multipart boundary)
  body: form,                                         // the .eml part
});
console.log(resp.status);                             // 201 when the check is recorded
console.log(JSON.stringify(await resp.json(), null, 2)); // result is stamped either way

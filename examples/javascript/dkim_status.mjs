#!/usr/bin/env node
// Check the DKIM verification status of a removal request.
// Usage: node dkim_status.mjs <event_id>

const BASE = process.env.IPRX_BASE || "https://iprx.org"; // set IPRX_BASE only if you use a different host
const EVENT_ID = process.argv[2];                     // from the removal response
if (!EVENT_ID) throw new Error("usage: node dkim_status.mjs <event_id>"); // how to run it
const resp = await fetch(`${BASE}/api/v1/removals/${EVENT_ID}/dkim-status`); // GET the status document
console.log(JSON.stringify(await resp.json(), null, 2)); // dkim_status is pending, passed, or failed
